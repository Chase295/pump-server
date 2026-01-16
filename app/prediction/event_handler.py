"""
Event-Handler für ML Prediction Service

Überwacht coin_metrics für neue Einträge und macht automatisch Vorhersagen.
Unterstützt LISTEN/NOTIFY (Echtzeit) und Polling-Fallback.
"""
import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
import asyncpg
from app.database.connection import get_pool, DB_DSN
from app.database.models import (
    get_active_models, save_prediction, save_model_prediction,
    check_coin_ignore_status, update_coin_scan_cache,
    get_coin_metrics_at_timestamp
)
from app.prediction.engine import predict_coin_all_models
from app.prediction.n8n_client import send_to_n8n
from app.utils.config import POLLING_INTERVAL_SECONDS, BATCH_SIZE, BATCH_TIMEOUT_SECONDS
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


class EventHandler:
    """Event-Handler mit LISTEN/NOTIFY und Polling-Fallback"""
    
    def __init__(self):
        self.listener_connection: Optional[asyncpg.Connection] = None
        self.use_listen_notify = True
        self.batch: List[Dict[str, Any]] = []
        self.batch_lock = asyncio.Lock()
        self.last_batch_time = datetime.now(timezone.utc)
        self.running = False
        self.active_models: List[Dict[str, Any]] = []
        self.last_models_update = datetime.now(timezone.utc)
        self.notification_queue: Optional[asyncio.Queue] = None
        self.last_heartbeat = datetime.now(timezone.utc)
        self.last_processed_timestamp = datetime.now(timezone.utc) - timedelta(minutes=5)
    
    async def setup_listener(self):
        """Setup LISTEN/NOTIFY Listener"""
        logger.info("🔧 Starte LISTEN/NOTIFY Setup...")
        try:
            # Separate Connection für LISTEN (kann nicht über Pool sein)
            self.listener_connection = await asyncpg.connect(DB_DSN)
            
            # ⚠️ WICHTIG: asyncpg's add_listener benötigt eine sync Funktion
            # Aber wir müssen async Code ausführen - nutze eine Queue!
            self.notification_queue = asyncio.Queue()
            
            # Listener-Funktion (MUSS synchron sein für asyncpg!)
            def notification_handler(conn, pid, channel, payload):
                """Wird aufgerufen wenn NOTIFY empfangen wird - LIVE!"""
                try:
                    logger.info(f"🔔🔔🔔 LIVE NOTIFY empfangen! Channel={channel}, PID={pid}")
                    logger.info(f"📦 Payload: {payload}")
                    
                    # Parse JSON
                    data = json.loads(payload)
                    coin_id = data.get('mint', 'UNKNOWN')[:20]
                    timestamp = data.get('timestamp', 'N/A')
                    logger.info(f"🪙 Neuer Coin-Eintrag LIVE: {coin_id}... am {timestamp}")
                    
                    # Füge zu Queue hinzu (thread-safe)
                    # ⚠️ WICHTIG: notification_handler ist sync, aber Queue.put() ist async
                    # Nutze call_soon_threadsafe um async Task im Event Loop zu erstellen
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # Loop läuft - nutze call_soon_threadsafe für async Operation
                            def put_in_queue():
                                try:
                                    asyncio.create_task(self.notification_queue.put(data))
                                except Exception as e:
                                    logger.error(f"❌ Fehler beim Erstellen der Queue-Task: {e}")
                            loop.call_soon_threadsafe(put_in_queue)
                            logger.debug(f"✅ Event zu Queue hinzugefügt für Coin {coin_id}...")
                        else:
                            # Loop läuft nicht - direkt put (sollte nicht passieren)
                            asyncio.run(self.notification_queue.put(data))
                            logger.debug(f"✅ Event zu Queue hinzugefügt (run) für Coin {coin_id}...")
                    except RuntimeError as e:
                        # Kein Event Loop - erstelle neuen
                        logger.warning(f"⚠️ Kein Event Loop, erstelle neuen: {e}")
                        try:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            loop.run_until_complete(self.notification_queue.put(data))
                            logger.debug(f"✅ Event zu Queue hinzugefügt (neuer Loop) für Coin {coin_id}...")
                        except Exception as e2:
                            logger.error(f"❌ Fehler beim Erstellen neues Loop: {e2}")
                except Exception as e:
                    logger.error(f"❌ Fehler beim Verarbeiten von Notification: {e}", exc_info=True)
            
            # Listener registrieren
            await self.listener_connection.add_listener(
                'coin_metrics_insert',
                notification_handler
            )
            
            # LISTEN aktivieren
            await self.listener_connection.execute("LISTEN coin_metrics_insert")

            logger.info("✅ LISTEN/NOTIFY ERFOLGREICH aktiviert - warte auf neue Coins!")
            self.use_listen_notify = True
            
            # Starte Queue-Processor (verarbeitet Events aus Queue)
            asyncio.create_task(self._process_notification_queue())
            
        except Exception as e:
            logger.warning(f"⚠️ LISTEN/NOTIFY nicht verfügbar: {e}", exc_info=True)
            logger.info("→ Fallback auf Polling")
            logger.error(f"❌ LISTEN/NOTIFY SETUP FEHLER: {str(e)}")
            logger.info("🔄 POLLING-MODUS: Prüfe alle 30 Sekunden nach neuen Coins")
            import traceback
            logger.error(f"❌ FULL TRACEBACK: {traceback.format_exc()}")
            self.use_listen_notify = False
    
    async def _process_notification_queue(self):
        """Verarbeitet Events aus der Notification-Queue"""
        logger.info("🔄 Notification-Queue-Processor gestartet")
        while self.running:
            try:
                # Warte auf Event (mit Timeout)
                event_data = await asyncio.wait_for(
                    self.notification_queue.get(),
                    timeout=1.0
                )
                logger.debug(f"📥 Event aus Queue geholt: {event_data.get('mint', 'UNKNOWN')[:20]}...")
                await self.add_to_batch(event_data)
            except asyncio.TimeoutError:
                # Timeout ist OK - nur prüfen ob noch running
                continue
            except Exception as e:
                logger.error(f"❌ Fehler im Queue-Processor: {e}", exc_info=True)
    
    async def add_to_batch(self, event_data: Dict[str, Any]):
        """Fügt Event zu Batch hinzu"""
        should_process = False
        batch_to_process = None
        
        async with self.batch_lock:
            # Wenn Batch leer war, setze last_batch_time neu (Start des neuen Batches)
            if not self.batch:
                self.last_batch_time = datetime.now(timezone.utc)
            
            self.batch.append(event_data)
            logger.debug(f"📥 Event zu Batch hinzugefügt (Batch-Größe: {len(self.batch)})")
            
            # Prüfe ob Batch voll
            if len(self.batch) >= BATCH_SIZE:
                logger.info(f"📦 Batch voll ({len(self.batch)} Einträge), verarbeite sofort")
                batch_to_process = self.batch.copy()
                self.batch.clear()
                self.last_batch_time = datetime.now(timezone.utc)
                should_process = True
        
        # ⚠️ WICHTIG: Verarbeite Batch AUSSERHALB des Locks!
        if should_process and batch_to_process:
            logger.info(f"🔄 Verarbeite Batch: {len(batch_to_process)} Einträge")
            await self._process_coin_entries(batch_to_process)
    
    async def process_batch(self):
        """Verarbeitet aktuellen Batch"""
        async with self.batch_lock:
            if not self.batch:
                return
            
            batch_to_process = self.batch.copy()
            self.batch.clear()
            self.last_batch_time = datetime.now(timezone.utc)
        
        logger.info(f"🔄 Verarbeite Batch: {len(batch_to_process)} Einträge")
        # Verarbeite Batch
        await self._process_coin_entries(batch_to_process)
    
    async def _process_coin_entries(self, coin_entries: List[Dict[str, Any]]):
        """
        Verarbeitet Liste von Coin-Einträgen.
        
        Args:
            coin_entries: Liste von Dicts mit 'mint' und 'timestamp'
        """
        pool = await get_pool()
        
        # Aktualisiere aktive Modelle (alle 10 Sekunden - für n8n Einstellungen wichtig!)
        now = datetime.now(timezone.utc)
        if (now - self.last_models_update).total_seconds() > 10:
            try:
                self.active_models = await get_active_models()
                self.last_models_update = now
                logger.debug(f"✅ Aktive Modelle aktualisiert: {len(self.active_models)} Modelle")
                # Debug: Zeige n8n_enabled Status
                for m in self.active_models:
                    logger.debug(f"  - Modell {m.get('id')}: n8n_enabled={m.get('n8n_enabled')}, n8n_url={m.get('n8n_webhook_url')}")
            except Exception as e:
                logger.error(f"❌ Fehler beim Aktualisieren aktiver Modelle: {e}")
        
        if not self.active_models:
            logger.warning("⚠️ Keine aktiven Modelle - überspringe Vorhersagen")
            return
        
        # Verarbeite jeden Coin mit Ignore-Logik
        model_names = [m.get('custom_name') or m.get('name', 'Unknown') for m in self.active_models]
        logger.info(f"📊 Verarbeite {len(coin_entries)} Coin-Einträge mit {len(self.active_models)} aktiven Modellen: {', '.join(model_names)}")

        total_processed = 0
        total_ignored = 0

        for entry in coin_entries:
            coin_id = entry.get('mint')
            timestamp_str = entry.get('timestamp')
            
            if not coin_id or not timestamp_str:
                logger.warning(f"⚠️ Ungültiger Eintrag: {entry}")
                continue
            
            logger.debug(f"🪙 Verarbeite Coin: {coin_id[:20]}... am {timestamp_str}")
            
            # Parse timestamp
            try:
                if isinstance(timestamp_str, str):
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                else:
                    timestamp = timestamp_str
                
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=timezone.utc)
            except Exception as e:
                logger.error(f"❌ Fehler beim Parsen von Timestamp: {e}")
                continue
            
            # 🔄 COIN-FILTER- UND IGNORE-LOGIK: Prüfe für jedes Modell separat
            models_to_process = []

            for model_config in self.active_models:
                model_id = model_config.get('id')

                # 🔍 COIN-FILTER-LOGIK: Prüfe ob Coin verarbeitet werden soll
                coin_filter_mode = model_config.get('coin_filter_mode') or 'all'  # Default: 'all' wenn None
                coin_whitelist = model_config.get('coin_whitelist') or []

                # Wenn Whitelist-Modus: Prüfe ob Coin in Whitelist ist
                if coin_filter_mode == 'whitelist':
                    if not coin_whitelist or coin_id not in coin_whitelist:
                        logger.debug(f"🚫 Coin {coin_id[:8]}... nicht in Whitelist von Modell {model_id} - überspringe")
                        total_ignored += 1
                        continue

                # 🔍 PHASEN-FILTER-LOGIK: Prüfe ob Coin in der richtigen Phase ist
                model_phases = model_config.get('phases')
                coin_phase_id = entry.get('phase_id')
                
                # Wenn Modell auf spezifische Phasen trainiert wurde, prüfe ob Coin in einer dieser Phasen ist
                if model_phases and len(model_phases) > 0:
                    # Modell ist nur für bestimmte Phasen trainiert
                    if coin_phase_id is None:
                        logger.debug(f"🚫 Coin {coin_id[:8]}... hat keine Phase (phase_id=None) - Modell {model_id} benötigt Phasen {model_phases} - überspringe")
                        total_ignored += 1
                        continue
                    
                    if coin_phase_id not in model_phases:
                        logger.debug(f"🚫 Coin {coin_id[:8]}... ist in Phase {coin_phase_id}, aber Modell {model_id} ist nur für Phasen {model_phases} trainiert - überspringe")
                        total_ignored += 1
                        continue
                    
                    logger.debug(f"✅ Coin {coin_id[:8]}... ist in Phase {coin_phase_id}, passt zu Modell {model_id} (Phasen {model_phases})")
                else:
                    # Modell ist für alle Phasen (phases = None oder [])
                    logger.debug(f"✅ Coin {coin_id[:8]}... wird von Modell {model_id} verarbeitet (Modell für alle Phasen)")

                # ✅ Coin-Filter bestanden - prüfe jetzt Ignore-Einstellungen
                # WICHTIG: min_scan_interval wurde entfernt - verwende nur ignore_bad/positive/alert_seconds
                ignore_status = await check_coin_ignore_status(
                    pool, 
                    coin_id, 
                    model_id,
                    min_scan_interval_seconds=0  # Deaktiviert - wird nicht mehr verwendet
                )

                if ignore_status.get('should_ignore'):
                    # Coin wird ignoriert - KEIN Eintrag nirgendwo, nur minimales Debug-Logging
                    ignore_reason = ignore_status.get('ignore_reason')
                    remaining_seconds = ignore_status.get('remaining_seconds', 0)
                    
                    # Nur Debug-Logging (keine Info-Logs um Logs nicht zu überfluten)
                    logger.debug(f"🚫 Coin {coin_id[:8]}... wird von Modell {model_id} ignoriert ({ignore_reason}) - noch {remaining_seconds:.1f}s")
                    
                    total_ignored += 1
                    continue

                # ✅ Coin soll verarbeitet werden - zur Verarbeitungsliste hinzufügen
                models_to_process.append(model_config)

            # Überspringe diesen Coin komplett, wenn alle Modelle ihn ignorieren
            if not models_to_process:
                logger.debug(f"🚫 Coin {coin_id[:8]}... wird von allen Modellen ignoriert - überspringe")
                continue

            try:
                logger.info(f"🔮 Starte Vorhersagen für Coin {coin_id[:20]}... mit {len(models_to_process)} von {len(self.active_models)} Modellen")

                # Mache Vorhersagen nur mit den Modellen, die den Coin nicht ignorieren
                results = await predict_coin_all_models(
                    coin_id=coin_id,
                    timestamp=timestamp,
                    active_models=models_to_process,  # Nur nicht-ignorierende Modelle
                    pool=pool
                )
                
                logger.info(f"✅ {len(results)} Vorhersagen erstellt für Coin {coin_id[:20]}...")
                total_processed += len(results)
                
                # Speichere Vorhersagen in DB und aktualisiere Cache
                # Hole Metriken für diesen Coin zum Zeitpunkt der Vorhersage
                metrics = await get_coin_metrics_at_timestamp(coin_id, timestamp, pool=pool)
                
                for result in results:
                    try:
                        model_id = result.get('active_model_id')
                        prediction = result['prediction']
                        probability = result['probability']
                        
                        # Finde das entsprechende Modell-Config für future_minutes und alert_threshold
                        model_config = next((m for m in models_to_process if m.get('id') == model_id), None)
                        if not model_config:
                            logger.warning(f"⚠️ Modell-Config nicht gefunden für active_model_id={model_id}")
                            continue
                        
                        alert_threshold = model_config.get('alert_threshold', 0.7)
                        future_minutes = model_config.get('future_minutes', 10)  # Default: 10 Minuten

                        # 🔍 MAX-LOG-ENTRIES-PRÜFUNG: Prüfe ob Coin bereits zu oft eingetragen wurde
                        # Berechne tag vorher (wird auch in save_model_prediction berechnet, aber wir brauchen es hier)
                        if probability < 0.5:
                            tag = 'negativ'
                        elif probability < alert_threshold:
                            tag = 'positiv'
                        else:
                            tag = 'alert'
                        
                        # Prüfe Limit für diesen Tag
                        max_entries = None
                        if tag == 'negativ':
                            max_entries = model_config.get('max_log_entries_per_coin_negative', 0)
                        elif tag == 'positiv':
                            max_entries = model_config.get('max_log_entries_per_coin_positive', 0)
                        else:  # alert
                            max_entries = model_config.get('max_log_entries_per_coin_alert', 0)
                        
                        # Wenn Limit gesetzt (max_entries > 0), prüfe ob bereits erreicht
                        if max_entries > 0:
                            current_count = await pool.fetchval("""
                                SELECT COUNT(*)
                                FROM model_predictions
                                WHERE coin_id = $1
                                  AND active_model_id = $2
                                  AND tag = $3
                                  AND status = 'aktiv'
                            """, coin_id, model_id, tag)
                            
                            if current_count >= max_entries:
                                # Prüfe ob ignorierten Coins trotzdem an n8n gesendet werden sollen
                                send_ignored_to_n8n = model_config.get('send_ignored_to_n8n', False)
                                n8n_enabled = model_config.get('n8n_enabled', False)
                                
                                if send_ignored_to_n8n and n8n_enabled:
                                    # Sende trotzdem an n8n, aber speichere NICHT in DB
                                    logger.debug(f"📤 Coin {coin_id[:8]}... bereits {current_count}x als {tag} eingetragen (Limit: {max_entries}) - sende trotzdem an n8n (ohne DB-Speicherung)")
                                    
                                    # Erstelle temporäres Result-Objekt für n8n
                                    ignored_result = {
                                        'active_model_id': model_id,
                                        'model_id': result['model_id'],
                                        'prediction': prediction,
                                        'probability': probability,
                                        'coin_id': coin_id,
                                        'timestamp': timestamp
                                    }
                                    
                                    # Sende an n8n (wird später im send_to_n8n Block verarbeitet)
                                    # Wir fügen es zu results hinzu, damit es an n8n gesendet wird
                                    results.append(ignored_result)
                                    
                                    total_ignored += 1
                                    continue  # Überspringe DB-Speicherung
                                else:
                                    # Komplett überspringen (kein n8n, keine DB)
                                    logger.debug(f"🚫 Coin {coin_id[:8]}... bereits {current_count}x als {tag} eingetragen (Limit: {max_entries}) - überspringe komplett")
                                    total_ignored += 1
                                    continue

                        # Speichere Vorhersage in NEUER Tabelle (model_predictions)
                        await save_model_prediction(
                            coin_id=coin_id,
                            prediction_timestamp=timestamp,
                            model_id=result['model_id'],
                            active_model_id=model_id,
                            prediction=prediction,
                            probability=probability,
                            alert_threshold=alert_threshold,
                            future_minutes=future_minutes,
                            metrics=metrics,
                            phase_id_at_time=entry.get('phase_id'),
                            pool=pool
                        )
                        
                        # ⚠️ ALTE FUNKTION: Behalte für Rückwärtskompatibilität (kann später entfernt werden)
                        # await save_prediction(...)

                        # 🔄 CACHE-AKTUALISIERUNG: Nach erfolgreicher Vorhersage
                        if model_id:
                            # Finde das entsprechende Modell-Config
                            model_config = next((m for m in models_to_process if m.get('id') == model_id), None)
                            if model_config:
                                await update_coin_scan_cache(
                                    pool=pool,
                                    coin_id=coin_id,
                                    active_model_id=model_id,
                                    prediction=prediction,
                                    probability=probability,
                                    alert_threshold=model_config.get('alert_threshold', 0.7),
                                    ignore_bad_seconds=model_config.get('ignore_bad_seconds', 0),
                                    ignore_positive_seconds=model_config.get('ignore_positive_seconds', 0),
                                    ignore_alert_seconds=model_config.get('ignore_alert_seconds', 0)
                                )

                    except Exception as e:
                        logger.error(f"❌ Fehler beim Speichern/Aktualisieren für Modell {model_id}: {e}")
                
                # Sende Vorhersagen an n8n (nur für tatsächlich verarbeitete Modelle)
                if results:
                    logger.info(f"📤 Sende {len(results)} Vorhersagen an n8n")
                    result = await send_to_n8n(
                        coin_id=coin_id,
                        timestamp=timestamp,
                        predictions=results,
                        active_models=models_to_process  # Nur die verarbeiteten Modelle
                    )
                    logger.info(f"📤 n8n Ergebnis: {result}")
                else:
                    logger.warning(f"⚠️ Keine Vorhersagen für Coin {coin_id[:8]}...")
                
            except Exception as e:
                logger.error(
                    f"❌ Fehler bei Verarbeitung von Coin {coin_id[:8]}...: {e}",
                    exc_info=True
                )
                continue
    
        # 📊 Zusammenfassung der Verarbeitung
        logger.info(f"📊 Batch-Verarbeitung abgeschlossen: {total_processed} Vorhersagen erstellt, {total_ignored} Coins/Modelle ignoriert")
    
    async def start_polling_fallback(self):
        """Polling-Fallback wenn LISTEN/NOTIFY nicht verfügbar"""
        pool = await get_pool()
        
        # WICHTIG: Prüfe letzte verarbeitete Prediction, um nicht zu viele zu verarbeiten
        # Aber wenn keine Predictions existieren, gehe weiter zurück
        last_prediction_row = await pool.fetchrow("""
            SELECT MAX(prediction_timestamp) as max_ts
            FROM model_predictions
            WHERE active_model_id IN (SELECT id FROM prediction_active_models WHERE is_active = true)
        """)
        
        if last_prediction_row and last_prediction_row['max_ts']:
            # Verwende letzte verarbeitete Prediction als Startpunkt
            self.last_processed_timestamp = last_prediction_row['max_ts']
            logger.info(f"📊 Verwende letzte verarbeitete Prediction als Startpunkt: {self.last_processed_timestamp}")
        else:
            # Keine Predictions vorhanden - finde neueste coin_metrics und starte von dort
            newest_metric_row = await pool.fetchrow("""
                SELECT MAX(timestamp) as max_ts
                FROM coin_metrics
            """)
            
            if newest_metric_row and newest_metric_row['max_ts']:
                # Starte mit neuesten coin_metrics (aber nicht zu weit zurück, um nicht zu viele auf einmal zu verarbeiten)
                # Verwende letzten Tag als Maximum
                one_day_ago = datetime.now(timezone.utc) - timedelta(days=1)
                newest_ts = newest_metric_row['max_ts']
                
                # Verwende das neueste von beiden (neueste coin_metrics oder letzter Tag)
                if newest_ts > one_day_ago:
                    self.last_processed_timestamp = one_day_ago
                    logger.info(f"📊 Keine Predictions vorhanden, starte mit letztem Tag: {self.last_processed_timestamp} (neueste coin_metrics: {newest_ts})")
                else:
                    self.last_processed_timestamp = newest_ts - timedelta(minutes=5)
                    logger.info(f"📊 Keine Predictions vorhanden, starte kurz vor neuesten coin_metrics: {self.last_processed_timestamp} (neueste: {newest_ts})")
            else:
                # Keine coin_metrics vorhanden - starte mit letzten 5 Minuten
                self.last_processed_timestamp = datetime.now(timezone.utc) - timedelta(minutes=5)
                logger.warning(f"⚠️ Keine coin_metrics vorhanden, starte mit letzten 5 Minuten: {self.last_processed_timestamp}")
        
        logger.info(f"🔄 Starte Polling-Fallback (Intervall: {POLLING_INTERVAL_SECONDS}s, Start: {self.last_processed_timestamp})")
        
        # Starte Watchdog-Task für Heartbeats
        asyncio.create_task(self._watchdog_loop())
        asyncio.create_task(self._evaluation_loop())  # Starte Auswertungs-Loop
        asyncio.create_task(self._ath_tracking_loop())  # Starte ATH-Tracking-Loop
        
        while self.running:
            try:
                # Update Heartbeat
                self.last_heartbeat = datetime.now(timezone.utc)
                
                # Hole aktive Modelle (periodisch aktualisieren)
                self.active_models = await get_active_models()
                
                if not self.active_models:
                    logger.warning("⚠️ Keine aktiven Modelle gefunden")
                    await asyncio.sleep(POLLING_INTERVAL_SECONDS)
                    continue
                
                # Hole neue Einträge
                # WICHTIG: Hole die Phase zum Zeitpunkt des latest_timestamp, nicht MAX(phase_id_at_time)!
                query = """
                    WITH latest_entries AS (
                        SELECT DISTINCT 
                            mint, 
                            MAX(timestamp) as latest_timestamp
                    FROM coin_metrics
                    WHERE timestamp > $1
                    GROUP BY mint
                    )
                    SELECT 
                        le.mint,
                        le.latest_timestamp,
                        cm.phase_id_at_time as phase_id
                    FROM latest_entries le
                    JOIN coin_metrics cm ON cm.mint = le.mint 
                        AND cm.timestamp = le.latest_timestamp
                    ORDER BY le.latest_timestamp ASC
                    LIMIT $2
                """
                rows = await pool.fetch(query, self.last_processed_timestamp, BATCH_SIZE)
                
                if rows:
                    logger.info(f"📥 Polling: {len(rows)} neue Einträge gefunden (seit {self.last_processed_timestamp})")
                    events = [
                        {
                            'mint': row['mint'],
                            'timestamp': row['latest_timestamp'],
                            'phase_id': row['phase_id']
                        }
                        for row in rows
                    ]
                    await self._process_coin_entries(events)
                    self.last_processed_timestamp = max(e['timestamp'] for e in events)
                    # Update Heartbeat nach erfolgreicher Verarbeitung
                    self.last_heartbeat = datetime.now(timezone.utc)
                    logger.debug(f"✅ Polling: Verarbeitet bis {self.last_processed_timestamp}")
                else:
                    # Auch wenn keine neuen Einträge, update Heartbeat (zeigt dass Loop läuft)
                    self.last_heartbeat = datetime.now(timezone.utc)
                    logger.debug(f"📭 Polling: Keine neuen Einträge seit {self.last_processed_timestamp}")
                
                await asyncio.sleep(POLLING_INTERVAL_SECONDS)
                
            except Exception as e:
                logger.error(f"❌ Fehler im Polling-Loop: {e}", exc_info=True)
                # WICHTIG: Auch bei Fehlern weitermachen, damit der Loop nicht stoppt
                await asyncio.sleep(POLLING_INTERVAL_SECONDS)
                continue
    
    
    async def start(self):
        """Startet Event-Handler"""
        self.running = True
        
        # Lade aktive Modelle
        try:
            self.active_models = await get_active_models()
            logger.info(f"✅ {len(self.active_models)} aktive Modelle geladen")
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden aktiver Modelle: {e}")
            self.active_models = []
        
        # Versuche LISTEN/NOTIFY
        await self.setup_listener()
        
        # WICHTIG: Nutze IMMER Polling-Fallback (LISTEN/NOTIFY ist zu unzuverlässig)
        # Der Benutzer hat Recht: Es ist einfach - alle Coins die nicht in den letzten X Sekunden
        # geprüft wurden, werden geprüft und in die Logs eingetragen
        logger.info("🔄 Event-Handler gestartet (Polling-Modus - zuverlässig)")
        await self.start_polling_fallback()
    
    async def _batch_timeout_loop(self):
        """Background-Task für Batch-Timeout"""
        logger.debug("⏰ Batch-Timeout-Loop gestartet")
        while self.running:
            try:
                await asyncio.sleep(BATCH_TIMEOUT_SECONDS)

                batch_to_process = None
                async with self.batch_lock:
                    if self.batch:
                        time_since_last = (datetime.now(timezone.utc) - self.last_batch_time).total_seconds()
                        if time_since_last >= BATCH_TIMEOUT_SECONDS:
                            logger.info(f"⏰ Batch-Timeout erreicht ({time_since_last:.1f}s), verarbeite {len(self.batch)} Einträge")
                            batch_to_process = self.batch.copy()
                            self.batch.clear()
                            self.last_batch_time = datetime.now(timezone.utc)

                # ⚠️ WICHTIG: Verarbeite Batch AUSSERHALB des Locks!
                if batch_to_process:
                    logger.info(f"🔄 Verarbeite Batch (Timeout): {len(batch_to_process)} Einträge")
                    await self._process_coin_entries(batch_to_process)
            except Exception as e:
                logger.error(f"❌ Fehler im Batch-Timeout-Loop: {e}", exc_info=True)
                # Weiterlaufen, auch bei Fehlern
                continue
    
    async def _evaluation_loop(self):
        """Auswertungs-Loop: Prüft alle 'aktiv' Einträge und wertet sie aus"""
        from app.database.evaluation_job import evaluate_pending_predictions
        logger.info("🔄 Auswertungs-Loop gestartet")
        await asyncio.sleep(5)  # Kurze Verzögerung beim Start
        while self.running:
            try:
                # Erhöhte Batch-Größe für bessere Performance bei vielen ausstehenden Auswertungen
                batch_size = 500
                stats = await evaluate_pending_predictions(batch_size=batch_size)
                if stats['evaluated'] > 0:
                    logger.info(f"✅ {stats['evaluated']} Vorhersagen ausgewertet: {stats['success']} success, {stats['failed']} failed, {stats['not_applicable']} not_applicable")
                else:
                    logger.debug(f"🔄 Auswertungs-Loop: Keine ausstehenden Auswertungen")
                
                # Wenn viele ausgewertet wurden, verkürze das Intervall für schnelleres Aufholen
                if stats['evaluated'] >= batch_size:
                    # Viele ausstehend - verarbeite schneller
                    await asyncio.sleep(10)  # Nur 10 Sekunden warten
                else:
                    # Wenige ausstehend - normaler Intervall
                    await asyncio.sleep(30)  # Alle 30 Sekunden prüfen (statt 60)
            except Exception as e:
                logger.error(f"❌ Fehler im Auswertungs-Loop: {e}", exc_info=True)
                await asyncio.sleep(30)  # Auch bei Fehler weiterlaufen
    
    async def _ath_tracking_loop(self):
        """ATH-Tracking-Loop: Prüft alle 30 Sekunden ATH Highest/Lowest für aktive Predictions"""
        from app.database.ath_tracker_model_predictions import update_ath_for_active_predictions
        logger.info("📈 ATH-Tracking-Loop gestartet")
        await asyncio.sleep(5)  # Kurze Verzögerung beim Start
        while self.running:
            try:
                stats = await update_ath_for_active_predictions(batch_size=200)  # Größerer Batch
                if stats['checked'] > 0:
                    logger.info(f"📈 ATH-Tracking: {stats['checked']} geprüft, {stats['updated_highest']} Highest, {stats['updated_lowest']} Lowest aktualisiert, {stats['errors']} Fehler")
                else:
                    logger.debug(f"📈 ATH-Tracking: Keine Einträge zum Prüfen gefunden")
                await asyncio.sleep(30)  # Alle 30 Sekunden prüfen (schneller für neue Einträge)
            except Exception as e:
                logger.error(f"❌ Fehler im ATH-Tracking-Loop: {e}", exc_info=True)
                await asyncio.sleep(30)  # Auch bei Fehler weiterlaufen
    
    async def _watchdog_loop(self):
        """Watchdog-Task für Heartbeats und Health-Checks"""
        logger.info("🐕 Watchdog-Loop gestartet")
        last_heartbeat_check = datetime.now(timezone.utc)
        
        while self.running:
            try:
                await asyncio.sleep(60)  # Alle 60 Sekunden prüfen
                
                # Prüfe ob Event-Handler noch aktiv ist (Heartbeat sollte regelmäßig aktualisiert werden)
                time_since_heartbeat = (datetime.now(timezone.utc) - self.last_heartbeat).total_seconds()
                time_since_last_processed = (datetime.now(timezone.utc) - self.last_processed_timestamp).total_seconds()
                
                if time_since_heartbeat > 180:  # Mehr als 3 Minuten ohne Heartbeat = Problem
                    logger.error(f"🚨 Watchdog: Kein Heartbeat seit {time_since_heartbeat:.1f}s - Event-Handler hängt möglicherweise!")
                    logger.error(f"🚨 Watchdog: Letzte Verarbeitung vor {time_since_last_processed:.1f}s")
                    # Versuche graceful restart durch Beenden des Loops
                    logger.warning("🔄 Watchdog: Versuche Event-Handler neu zu starten...")
                    self.running = False
                    # Exit mit Fehlercode, damit Supervisor neu startet
                    import sys
                    sys.exit(1)
                
                # Log Heartbeat (nur alle 5 Minuten, um Logs nicht zu überfluten)
                if (datetime.now(timezone.utc) - last_heartbeat_check).total_seconds() >= 300:
                    logger.info(f"💓 Watchdog Heartbeat: Event-Handler läuft (letzte Verarbeitung: {self.last_processed_timestamp}, Heartbeat: {time_since_heartbeat:.1f}s alt)")
                    last_heartbeat_check = datetime.now(timezone.utc)
                
            except Exception as e:
                logger.error(f"❌ Fehler im Watchdog-Loop: {e}", exc_info=True)
                # Weiterlaufen, auch bei Fehlern
                continue
    
    async def stop(self):
        """Stoppt Event-Handler"""
        self.running = False
        
        # Verarbeite verbleibenden Batch
        if self.batch:
            await self.process_batch()
        
        # Schließe LISTEN-Connection
        if self.listener_connection and not self.listener_connection.is_closed():
            await self.listener_connection.close()
            logger.info("✅ LISTEN-Connection geschlossen")
        
        logger.info("✅ Event-Handler gestoppt")





async def start_event_handler():
    """Startet den Event-Handler als Background-Task"""
    handler = EventHandler()
    asyncio.create_task(handler.start())
    logger.info("🎯 Event-Handler als Background-Task gestartet")


async def main():
    """Main entry point for running the event handler"""
    handler = EventHandler()
    await handler.start()


if __name__ == "__main__":
    # Wird ausgeführt wenn das Modul direkt gestartet wird
    asyncio.run(main())

"""
Auswertungs-Job für model_predictions

Prüft alle 'aktiv' Einträge und wertet sie aus, wenn evaluation_timestamp erreicht wurde.
"""
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import asyncpg
from app.database.connection import get_pool
from app.database.models import get_coin_metrics_at_timestamp
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


async def evaluate_pending_predictions(batch_size: int = 100, per_model_batch_size: int = 50) -> Dict[str, int]:
    """
    Prüft alle 'aktiv' Einträge und wertet sie aus.
    
    ✅ OPTIMIERT: Verarbeitet jedes Modell separat - kein Blockieren!
    Jedes Modell bekommt eigene Batch-Größe, um Rückstau zu vermeiden.
    
    Args:
        batch_size: Maximale Gesamtanzahl der Einträge (DEPRECATED - wird nicht mehr verwendet)
        per_model_batch_size: Anzahl der Einträge pro Modell (Standard: 50)
        
    Returns:
        Dict mit Statistiken (evaluated, success, failed, not_applicable)
    """
    pool = await get_pool()
    
    # ✅ NEU: Hole zuerst alle aktiven Modell-IDs
    active_model_ids = await pool.fetch("""
        SELECT id FROM prediction_active_models WHERE is_active = true
    """)
    
    if not active_model_ids:
        logger.debug("ℹ️ Keine aktiven Modelle - keine Evaluierungen")
        return {'evaluated': 0, 'success': 0, 'failed': 0, 'not_applicable': 0, 'errors': 0}
    
    # ✅ NEU: Verarbeite jedes Modell separat
    all_rows = []
    for model_row in active_model_ids:
        active_model_id = model_row['id']
        
        # Hole ausstehende Einträge NUR für dieses Modell
        rows = await pool.fetch("""
            SELECT
                mp.*,
                pam.future_minutes,
                pam.price_change_percent,
                pam.target_direction,
                -- WICHTIG: Für Alerts brauchen wir price_close_at_alert aus alert_evaluations
                ae.alert_timestamp,
                ae.price_close_at_alert,
                ae.price_open_at_alert,
                ae.price_high_at_alert,
                ae.price_low_at_alert,
                cm_eval.price_open as eval_price_open,
                cm_eval.price_high as eval_price_high,
                cm_eval.price_low as eval_price_low,
                cm_eval.price_close as eval_price_close,
                cm_eval.market_cap_close as eval_market_cap_close,
                cm_eval.volume_sol as eval_volume_sol,
                cm_eval.buy_volume_sol as eval_buy_volume_sol,
                cm_eval.sell_volume_sol as eval_sell_volume_sol,
                cm_eval.num_buys as eval_num_buys,
                cm_eval.num_sells as eval_num_sells,
                cm_eval.unique_wallets as eval_unique_wallets,
                cm_eval.phase_id_at_time as eval_phase_id
            FROM model_predictions mp
            INNER JOIN prediction_active_models pam ON pam.id = mp.active_model_id AND pam.is_active = true
            LEFT JOIN alert_evaluations ae ON ae.prediction_id = mp.prediction  -- JOIN für Alert-Daten
            LEFT JOIN LATERAL (
                SELECT *
                FROM coin_metrics
                WHERE mint = mp.coin_id
                  AND timestamp <= mp.evaluation_timestamp
                ORDER BY timestamp DESC
                LIMIT 1
            ) cm_eval ON true
            WHERE mp.status = 'aktiv'
              AND mp.active_model_id = $1
              AND mp.evaluation_timestamp <= NOW()
            ORDER BY mp.evaluation_timestamp ASC
            LIMIT $2
        """, active_model_id, per_model_batch_size)
        
        all_rows.extend(rows)
        if rows:
            logger.debug(f"📊 Modell {active_model_id}: {len(rows)} ausstehende Evaluierungen gefunden")
    
    # Sortiere alle Einträge nach evaluation_timestamp (älteste zuerst)
    rows = sorted(all_rows, key=lambda r: r['evaluation_timestamp'])
    
    stats = {
        'evaluated': 0,
        'success': 0,
        'failed': 0,
        'not_applicable': 0,
        'errors': 0
    }
    
    # OPTIMIERUNG: Sammle alle Updates und führe sie in Batches aus (viel schneller!)
    updates_to_execute = []
    
    for row in rows:
        try:
            prediction_id = row['id']
            coin_id = row['coin_id']
            tag = row['tag']
            prediction = row['prediction']
            evaluation_timestamp = row['evaluation_timestamp']
            
            # Metriken sind bereits im JOIN enthalten (viel schneller!)
            if row.get('eval_price_close') is not None:
                current_metrics = {
                    'price_open': float(row['eval_price_open']) if row['eval_price_open'] else None,
                    'price_high': float(row['eval_price_high']) if row['eval_price_high'] else None,
                    'price_low': float(row['eval_price_low']) if row['eval_price_low'] else None,
                    'price_close': float(row['eval_price_close']) if row['eval_price_close'] else None,
                    'market_cap_close': float(row['eval_market_cap_close']) if row['eval_market_cap_close'] else None,
                    'volume_sol': float(row['eval_volume_sol']) if row['eval_volume_sol'] else None,
                    'volume_usd': None,
                    'buy_volume_sol': float(row['eval_buy_volume_sol']) if row['eval_buy_volume_sol'] else None,
                    'sell_volume_sol': float(row['eval_sell_volume_sol']) if row['eval_sell_volume_sol'] else None,
                    'num_buys': int(row['eval_num_buys']) if row['eval_num_buys'] else None,
                    'num_sells': int(row['eval_num_sells']) if row['eval_num_sells'] else None,
                    'unique_wallets': int(row['eval_unique_wallets']) if row['eval_unique_wallets'] else None,
                    'phase_id': int(row['eval_phase_id']) if row['eval_phase_id'] else None
                }
            else:
                current_metrics = None
            
            if not current_metrics:
                logger.warning(f"⚠️ Keine Metriken gefunden für Coin {coin_id[:12]}... zum Zeitpunkt {evaluation_timestamp} (Prediction ID: {prediction_id})")
                # Sammle für Batch-UPDATE
                updates_to_execute.append((
                    'inaktiv',
                    'not_applicable',
                    None,  # actual_change_pct
                    'Keine Metriken zum evaluation_timestamp gefunden',
                    None, None, None, None, None, None, None, None, None,  # metrics
                    prediction_id
                ))
                stats['not_applicable'] += 1
                stats['evaluated'] += 1
                continue
            
            # Berechne tatsächliche Preisänderung
            # WICHTIG: Konvertiere Decimal zu float für Berechnungen
            # asyncpg gibt Decimal zurück, muss zu float konvertiert werden
            from decimal import Decimal
            
            # WICHTIG: Speichere price_close_at_evaluation WERT sofort, bevor es geändert werden könnte
            # Verwende direkt row['eval_price_close'] statt current_metrics, um sicherzustellen, dass der richtige Wert verwendet wird
            price_close_at_evaluation_to_save = row.get('eval_price_close')
            if price_close_at_evaluation_to_save is not None:
                # Konvertiere zu float falls Decimal
                from decimal import Decimal
                if isinstance(price_close_at_evaluation_to_save, Decimal):
                    price_close_at_evaluation_to_save = float(price_close_at_evaluation_to_save)
                else:
                    price_close_at_evaluation_to_save = float(price_close_at_evaluation_to_save)
            
            # WICHTIG: Für Alerts verwende price_close_at_alert (Start beim Alert), nicht price_close_at_prediction!
            # Für normale Predictions verwende weiterhin price_close_at_prediction
            if tag == 'alert' and row.get('alert_timestamp'):
                # ALERT: Verwende Preis zum alert_timestamp als Startpunkt
                price_close_at_start_raw = row.get('price_close_at_alert')
                start_timestamp_desc = "alert_timestamp"
            else:
                # NORMALE PREDICTION: Verwende Preis zum prediction_timestamp
                price_close_at_start_raw = row['price_close_at_prediction']
                start_timestamp_desc = "prediction_timestamp"

            price_close_at_evaluation_raw = price_close_at_evaluation_to_save  # Verwende gespeicherten Wert

            # Konvertiere beide zu float (falls Decimal)
            if price_close_at_start_raw is not None:
                if isinstance(price_close_at_start_raw, Decimal):
                    price_close_at_start = float(price_close_at_start_raw)
                else:
                    price_close_at_start = float(price_close_at_start_raw)
            else:
                price_close_at_start = None

            if price_close_at_evaluation_raw is not None:
                if isinstance(price_close_at_evaluation_raw, Decimal):
                    price_close_at_evaluation = float(price_close_at_evaluation_raw)
                else:
                    price_close_at_evaluation = float(price_close_at_evaluation_raw)
            else:
                price_close_at_evaluation = None

            if price_close_at_start and price_close_at_evaluation:
                # ZURÜCK ZUR ABSOLUTEN BERECHNUNG: Tatsächlicher prozentualer Gewinn/Verlust
                # (Endpreis - Startpreis) / Startpreis * 100
                # Das ist der reale Gewinn, den man gemacht hätte
                actual_change_pct = ((price_close_at_evaluation - price_close_at_start) / price_close_at_start) * 100
                logger.debug(f"✅ {prediction_id}: actual_change_pct={actual_change_pct:.2f}% (absoluter Gewinn: {price_close_at_start:.2e} → {price_close_at_evaluation:.2e})")
            else:
                actual_change_pct = None
                logger.debug(f"⚠️ Keine Preis-Daten für Prediction {prediction_id}: start={price_close_at_start}, evaluation={price_close_at_evaluation}")
            
            # Bestimme evaluation_result
            # WICHTIG: ALLE Vorhersagen werden ausgewertet (negativ, positiv, alert)
            evaluation_result = 'not_applicable'
            evaluation_note = None
            
            # Hole Modell-Konfiguration für Auswertung
            target_change = float(row.get('price_change_percent')) if row.get('price_change_percent') else None
            target_direction = row.get('target_direction') or 'up'
            future_minutes = row.get('future_minutes') or 10
            
            if actual_change_pct is None:
                evaluation_result = 'not_applicable'
                evaluation_note = 'Preis-Daten nicht verfügbar'
                logger.debug(f"⚠️ Prediction {prediction_id}: actual_change_pct ist None (start={price_close_at_start}, evaluation={price_close_at_evaluation})")
            elif target_change is None:
                # Kein Ziel definiert - kann nicht ausgewertet werden
                # Dies passiert wenn das Modell gelöscht/deaktiviert wurde oder keine Konfiguration hat
                evaluation_result = 'not_applicable'
                if row.get('future_minutes') is None:
                    evaluation_note = 'Modell gelöscht oder deaktiviert - keine Konfiguration verfügbar'
                else:
                    evaluation_note = 'Kein Ziel (price_change_percent) definiert'
            else:
                # Auswertung basierend auf Vorhersage und tatsächlicher Änderung
                if prediction == 1:
                    # Positive Vorhersage: Erwartet Preissteigerung
                    if target_direction == 'up':
                        if actual_change_pct >= target_change:
                            evaluation_result = 'success'
                            evaluation_note = f'Preis stieg um {actual_change_pct:.2f}% (Ziel: {target_change}%)'
                        else:
                            evaluation_result = 'failed'
                            evaluation_note = f'Preis stieg nur um {actual_change_pct:.2f}% (Ziel: {target_change}%)'
                    else:  # down (selten bei prediction=1)
                        if actual_change_pct <= -target_change:
                            evaluation_result = 'success'
                            evaluation_note = f'Preis fiel um {abs(actual_change_pct):.2f}% (Ziel: {target_change}%)'
                        else:
                            evaluation_result = 'failed'
                            evaluation_note = f'Preis fiel nur um {abs(actual_change_pct):.2f}% (Ziel: {target_change}%)'
                else:
                    # Negative Vorhersage (prediction=0): Erwartet KEINE Preissteigerung
                    # Erfolg = Preis stieg NICHT um target_change% oder mehr
                    if target_direction == 'up':
                        if actual_change_pct < target_change:
                            evaluation_result = 'success'
                            evaluation_note = f'Preis stieg nur um {actual_change_pct:.2f}% (Ziel war ≥{target_change}% - korrekt negativ)'
                        else:
                            evaluation_result = 'failed'
                            evaluation_note = f'Preis stieg um {actual_change_pct:.2f}% (Ziel war ≥{target_change}% - falsch negativ)'
                    else:  # down
                        if actual_change_pct > -target_change:
                            evaluation_result = 'success'
                            evaluation_note = f'Preis fiel nur um {abs(actual_change_pct):.2f}% (Ziel war ≤-{target_change}% - korrekt negativ)'
                        else:
                            evaluation_result = 'failed'
                            evaluation_note = f'Preis fiel um {abs(actual_change_pct):.2f}% (Ziel war ≤-{target_change}% - falsch negativ)'
            
            # Finale ATH-Prüfung: Stelle sicher, dass actual_change_pct auch in ATH berücksichtigt wird
            # ATH Highest: Nur POSITIVE Werte
            # ATH Lowest: Nur NEGATIVE Werte
            final_ath_highest = row.get('ath_highest_pct')
            final_ath_lowest = row.get('ath_lowest_pct')
            
            if actual_change_pct is not None:
                # ATH Highest: Nur wenn positiv UND höher als bisheriger Wert
                if actual_change_pct > 0:
                    if final_ath_highest is None or actual_change_pct > float(final_ath_highest):
                        final_ath_highest = actual_change_pct
                # ATH Lowest: Nur wenn negativ UND niedriger als bisheriger Wert
                if actual_change_pct < 0:
                    if final_ath_lowest is None or actual_change_pct < float(final_ath_lowest):
                        final_ath_lowest = actual_change_pct
                # WICHTIG: Wenn actual_change_pct = 0 oder positiv, aber ath_lowest_pct negativ ist,
                # dann sollte ath_lowest_pct auf 0 oder None gesetzt werden (nicht negativ bleiben)
                # ABER: ath_lowest_pct sollte den niedrigsten Wert während der Evaluierungszeit behalten,
                # auch wenn der finale Wert 0 oder positiv ist!
                # Daher: NUR aktualisieren wenn actual_change_pct < 0 UND niedriger als bisheriger Wert
                # Ansonsten: ath_lowest_pct bleibt wie es ist (kann negativ sein, auch wenn final 0%)
            
            # Sammle für Batch-UPDATE (viel schneller!)
            # WICHTIG: Verwende gespeicherten Wert für price_close_at_evaluation, nicht current_metrics.get() erneut
            # DEBUG: Logge den Wert, der gespeichert werden soll
            if price_close_at_evaluation_to_save is None:
                logger.warning(f"⚠️ Prediction {prediction_id}: price_close_at_evaluation_to_save ist None! Verwende price_close_at_start als Fallback.")
                # Fallback: Verwende price_close_at_start wenn eval_price_close None ist
                price_close_at_evaluation_to_save = price_close_at_start
            else:
                logger.debug(f"✅ Prediction {prediction_id}: price_close_at_evaluation_to_save = {price_close_at_evaluation_to_save}")
            
            updates_to_execute.append((
                'inaktiv',
                evaluation_result,
                actual_change_pct,
                evaluation_note,
                price_close_at_evaluation_to_save,  # Verwende gespeicherten Wert statt current_metrics.get()
                current_metrics.get('price_open') if current_metrics else None,
                current_metrics.get('price_high') if current_metrics else None,
                current_metrics.get('price_low') if current_metrics else None,
                current_metrics.get('market_cap_close') if current_metrics else None,
                (current_metrics.get('volume_usd') or current_metrics.get('volume_sol')) if current_metrics else None,
                current_metrics.get('phase_id') if current_metrics else None,
                final_ath_highest,
                final_ath_lowest,
                prediction_id
            ))
            
            stats['evaluated'] += 1
            if evaluation_result == 'success':
                stats['success'] += 1
            elif evaluation_result == 'failed':
                stats['failed'] += 1
            else:
                stats['not_applicable'] += 1
            
            logger.debug(f"✅ Prediction {prediction_id} ausgewertet: {evaluation_result} ({evaluation_note})")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Auswerten von Prediction {row.get('id')}: {e}", exc_info=True)
            stats['errors'] += 1
    
    # OPTIMIERUNG: Führe alle UPDATEs in Batches aus (viel schneller!)
    # Verwende einzelne UPDATEs in kleineren Batches (50 pro Batch) für bessere Performance
    if updates_to_execute:
        batch_size = 50
        total_batches = (len(updates_to_execute) + batch_size - 1) // batch_size
        
        for batch_idx in range(total_batches):
            batch = updates_to_execute[batch_idx * batch_size:(batch_idx + 1) * batch_size]
            
            # Führe Batch-UPDATEs parallel aus (viel schneller!)
            tasks = []
            for update_data in batch:
                tasks.append(pool.execute("""
                    UPDATE model_predictions
                    SET status = $1,
                        evaluated_at = NOW(),
                        evaluation_result = $2,
                        actual_price_change_pct = $3,
                        evaluation_note = $4,
                        price_close_at_evaluation = $5,
                        price_open_at_evaluation = $6,
                        price_high_at_evaluation = $7,
                        price_low_at_evaluation = $8,
                        market_cap_at_evaluation = $9,
                        volume_at_evaluation = $10,
                        phase_id_at_evaluation = $11,
                        ath_highest_pct = $12,
                        ath_lowest_pct = $13,
                        updated_at = NOW()
                    WHERE id = $14
                """, *update_data))
            
            # Führe alle UPDATEs im Batch parallel aus
            await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.debug(f"✅ {len(updates_to_execute)} Updates in {total_batches} Batches ausgeführt")
    
    return stats

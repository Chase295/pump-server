"""
Alert-Evaluations Funktionen für Pump Server

Erweiterte Funktionen für Alert-Management:
- Alert-Auswertung (Hintergrund-Job)
- Alert-Abfragen (Liste, Details, Statistiken)
"""
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta, timezone
import asyncpg
from app.database.connection import get_pool
from app.database.models import get_coin_metrics_at_timestamp
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

# ============================================================
# Sofortige Alert-Auswertung
# ============================================================

async def evaluate_alert_immediately(alert_id: int, pool: Optional[asyncpg.Pool] = None) -> Optional[Dict[str, Any]]:
    """
    Wertet einen Alert aus, NUR wenn evaluation_timestamp erreicht wurde.
    
    Args:
        alert_id: ID des Alerts
        pool: Optional: DB-Pool
        
    Returns:
        Dict mit Ergebnis oder None wenn nicht auswertbar (z.B. Zeit noch nicht erreicht)
    """
    if pool is None:
        pool = await get_pool()
    
    # Hole Alert-Daten
    alert = await pool.fetchrow("""
        SELECT ae.*, COALESCE(ae.probability, p.probability) as probability
        FROM alert_evaluations ae
        LEFT JOIN predictions p ON p.id = ae.prediction_id
        WHERE ae.id = $1
    """, alert_id)
    
    if not alert:
        logger.warning(f"⚠️ Alert {alert_id} nicht gefunden")
        return None
    
    if alert['status'] != 'pending':
        logger.debug(f"ℹ️ Alert {alert_id} ist bereits ausgewertet (Status: {alert['status']})")
        return None
    
    # WICHTIG: Prüfe ob evaluation_timestamp bereits erreicht wurde
    eval_timestamp = alert.get('evaluation_timestamp')
    if eval_timestamp:
        now = datetime.now(timezone.utc)
        if eval_timestamp > now:
            # Zeit noch nicht erreicht - nicht auswerten!
            logger.debug(f"ℹ️ Alert {alert_id} noch nicht auswertbar: evaluation_timestamp ({eval_timestamp}) noch nicht erreicht (jetzt: {now})")
            return None
    
    try:
        if alert['prediction_type'] == 'time_based':
            # Zeitbasierte Vorhersage: Hole Metriken zum evaluation_timestamp
            eval_timestamp = alert['evaluation_timestamp']
            current_metrics = await get_coin_metrics_at_timestamp(
                alert['coin_id'],
                eval_timestamp,  # Metriken zum geplanten Auswertungszeitpunkt
                pool
            )
            
            if not current_metrics or current_metrics.get('price_close') is None:
                logger.debug(f"ℹ️ Keine Metriken für Coin {alert['coin_id'][:20]}... zum evaluation_timestamp {eval_timestamp} - Alert {alert_id} bleibt pending")
                return None
            
            # Berechne Preisänderung seit Alert bis zum evaluation_timestamp
            price_at_alert = float(alert['price_close_at_alert'])
            price_at_eval = float(current_metrics['price_close'])
            actual_change_pct = ((price_at_eval - price_at_alert) / price_at_alert) * 100
            
            # Prüfe ob Ziel erreicht wurde
            target_change = float(alert['price_change_percent']) if alert['price_change_percent'] else 0
            target_direction = alert['target_direction']
            
            if target_direction == 'up':
                success = actual_change_pct >= target_change
            else:  # 'down'
                success = actual_change_pct <= -target_change
            
            # Update Status
            # WICHTIG: evaluation_timestamp NICHT überschreiben - das ist die ZIEL-Zeit (alert_timestamp + future_minutes)
            # evaluated_at ist die tatsächliche Auswertungszeit
            final_status = 'success' if success else 'failed'
            await pool.execute("""
                UPDATE alert_evaluations
                SET status = $1,
                    actual_price_change_pct = $2,
                    price_close_at_evaluation = $3,
                    evaluated_at = NOW(),
                    updated_at = NOW()
                WHERE id = $4
            """, final_status, actual_change_pct, price_at_eval, alert_id)
            logger.info(f"✅ Alert {alert_id} ausgewertet: {final_status} (Preisänderung: {actual_change_pct:.2f}%, Ziel: {target_change}%)")
            return {'status': final_status, 'actual_change': actual_change_pct}
                
        elif alert['prediction_type'] == 'classic':
            # Klassische Vorhersage: Hole Metriken zum evaluation_timestamp (für klassische = data_timestamp, also sofort)
            eval_timestamp = alert.get('evaluation_timestamp') or alert['alert_timestamp']
            target_var = alert['target_variable']
            current_metrics = await get_coin_metrics_at_timestamp(
                alert['coin_id'],
                eval_timestamp,  # Metriken zum geplanten Auswertungszeitpunkt
                pool
            )
            
            if not current_metrics:
                logger.debug(f"ℹ️ Keine Metriken für Coin {alert['coin_id'][:20]}... zum evaluation_timestamp {eval_timestamp} - Alert {alert_id} bleibt pending")
                return None
            
            actual_value = current_metrics.get(target_var)
            if actual_value is None:
                logger.debug(f"ℹ️ Variable {target_var} nicht verfügbar - Alert {alert_id} bleibt pending")
                return None
            
            # Vergleiche mit Ziel
            operator = alert['target_operator']
            target_value = float(alert['target_value'])
            
            if operator == '>':
                success = actual_value > target_value
            elif operator == '<':
                success = actual_value < target_value
            elif operator == '>=':
                success = actual_value >= target_value
            elif operator == '<=':
                success = actual_value <= target_value
            elif operator == '=':
                success = abs(actual_value - target_value) < 0.01
            else:
                success = False
            
            # Update Status
            # WICHTIG: evaluation_timestamp NICHT überschreiben - das ist die ZIEL-Zeit (alert_timestamp + future_minutes)
            # evaluated_at ist die tatsächliche Auswertungszeit
            final_status = 'success' if success else 'failed'
            await pool.execute("""
                UPDATE alert_evaluations
                SET status = $1,
                    actual_value_at_evaluation = $2,
                    evaluated_at = NOW(),
                    updated_at = NOW()
                WHERE id = $3
            """, final_status, actual_value, alert_id)
            
            logger.info(f"✅ Alert {alert_id} ausgewertet: {final_status} (aktuell: {actual_value}, Ziel: {operator} {target_value})")
            return {'status': final_status, 'actual_value': actual_value}
        else:
            logger.warning(f"⚠️ Unbekannter prediction_type: {alert['prediction_type']}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Fehler bei sofortiger Auswertung von Alert {alert_id}: {e}", exc_info=True)
        return None

# ============================================================
# Alert-Auswertung (Background-Job)
# ============================================================

async def evaluate_pending_alerts(batch_size: int = 100, include_non_alerts: bool = True) -> Dict[str, int]:
    """
    Wertet alle ausstehenden Alerts aus (Hintergrund-Job).
    Prüft SOFORT ob Ziel erreicht wurde - kein Warten auf evaluation_timestamp!
    
    Args:
        batch_size: Maximale Anzahl Alerts pro Durchlauf
        
    Returns:
        Dict mit Statistiken (evaluated, success, failed, expired)
    """
    pool = await get_pool()
    stats = {'evaluated': 0, 'success': 0, 'failed': 0, 'expired': 0}
    
    # Finde ausstehende Alerts (zeitbasiert) - NUR die, deren evaluation_timestamp erreicht wurde!
    # WICHTIG: Auch 'non_alert' Einträge evaluieren (für Performance-Auswertung)
    status_filter = "('pending', 'non_alert')" if include_non_alerts else "('pending')"
    time_based_alerts = await pool.fetch(f"""
        SELECT ae.*, COALESCE(ae.probability, p.probability) as probability 
        FROM alert_evaluations ae 
        LEFT JOIN predictions p ON p.id = ae.prediction_id
        WHERE ae.status IN {status_filter}
          AND ae.prediction_type = 'time_based'
          AND ae.evaluation_timestamp <= NOW()  -- WICHTIG: Nur wenn Zeit erreicht wurde!
        ORDER BY ae.alert_timestamp ASC
        LIMIT $1
    """, batch_size)
    
    for alert in time_based_alerts:
        try:
            # evaluation_timestamp wurde bereits erreicht - hole Metriken zum evaluation_timestamp
            eval_timestamp = alert['evaluation_timestamp']
            current_metrics = await get_coin_metrics_at_timestamp(
                alert['coin_id'],
                eval_timestamp,  # Metriken zum geplanten Auswertungszeitpunkt
                pool
            )
            
            if not current_metrics or current_metrics.get('price_close') is None:
                # Keine aktuellen Daten verfügbar - prüfe später nochmal
                # Nur als 'expired' markieren, wenn evaluation_timestamp bereits vorbei ist
                eval_ts = alert['evaluation_timestamp']
                if eval_ts and eval_ts <= datetime.now(timezone.utc):
                    await pool.execute("""
                        UPDATE alert_evaluations
                        SET status = 'expired',
                            evaluated_at = NOW(),
                            updated_at = NOW()
                        WHERE id = $1
                    """, alert['id'])
                    stats['expired'] += 1
                continue
            
            # Berechne aktuelle Änderung seit Alert
            price_at_alert = float(alert['price_close_at_alert'])
            price_now = float(current_metrics['price_close'])
            actual_change = ((price_now - price_at_alert) / price_at_alert) * 100
            
            target_change = float(alert['price_change_percent']) if alert['price_change_percent'] else 0
            target_direction = alert['target_direction']
            
            # WICHTIG: Prüfe ATH statt aktueller Preisänderung!
            # Wenn ATH das Ziel erreicht hat → success (auch wenn Preis danach wieder gefallen ist)
            ath_change = alert.get('ath_price_change_pct')
            if ath_change is not None:
                ath_change = float(ath_change)
            else:
                # Fallback: Verwende aktuelle Änderung wenn kein ATH vorhanden
                ath_change = actual_change
            
            # Prüfe ob Ziel erreicht wurde (basierend auf ATH)
            if target_direction == 'up':
                target_reached = ath_change >= target_change
            else:  # 'down'
                target_reached = ath_change <= -target_change
            
            # evaluation_timestamp wurde erreicht - jetzt final auswerten
            # WICHTIG: Für 'non_alert' Einträge ist die Logik umgekehrt!
            # - Wenn Ziel erreicht wurde → Modell hat es übersehen → 'failed'
            # - Wenn Ziel nicht erreicht wurde → Modell lag richtig → 'success'
            is_non_alert = alert['status'] == 'non_alert'
            
            if is_non_alert:
                # Für non_alert: Umgekehrte Logik
                if target_reached:
                    final_status = 'failed'  # Modell hat es übersehen (Ziel wurde erreicht)
                else:
                    final_status = 'success'  # Modell lag richtig (Ziel wurde nicht erreicht)
            else:
                # Für pending (echte Alerts): Normale Logik
                if target_reached:
                    final_status = 'success'  # Ziel erreicht
                else:
                    final_status = 'failed'  # Zeit abgelaufen, Ziel nicht erreicht
            
            # Update Status mit ALLEN Metriken
            # WICHTIG: evaluation_timestamp NICHT überschreiben - das ist die ZIEL-Zeit (alert_timestamp + future_minutes)
            # evaluated_at ist die tatsächliche Auswertungszeit
            await pool.execute("""
                UPDATE alert_evaluations
                SET status = $1,
                    price_close_at_evaluation = $2,
                    price_open_at_evaluation = $3,
                    price_high_at_evaluation = $4,
                    price_low_at_evaluation = $5,
                    market_cap_close_at_evaluation = $6,
                    market_cap_open_at_evaluation = $7,
                    volume_sol_at_evaluation = $8,
                    volume_usd_at_evaluation = $9,
                    buy_volume_sol_at_evaluation = $10,
                    sell_volume_sol_at_evaluation = $11,
                    num_buys_at_evaluation = $12,
                    num_sells_at_evaluation = $13,
                    unique_wallets_at_evaluation = $14,
                    phase_id_at_evaluation = $15,
                    actual_price_change_pct = $16,
                    evaluated_at = NOW(),
                    updated_at = NOW()
                WHERE id = $17
            """,
                final_status,
                current_metrics['price_close'],
                current_metrics.get('price_open'),
                current_metrics.get('price_high'),
                current_metrics.get('price_low'),
                current_metrics.get('market_cap_close'),
                current_metrics.get('market_cap_open'),
                current_metrics.get('volume_sol'),
                current_metrics.get('volume_usd'),
                current_metrics.get('buy_volume_sol'),
                current_metrics.get('sell_volume_sol'),
                current_metrics.get('num_buys'),
                current_metrics.get('num_sells'),
                current_metrics.get('unique_wallets'),
                current_metrics.get('phase_id'),
                actual_change,
                alert['id']
            )
            
            stats['evaluated'] += 1
            if final_status == 'success':
                stats['success'] += 1
            elif final_status == 'failed':
                stats['failed'] += 1
                
        except Exception as e:
            logger.error(f"❌ Fehler bei Auswertung von Alert {alert['id']}: {e}", exc_info=True)
    
    # Finde ALLE ausstehenden Alerts (klassisch) - KEIN Warten auf evaluation_timestamp!
    # WICHTIG: Auch 'non_alert' Einträge evaluieren (für Performance-Auswertung)
    status_filter = "('pending', 'non_alert')" if include_non_alerts else "('pending')"
    classic_alerts = await pool.fetch(f"""
        SELECT ae.*, COALESCE(ae.probability, p.probability) as probability 
        FROM alert_evaluations ae 
        LEFT JOIN predictions p ON p.id = ae.prediction_id
        WHERE ae.status IN {status_filter}
          AND ae.prediction_type = 'classic'
        ORDER BY ae.alert_timestamp ASC
        LIMIT $1
    """, batch_size)
    
    for alert in classic_alerts:
        try:
            # Hole Wert der target_variable zum evaluation_timestamp (für klassische = data_timestamp, also sofort)
            eval_timestamp = alert.get('evaluation_timestamp') or alert['alert_timestamp']
            target_var = alert['target_variable']
            metrics = await get_coin_metrics_at_timestamp(
                alert['coin_id'],
                eval_timestamp,  # Metriken zum geplanten Auswertungszeitpunkt
                pool
            )
            
            if not metrics:
                await pool.execute("""
                    UPDATE alert_evaluations
                    SET status = 'expired',
                        evaluated_at = NOW(),
                        updated_at = NOW()
                    WHERE id = $1
                """, alert['id'])
                stats['expired'] += 1
                continue
            
            # Hole Wert der target_variable
            actual_value = metrics.get(target_var)
            if actual_value is None:
                await pool.execute("""
                    UPDATE alert_evaluations
                    SET status = 'expired',
                        evaluated_at = NOW(),
                        updated_at = NOW()
                    WHERE id = $1
                """, alert['id'])
                stats['expired'] += 1
                continue
            
            # Vergleiche mit Ziel
            operator = alert['target_operator']
            target_value = float(alert['target_value'])
            
            if operator == '>':
                target_reached = actual_value > target_value
            elif operator == '<':
                target_reached = actual_value < target_value
            elif operator == '>=':
                target_reached = actual_value >= target_value
            elif operator == '<=':
                target_reached = actual_value <= target_value
            elif operator == '=':
                target_reached = abs(actual_value - target_value) < 0.01  # Toleranz für Floats
            else:
                target_reached = False
            
            # WICHTIG: Für 'non_alert' Einträge ist die Logik umgekehrt!
            # - Wenn Ziel erreicht wurde → Modell hat es übersehen → 'failed'
            # - Wenn Ziel nicht erreicht wurde → Modell lag richtig → 'success'
            is_non_alert = alert['status'] == 'non_alert'
            
            if is_non_alert:
                # Für non_alert: Umgekehrte Logik
                if target_reached:
                    final_status = 'failed'  # Modell hat es übersehen (Ziel wurde erreicht)
                else:
                    final_status = 'success'  # Modell lag richtig (Ziel wurde nicht erreicht)
            else:
                # Für pending (echte Alerts): Normale Logik
                if target_reached:
                    final_status = 'success'  # Ziel erreicht
                else:
                    final_status = 'failed'  # Ziel nicht erreicht
            
            # Update Status
            await pool.execute("""
                UPDATE alert_evaluations
                SET status = $1,
                    actual_value_at_evaluation = $2,
                    evaluated_at = NOW(),
                    updated_at = NOW()
                WHERE id = $3
            """,
                final_status,
                actual_value,
                alert['id']
            )
            
            stats['evaluated'] += 1
            if final_status == 'success':
                stats['success'] += 1
            elif final_status == 'failed':
                stats['failed'] += 1
                
        except Exception as e:
            logger.error(f"❌ Fehler bei Auswertung von Alert {alert['id']}: {e}", exc_info=True)
    
    return stats

# ============================================================
# Alert-Abfragen
# ============================================================

async def get_alerts(
    status: Optional[str] = None,
    model_id: Optional[int] = None,
    coin_id: Optional[str] = None,
    prediction_type: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    unique_coins: bool = True,  # Nur ältester Alert pro Coin
    include_non_alerts: bool = False,  # NEU: Auch Vorhersagen unter Threshold anzeigen
    limit: int = 100,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Holt Alerts mit Filtern.
    
    Args:
        status: Filter nach Status ('pending', 'success', 'failed', 'expired')
        model_id: Filter nach Modell-ID
        coin_id: Filter nach Coin-ID
        prediction_type: Filter nach Typ ('time_based', 'classic')
        date_from: Filter ab Datum
        date_to: Filter bis Datum
        unique_coins: Wenn True, nur ältester Alert pro Coin
        include_non_alerts: Wenn True, auch Vorhersagen unter dem Alert-Threshold anzeigen
        limit: Maximale Anzahl
        offset: Offset für Pagination
        
    Returns:
        Dict mit 'alerts' (Liste) und 'total' (Anzahl)
    """
    pool = await get_pool()
    
    # Hole Alert-Threshold für das Modell (falls model_id gegeben)
    alert_threshold = 0.7  # Default
    if model_id:
        threshold_row = await pool.fetchrow("""
            SELECT alert_threshold 
            FROM prediction_active_models 
            WHERE model_id = $1 
            LIMIT 1
        """, model_id)
        if threshold_row and threshold_row.get('alert_threshold'):
            alert_threshold = float(threshold_row['alert_threshold'])
    
    # WHERE-Klausel bauen
    conditions = []
    params = []
    param_idx = 1
    
    if status:
        conditions.append(f"ae.status = ${param_idx}")
        params.append(status)
        param_idx += 1
    elif include_non_alerts:
        # Wenn include_non_alerts=True und kein Status-Filter, schließe auch 'non_alert' ein
        # Aber nur wenn es keine explizite Status-Filterung gibt
        # Wir fügen hier nichts hinzu, da wir alle Status zurückgeben wollen
        pass
    
    if model_id:
        conditions.append(f"ae.model_id = ${param_idx}")
        params.append(model_id)
        param_idx += 1
    
    if coin_id:
        conditions.append(f"ae.coin_id = ${param_idx}")
        params.append(coin_id)
        param_idx += 1
    
    if prediction_type:
        conditions.append(f"ae.prediction_type = ${param_idx}")
        params.append(prediction_type)
        param_idx += 1
    
    if date_from:
        conditions.append(f"ae.alert_timestamp >= ${param_idx}")
        params.append(date_from)
        param_idx += 1
    
    if date_to:
        conditions.append(f"ae.alert_timestamp <= ${param_idx}")
        params.append(date_to)
        param_idx += 1
    
    # WICHTIG: Wenn include_non_alerts=True, müssen wir auch 'non_alert' Einträge aus alert_evaluations zurückgeben
    # Daher erweitern wir die where_clause, um 'non_alert' Status einzuschließen
    if include_non_alerts and not status:
        # Wenn include_non_alerts=True und kein Status-Filter gesetzt, schließe auch 'non_alert' ein
        # Aber nur wenn es keine explizite Status-Filterung gibt
        pass  # Status-Filter wird später angepasst
    
    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
    
    # Wenn include_non_alerts=True, hole auch Vorhersagen unter dem Threshold
    if include_non_alerts and model_id:
        # Baue WHERE-Klausel für predictions (nur positive Vorhersagen unter Threshold)
        # WICHTIG: Für UNION-Query müssen Parameter-Platzhalter eindeutig sein!
        # where_clause verwendet bereits $1, $2, ..., $param_idx
        # pred_where muss bei $param_idx+1 starten (also len(params) + 1)
        pred_conditions = []
        pred_params = []
        
        # Finde ob model_id bereits in params ist (wird in where_clause verwendet)
        model_param_idx = None
        for i, p in enumerate(params):
            if p == model_id:
                model_param_idx = i + 1  # +1 weil Parameter bei $1 starten
                break
        
        if model_param_idx:
            # model_id ist bereits in params, verwende den gleichen Parameter-Platzhalter
            pred_conditions.append(f"p.model_id = ${model_param_idx}")
            # NICHT zu pred_params hinzufügen - wird bereits von params bereitgestellt
        else:
            # model_id ist nicht in params (sollte nicht passieren, aber sicherheitshalber)
            pred_idx = len(params) + 1
            pred_conditions.append(f"p.model_id = ${pred_idx}")
            pred_params.append(model_id)
        
        # Nur Vorhersagen unter dem Threshold und prediction = 1
        pred_conditions.append(f"p.probability < {alert_threshold}::float")
        pred_conditions.append("p.prediction = 1")
        
        # Nicht in alert_evaluations (um Duplikate zu vermeiden)
        pred_conditions.append("NOT EXISTS (SELECT 1 FROM alert_evaluations ae2 WHERE ae2.prediction_id = p.id)")
        
        # Berechne nächsten Parameter-Index (für neue Parameter)
        next_param_idx = len(params) + len(pred_params) + 1
        
        if coin_id:
            # Prüfe ob coin_id bereits in params ist
            coin_param_idx = None
            for i, p in enumerate(params):
                if p == coin_id:
                    coin_param_idx = i + 1
                    break
            
            if coin_param_idx:
                pred_conditions.append(f"p.coin_id = ${coin_param_idx}")
            else:
                pred_conditions.append(f"p.coin_id = ${next_param_idx}")
                pred_params.append(coin_id)
                next_param_idx += 1
        
        if date_from:
            # Prüfe ob date_from bereits in params ist
            date_from_param_idx = None
            for i, p in enumerate(params):
                if p == date_from:
                    date_from_param_idx = i + 1
                    break
            
            if date_from_param_idx:
                pred_conditions.append(f"p.data_timestamp >= ${date_from_param_idx}")
            else:
                pred_conditions.append(f"p.data_timestamp >= ${next_param_idx}")
                pred_params.append(date_from)
                next_param_idx += 1
        
        if date_to:
            # Prüfe ob date_to bereits in params ist
            date_to_param_idx = None
            for i, p in enumerate(params):
                if p == date_to:
                    date_to_param_idx = i + 1
                    break
            
            if date_to_param_idx:
                pred_conditions.append(f"p.data_timestamp <= ${date_to_param_idx}")
            else:
                pred_conditions.append(f"p.data_timestamp <= ${next_param_idx}")
                pred_params.append(date_to)
                next_param_idx += 1
        
        pred_where = "WHERE " + " AND ".join(pred_conditions) if pred_conditions else ""
        
        # UNION Query: Alerts + Non-Alerts
        # Zähle Gesamtanzahl
        # WICHTIG: pred_where verwendet f-strings für alert_threshold (kein Parameter)
        # Aber pred_where kann trotzdem Parameter-Platzhalter haben (coin_id, date_from, date_to)
        # Die Platzhalter in pred_where müssen neu nummeriert werden, da where_clause bereits $1, $2, etc. verwendet
        
        # Zähle Parameter-Platzhalter in where_clause
        where_param_count = len(params)
        
        # Renummiere Parameter in pred_where (falls vorhanden)
        # pred_where verwendet bereits korrekte Platzhalter-Nummern (pred_idx)
        # Aber für die UNION-Query müssen wir sicherstellen, dass die Nummern korrekt sind
        
        if unique_coins:
            count_query = f"""
                SELECT COUNT(DISTINCT coin_id) as total FROM (
                    SELECT ae.coin_id FROM alert_evaluations ae {where_clause}
                    UNION
                    SELECT p.coin_id FROM predictions p {pred_where}
                ) combined
            """
        else:
            count_query = f"""
                SELECT COUNT(*) as total FROM (
                    SELECT 1 FROM alert_evaluations ae {where_clause}
                    UNION ALL
                    SELECT 1 FROM predictions p {pred_where}
                ) combined
            """
        
        # Führe count_query aus
        # Kombiniere Parameter: params (für where_clause) + pred_params (für pred_where)
        all_count_params = list(params) + list(pred_params)
        
        # Debug-Logging
        logger.info(f"🔍 get_alerts: include_non_alerts={include_non_alerts}, model_id={model_id}, unique_coins={unique_coins}")
        logger.info(f"🔍 params: {params}, pred_params: {pred_params}")
        logger.info(f"🔍 param_idx: {len(params) + len(pred_params)}, LIMIT: ${len(params) + len(pred_params) + 1}, OFFSET: ${len(params) + len(pred_params) + 2}")
        
        if all_count_params:
            total_row = await pool.fetchrow(count_query, *all_count_params)
        else:
            total_row = await pool.fetchrow(count_query)
        total = total_row['total'] if total_row else 0
        
        # Hole Alerts + Non-Alerts mit UNION
        # WICHTIG: unique_coins funktioniert nicht mit UNION (DISTINCT ON ist ambiguous)
        # Daher deaktivieren wir unique_coins für include_non_alerts
        if unique_coins and not include_non_alerts:
            # Für unique_coins: Hole neuesten pro Coin
            # WICHTIG: DISTINCT ON muss nach der UNION angewendet werden, daher verwenden wir einen Subquery
            query = f"""
                SELECT DISTINCT ON (combined.coin_id) combined.* FROM (
                    SELECT 
                        ae.id, ae.prediction_id, ae.coin_id, ae.model_id,
                        ae.prediction_type, COALESCE(ae.probability, p.probability) as probability,
                        ae.target_variable, ae.future_minutes, ae.price_change_percent, ae.target_direction,
                        ae.target_operator, ae.target_value,
                        ae.alert_timestamp, ae.evaluation_timestamp,
                        ae.price_close_at_alert, ae.price_open_at_alert, ae.price_high_at_alert, ae.price_low_at_alert,
                        ae.market_cap_close_at_alert, ae.market_cap_open_at_alert,
                        ae.volume_sol_at_alert, ae.volume_usd_at_alert,
                        ae.buy_volume_sol_at_alert, ae.sell_volume_sol_at_alert,
                        ae.num_buys_at_alert, ae.num_sells_at_alert,
                        ae.unique_wallets_at_alert, ae.phase_id_at_alert,
                        ae.price_close_at_evaluation, ae.price_open_at_evaluation, ae.price_high_at_evaluation, ae.price_low_at_evaluation,
                        ae.market_cap_close_at_evaluation, ae.market_cap_open_at_evaluation,
                        ae.volume_sol_at_evaluation, ae.volume_usd_at_evaluation,
                        ae.buy_volume_sol_at_evaluation, ae.sell_volume_sol_at_evaluation,
                        ae.num_buys_at_evaluation, ae.num_sells_at_evaluation,
                        ae.unique_wallets_at_evaluation, ae.phase_id_at_evaluation,
                        ae.actual_price_change_pct, ae.actual_value_at_evaluation,
                        ae.ath_price_change_pct, ae.ath_timestamp, ae.ath_price_close,
                        ae.status, ae.evaluated_at, ae.evaluation_note, ae.created_at, ae.updated_at,
                        ae.coin_id as coin_id
                    FROM alert_evaluations ae
                    LEFT JOIN predictions p ON p.id = ae.prediction_id
                    {where_clause}
                    UNION ALL
                    SELECT 
                        p.id + 1000000000 as id,  -- Offset um Konflikte zu vermeiden
                        p.id as prediction_id, p.coin_id, p.model_id,
                        NULL as prediction_type, p.probability,
                        NULL as target_variable, NULL as future_minutes, NULL as price_change_percent, NULL as target_direction,
                        NULL as target_operator, NULL as target_value,
                        p.data_timestamp as alert_timestamp, NULL as evaluation_timestamp,
                        NULL as price_close_at_alert, NULL as price_open_at_alert, NULL as price_high_at_alert, NULL as price_low_at_alert,
                        NULL as market_cap_close_at_alert, NULL as market_cap_open_at_alert,
                        NULL as volume_sol_at_alert, NULL as volume_usd_at_alert,
                        NULL as buy_volume_sol_at_alert, NULL as sell_volume_sol_at_alert,
                        NULL as num_buys_at_alert, NULL as num_sells_at_alert,
                        NULL as unique_wallets_at_alert, NULL as phase_id_at_alert,
                        NULL as price_close_at_evaluation, NULL as price_open_at_evaluation, NULL as price_high_at_evaluation, NULL as price_low_at_evaluation,
                        NULL as market_cap_close_at_evaluation, NULL as market_cap_open_at_evaluation,
                        NULL as volume_sol_at_evaluation, NULL as volume_usd_at_evaluation,
                        NULL as buy_volume_sol_at_evaluation, NULL as sell_volume_sol_at_evaluation,
                        NULL as num_buys_at_evaluation, NULL as num_sells_at_evaluation,
                        NULL as unique_wallets_at_evaluation, NULL as phase_id_at_evaluation,
                        NULL as actual_price_change_pct, NULL as actual_value_at_evaluation,
                        NULL as ath_price_change_pct, NULL as ath_timestamp, NULL as ath_price_close,
                        'non_alert' as status, NULL as evaluated_at, NULL as evaluation_note, p.created_at, p.created_at as updated_at,
                        p.coin_id as coin_id
                    FROM predictions p
                    {pred_where}
                ) combined
                ORDER BY 
                    alert_timestamp DESC,  -- Neueste zuerst (unabhängig vom Status)
                    id DESC  -- Dann nach ID für Konsistenz
                LIMIT ${len(params) + len(pred_params) + 1} OFFSET ${len(params) + len(pred_params) + 2}
            """
        else:
            # Kombiniere alle Parameter für die Haupt-Query
            # Reihenfolge: params (für alert_evaluations), pred_params (für predictions), limit, offset
            # WICHTIG: param_idx muss die Gesamtzahl der Parameter sein (params + pred_params)
            param_idx = len(params) + len(pred_params)
            
            # Sortiere nach alert_timestamp DESC (neueste zuerst), dann nach status (pending zuerst)
            query = f"""
                SELECT * FROM (
                    SELECT 
                        ae.id, ae.prediction_id, ae.coin_id, ae.model_id,
                        ae.prediction_type, COALESCE(ae.probability, p.probability) as probability,
                        ae.target_variable, ae.future_minutes, ae.price_change_percent, ae.target_direction,
                        ae.target_operator, ae.target_value,
                        ae.alert_timestamp, ae.evaluation_timestamp,
                        ae.price_close_at_alert, ae.price_open_at_alert, ae.price_high_at_alert, ae.price_low_at_alert,
                        ae.market_cap_close_at_alert, ae.market_cap_open_at_alert,
                        ae.volume_sol_at_alert, ae.volume_usd_at_alert,
                        ae.buy_volume_sol_at_alert, ae.sell_volume_sol_at_alert,
                        ae.num_buys_at_alert, ae.num_sells_at_alert,
                        ae.unique_wallets_at_alert, ae.phase_id_at_alert,
                        ae.price_close_at_evaluation, ae.price_open_at_evaluation, ae.price_high_at_evaluation, ae.price_low_at_evaluation,
                        ae.market_cap_close_at_evaluation, ae.market_cap_open_at_evaluation,
                        ae.volume_sol_at_evaluation, ae.volume_usd_at_evaluation,
                        ae.buy_volume_sol_at_evaluation, ae.sell_volume_sol_at_evaluation,
                        ae.num_buys_at_evaluation, ae.num_sells_at_evaluation,
                        ae.unique_wallets_at_evaluation, ae.phase_id_at_evaluation,
                        ae.actual_price_change_pct, ae.actual_value_at_evaluation,
                        ae.ath_price_change_pct, ae.ath_timestamp, ae.ath_price_close,
                        ae.status, ae.evaluated_at, ae.evaluation_note, ae.created_at, ae.updated_at
                    FROM alert_evaluations ae
                    LEFT JOIN predictions p ON p.id = ae.prediction_id
                    {where_clause}
                    UNION ALL
                    SELECT 
                        p.id + 1000000000 as id,  -- Offset um Konflikte zu vermeiden
                        p.id as prediction_id, p.coin_id, p.model_id,
                        NULL as prediction_type, p.probability,
                        NULL as target_variable, NULL as future_minutes, NULL as price_change_percent, NULL as target_direction,
                        NULL as target_operator, NULL as target_value,
                        p.data_timestamp as alert_timestamp, NULL as evaluation_timestamp,
                        NULL as price_close_at_alert, NULL as price_open_at_alert, NULL as price_high_at_alert, NULL as price_low_at_alert,
                        NULL as market_cap_close_at_alert, NULL as market_cap_open_at_alert,
                        NULL as volume_sol_at_alert, NULL as volume_usd_at_alert,
                        NULL as buy_volume_sol_at_alert, NULL as sell_volume_sol_at_alert,
                        NULL as num_buys_at_alert, NULL as num_sells_at_alert,
                        NULL as unique_wallets_at_alert, NULL as phase_id_at_alert,
                        NULL as price_close_at_evaluation, NULL as price_open_at_evaluation, NULL as price_high_at_evaluation, NULL as price_low_at_evaluation,
                        NULL as market_cap_close_at_evaluation, NULL as market_cap_open_at_evaluation,
                        NULL as volume_sol_at_evaluation, NULL as volume_usd_at_evaluation,
                        NULL as buy_volume_sol_at_evaluation, NULL as sell_volume_sol_at_evaluation,
                        NULL as num_buys_at_evaluation, NULL as num_sells_at_evaluation,
                        NULL as unique_wallets_at_evaluation, NULL as phase_id_at_evaluation,
                        NULL as actual_price_change_pct, NULL as actual_value_at_evaluation,
                        NULL as ath_price_change_pct, NULL as ath_timestamp, NULL as ath_price_close,
                        'non_alert' as status, NULL as evaluated_at, NULL as evaluation_note, p.created_at, p.created_at as updated_at
                    FROM predictions p
                    {pred_where}
                ) combined
                ORDER BY 
                    alert_timestamp DESC,  -- Neueste zuerst (unabhängig vom Status)
                    id DESC  -- Dann nach ID für Konsistenz
                LIMIT ${param_idx + 1} OFFSET ${param_idx + 2}
            """
            
            all_query_params = list(params) + list(pred_params) + [limit, offset]
            rows = await pool.fetch(query, *all_query_params)
    else:
        # Nur Alerts (wie bisher)
        if unique_coins:
            count_query = f"""
                SELECT COUNT(DISTINCT ae.coin_id) as total
                FROM alert_evaluations ae
                {where_clause}
            """
        else:
            count_query = f"""
                SELECT COUNT(*) as total
                FROM alert_evaluations ae
                {where_clause}
            """
    
    total_row = await pool.fetchrow(count_query, *params)
    total = total_row['total'] if total_row else 0
    
    # Hole Alerts (mit probability aus predictions falls nicht in alert_evaluations)
    params.extend([limit, offset])
    if unique_coins:
        query = f"""
            SELECT DISTINCT ON (ae.coin_id)
                ae.*,
                COALESCE(ae.probability, p.probability) as probability
            FROM alert_evaluations ae
            LEFT JOIN predictions p ON p.id = ae.prediction_id
            {where_clause}
            ORDER BY ae.coin_id, ae.alert_timestamp DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
    else:
        query = f"""
            SELECT
                ae.*,
                COALESCE(ae.probability, p.probability) as probability
            FROM alert_evaluations ae
            LEFT JOIN predictions p ON p.id = ae.prediction_id
            {where_clause}
                ORDER BY
                    ae.alert_timestamp DESC,  -- Neueste zuerst (unabhängig vom Status)
                    ae.id DESC  -- Dann nach ID für Konsistenz
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
    rows = await pool.fetch(query, *params)
    
    # OPTIMIERT: Hole alle Modell-Namen in einem Query (statt N+1 Queries)
    model_ids = list(set([row['model_id'] for row in rows if row.get('model_id')]))
    model_names_dict = {}
    if model_ids:
        model_rows = await pool.fetch("""
            SELECT id, model_name, custom_name
            FROM prediction_active_models
            WHERE id = ANY($1::bigint[])
        """, model_ids)
        model_names_dict = {
            row['id']: row.get('custom_name') or row.get('model_name', f"Modell {row['id']}")
            for row in model_rows
        }
    
    # Konvertiere zu Dicts
    alerts = []
    for row in rows:
        alert = dict(row)
        
        # Berechne verbleibende Zeit (bei pending)
        if alert['status'] == 'pending' and alert['evaluation_timestamp']:
            now = datetime.now(timezone.utc)
            eval_time = alert['evaluation_timestamp']
            if isinstance(eval_time, str):
                eval_time = datetime.fromisoformat(eval_time.replace('Z', '+00:00'))
            remaining = (eval_time - now).total_seconds()
            alert['remaining_seconds'] = max(0, int(remaining))
        else:
            alert['remaining_seconds'] = None
        
        # Hole Modell-Name aus Cache (optimiert)
        model_id = alert.get('model_id')
        if model_id and model_id in model_names_dict:
            alert['model_name'] = model_names_dict[model_id]
        else:
            # Fallback: Einzelner Query nur wenn nicht im Cache
            model_row = await pool.fetchrow("""
                SELECT model_name, custom_name
                FROM prediction_active_models
                WHERE model_id = $1
                LIMIT 1
            """, alert['model_id'])
            
            if model_row:
                alert['model_name'] = model_row.get('custom_name') or model_row.get('model_name', f"ID: {alert['model_id']}")
            else:
                alert['model_name'] = f"ID: {alert['model_id']}"
        
        # Zähle weitere Alerts für diesen Coin (wenn unique_coins)
        if unique_coins:
            other_count = await pool.fetchval("""
                SELECT COUNT(*) - 1
                FROM alert_evaluations
                WHERE coin_id = $1
            """, alert['coin_id'])
            alert['other_alerts_count'] = max(0, other_count)
        else:
            alert['other_alerts_count'] = 0
        
        # Stelle sicher, dass probability vorhanden ist
        if alert.get('probability') is None:
            # Hole aus predictions falls nicht vorhanden
            prob_row = await pool.fetchrow("""
                SELECT probability FROM predictions WHERE id = $1
            """, alert['prediction_id'])
            if prob_row:
                alert['probability'] = float(prob_row['probability'])
            else:
                alert['probability'] = 0.0
        
        # Füge alert_threshold zum Alert hinzu (für Frontend-Anzeige)
        alert['alert_threshold'] = alert_threshold
        
        alerts.append(alert)
    
    # Hole Statistiken
    # WICHTIG: params enthält limit und offset am Ende, die müssen entfernt werden
    stats_params = params[:-2] if len(params) >= 2 else params
    stats_row = await pool.fetchrow(f"""
        SELECT 
            COUNT(*) FILTER (WHERE ae.status = 'pending') as pending,
            COUNT(*) FILTER (WHERE ae.status = 'success') as success,
            COUNT(*) FILTER (WHERE ae.status = 'failed') as failed,
            COUNT(*) FILTER (WHERE ae.status = 'expired') as expired
        FROM alert_evaluations ae
        {where_clause}
    """, *stats_params) if stats_params else await pool.fetchrow(f"""
        SELECT 
            COUNT(*) FILTER (WHERE ae.status = 'pending') as pending,
            COUNT(*) FILTER (WHERE ae.status = 'success') as success,
            COUNT(*) FILTER (WHERE ae.status = 'failed') as failed,
            COUNT(*) FILTER (WHERE ae.status = 'expired') as expired
        FROM alert_evaluations ae
        {where_clause}
    """)
    
    stats = {
        'pending': stats_row['pending'] if stats_row else 0,
        'success': stats_row['success'] if stats_row else 0,
        'failed': stats_row['failed'] if stats_row else 0,
        'expired': stats_row['expired'] if stats_row else 0
    }
    
    return {
        'alerts': alerts,
        'total': total,
        **stats
    }

async def get_coin_evaluations_for_model(
    coin_id: str,
    active_model_id: int,
    start_timestamp: datetime,
    end_timestamp: Optional[datetime] = None,
    pool: Optional[asyncpg.Pool] = None
) -> List[Dict[str, Any]]:
    """
    Holt alle Alert-Auswertungen für einen Coin und ein Modell.
    
    Args:
        coin_id: Coin-Mint-Adresse
        active_model_id: ID des aktiven Modells
        start_timestamp: Start-Zeitpunkt
        end_timestamp: Optional: End-Zeitpunkt
        pool: Optional: DB-Pool
    
    Returns:
        Liste von Dicts mit evaluation_id, evaluation_timestamp, status, actual_price_change
    """
    if pool is None:
        pool = await get_pool()
    
    if end_timestamp is None:
        end_timestamp = datetime.now(timezone.utc)
    
    try:
        # WICHTIG: Hole auch aus model_predictions (neue Tabelle)!
        # UNION ALL um beide Quellen zu kombinieren
        # FIX: Spalten-Reihenfolge muss in beiden SELECTs identisch sein!
        rows = await pool.fetch("""
            SELECT
                ae.id,
                ae.alert_timestamp,
                ae.evaluation_timestamp,
                ae.status,
                ae.actual_price_change_pct as actual_price_change,
                ae.price_change_percent as expected_price_change,
                p.data_timestamp as prediction_timestamp,
                COALESCE(ae.probability, p.probability) as probability
            FROM alert_evaluations ae
            JOIN predictions p ON ae.prediction_id = p.id
            WHERE p.coin_id = $1
              AND p.active_model_id = $2
              AND p.data_timestamp >= $3
              AND p.data_timestamp <= $4
            UNION ALL
            SELECT
                mp.id,
                mp.prediction_timestamp as alert_timestamp,
                mp.evaluated_at as evaluation_timestamp,
                mp.evaluation_result as status,
                mp.actual_price_change_pct as actual_price_change,
                pam.price_change_percent as expected_price_change,
                mp.prediction_timestamp,
                mp.probability
            FROM model_predictions mp
            JOIN prediction_active_models pam ON pam.id = mp.active_model_id
            WHERE mp.coin_id = $1
              AND mp.active_model_id = $2
              AND mp.prediction_timestamp >= $3
              AND mp.prediction_timestamp <= $4
              AND mp.evaluation_result IS NOT NULL
            ORDER BY prediction_timestamp ASC, evaluation_timestamp ASC NULLS LAST
        """, coin_id, active_model_id, start_timestamp, end_timestamp)
        
        return [
            {
                'id': row['id'],
                'evaluation_timestamp': row['evaluation_timestamp'],
                'prediction_timestamp': row['prediction_timestamp'],
                'status': row['status'],
                # WICHTIG: actual_price_change_pct ist bereits in Prozent (z.B. 46.4286), nicht Dezimal!
                # Konvertiere zu Dezimal für Frontend (z.B. 46.4286% -> 0.464286)
                'actual_price_change': float(row['actual_price_change']) / 100.0 if row['actual_price_change'] else None,
                'expected_price_change': float(row['expected_price_change']) if row['expected_price_change'] else None,
                'probability': float(row['probability']) if row['probability'] else None
            }
            for row in rows
        ]
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Auswertungen für Coin {coin_id} und Modell {active_model_id}: {e}")
        return []

async def get_alert_details(
    alert_id: int,
    chart_before_minutes: int = 10,
    chart_after_minutes: int = 10
) -> Optional[Dict[str, Any]]:
    """
    Holt detaillierte Informationen zu einem Alert.
    
    Args:
        alert_id: Alert-ID
        chart_before_minutes: Minuten vor Alert für Chart
        chart_after_minutes: Minuten nach Auswertung für Chart
        
    Returns:
        Dict mit Alert-Details, Metriken, Historie, etc.
    """
    pool = await get_pool()
    
    # Hole Alert
    alert_row = await pool.fetchrow("""
        SELECT ae.*, COALESCE(ae.probability, p.probability) as probability FROM alert_evaluations ae LEFT JOIN predictions p ON p.id = ae.prediction_id
        WHERE ae.id = $1
    """, alert_id)
    
    if not alert_row:
        return None
    
    alert = dict(alert_row)
    
    # Hole Modell-Name
    model_row = await pool.fetchrow("""
        SELECT model_name, custom_name
        FROM prediction_active_models
        WHERE model_id = $1
        LIMIT 1
    """, alert['model_id'])
    
    if model_row:
        alert['model_name'] = model_row.get('custom_name') or model_row.get('model_name', f"ID: {alert['model_id']}")
    else:
        alert['model_name'] = f"ID: {alert['model_id']}"
    
    # Hole Metriken zum Zeitpunkt des Alerts (bereits in alert gespeichert)
    coin_values_at_alert = {
        'price_close': float(alert['price_close_at_alert']) if alert['price_close_at_alert'] else None,
        'price_open': float(alert['price_open_at_alert']) if alert['price_open_at_alert'] else None,
        'price_high': float(alert['price_high_at_alert']) if alert['price_high_at_alert'] else None,
        'price_low': float(alert['price_low_at_alert']) if alert['price_low_at_alert'] else None,
        'market_cap_close': float(alert['market_cap_close_at_alert']) if alert['market_cap_close_at_alert'] else None,
        'market_cap_open': float(alert['market_cap_open_at_alert']) if alert['market_cap_open_at_alert'] else None,
        'volume_sol': float(alert['volume_sol_at_alert']) if alert['volume_sol_at_alert'] else None,
        'volume_usd': float(alert['volume_usd_at_alert']) if alert['volume_usd_at_alert'] else None,
        'buy_volume_sol': float(alert['buy_volume_sol_at_alert']) if alert['buy_volume_sol_at_alert'] else None,
        'sell_volume_sol': float(alert['sell_volume_sol_at_alert']) if alert['sell_volume_sol_at_alert'] else None,
        'num_buys': int(alert['num_buys_at_alert']) if alert['num_buys_at_alert'] else None,
        'num_sells': int(alert['num_sells_at_alert']) if alert['num_sells_at_alert'] else None,
        'unique_wallets': int(alert['unique_wallets_at_alert']) if alert['unique_wallets_at_alert'] else None,
        'phase_id': int(alert['phase_id_at_alert']) if alert['phase_id_at_alert'] else None
    }
    
    # Hole Metriken zur Auswertung (wenn ausgewertet)
    coin_values_at_evaluation = None
    if alert['status'] in ('success', 'failed') and alert['evaluation_timestamp']:
        coin_values_at_evaluation = {
            'price_close': float(alert['price_close_at_evaluation']) if alert['price_close_at_evaluation'] else None,
            'price_open': float(alert['price_open_at_evaluation']) if alert['price_open_at_evaluation'] else None,
            'price_high': float(alert['price_high_at_evaluation']) if alert['price_high_at_evaluation'] else None,
            'price_low': float(alert['price_low_at_evaluation']) if alert['price_low_at_evaluation'] else None,
            'market_cap_close': float(alert['market_cap_close_at_evaluation']) if alert['market_cap_close_at_evaluation'] else None,
            'market_cap_open': float(alert['market_cap_open_at_evaluation']) if alert['market_cap_open_at_evaluation'] else None,
            'volume_sol': float(alert['volume_sol_at_evaluation']) if alert['volume_sol_at_evaluation'] else None,
            'volume_usd': float(alert['volume_usd_at_evaluation']) if alert['volume_usd_at_evaluation'] else None,
            'buy_volume_sol': float(alert['buy_volume_sol_at_evaluation']) if alert['buy_volume_sol_at_evaluation'] else None,
            'sell_volume_sol': float(alert['sell_volume_sol_at_evaluation']) if alert['sell_volume_sol_at_evaluation'] else None,
            'num_buys': int(alert['num_buys_at_evaluation']) if alert['num_buys_at_evaluation'] else None,
            'num_sells': int(alert['num_sells_at_evaluation']) if alert['num_sells_at_evaluation'] else None,
            'unique_wallets': int(alert['unique_wallets_at_evaluation']) if alert['unique_wallets_at_evaluation'] else None,
            'phase_id': int(alert['phase_id_at_evaluation']) if alert['phase_id_at_evaluation'] else None
        }
    
    # Hole Preis-Historie für Chart
    alert_timestamp = alert['alert_timestamp']
    if isinstance(alert_timestamp, str):
        alert_timestamp = datetime.fromisoformat(alert_timestamp.replace('Z', '+00:00'))
    
    eval_timestamp = alert['evaluation_timestamp']
    if eval_timestamp:
        if isinstance(eval_timestamp, str):
            eval_timestamp = datetime.fromisoformat(eval_timestamp.replace('Z', '+00:00'))
    else:
        eval_timestamp = datetime.now(timezone.utc)
    
    chart_start = alert_timestamp - timedelta(minutes=chart_before_minutes)
    chart_end = eval_timestamp + timedelta(minutes=chart_after_minutes)
    
    history_rows = await pool.fetch("""
        SELECT 
            timestamp,
            price_close, price_high, price_low,
            volume_sol,
            market_cap_close
        FROM coin_metrics
        WHERE mint = $1
          AND timestamp >= $2
          AND timestamp <= $3
        ORDER BY timestamp ASC
    """, alert['coin_id'], chart_start, chart_end)
    
    price_history = []
    volume_history = []
    market_cap_history = []
    
    for row in history_rows:
        ts = row['timestamp']
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        
        price_history.append({
            'timestamp': ts.isoformat(),
            'price_close': float(row['price_close']) if row['price_close'] else None,
            'price_high': float(row['price_high']) if row['price_high'] else None,
            'price_low': float(row['price_low']) if row['price_low'] else None
        })
        
        volume_history.append({
            'timestamp': ts.isoformat(),
            'volume_sol': float(row['volume_sol']) if row['volume_sol'] else None
        })
        
        market_cap_history.append({
            'timestamp': ts.isoformat(),
            'market_cap_close': float(row['market_cap_close']) if row['market_cap_close'] else None
        })
    
    # Hole alle weiteren Alerts für diesen Coin
    other_alerts = await pool.fetch("""
        SELECT ae.id, ae.alert_timestamp, ae.model_id, ae.status, COALESCE(ae.probability, p.probability) as probability
        FROM alert_evaluations ae LEFT JOIN predictions p ON p.id = ae.prediction_id
        WHERE ae.coin_id = $1
          AND ae.id != $2
        ORDER BY ae.alert_timestamp ASC
    """, alert['coin_id'], alert_id)
    
    other_alerts_list = []
    for row in other_alerts:
        model_row = await pool.fetchrow("""
            SELECT model_name, custom_name
            FROM prediction_active_models
            WHERE model_id = $1
            LIMIT 1
        """, row['model_id'])
        
        model_name = model_row.get('custom_name') or model_row.get('model_name', f"ID: {row['model_id']}") if model_row else f"ID: {row['model_id']}"
        
        other_alerts_list.append({
            'id': row['id'],
            'alert_timestamp': row['alert_timestamp'].isoformat() if isinstance(row['alert_timestamp'], datetime) else str(row['alert_timestamp']),
            'model_name': model_name,
            'status': row['status'],
            'probability': float(row['probability']) if row.get('probability') else None
        })
    
    # Hole Statistiken für dieses Modell
    stats_row = await pool.fetchrow("""
        SELECT 
            COUNT(*) as total_alerts,
            COUNT(*) FILTER (WHERE ae.status = 'success') as success_count,
            COUNT(*) FILTER (WHERE ae.status = 'failed') as failed_count,
            AVG(actual_price_change_pct) FILTER (WHERE ae.status = 'success' AND prediction_type = 'time_based') as avg_actual_change,
            AVG(price_change_percent) FILTER (WHERE ae.prediction_type = 'time_based') as avg_expected_change
        FROM alert_evaluations ae
        WHERE ae.model_id = $1
    """, alert['model_id'])
    
    statistics = {
        'model_total_alerts': stats_row['total_alerts'] if stats_row else 0,
        'model_success_count': stats_row['success_count'] if stats_row else 0,
        'model_failed_count': stats_row['failed_count'] if stats_row else 0,
        'model_success_rate': (stats_row['success_count'] / stats_row['total_alerts'] * 100) if stats_row and stats_row['total_alerts'] > 0 else 0,
        'model_avg_actual_change': float(stats_row['avg_actual_change']) if stats_row and stats_row['avg_actual_change'] else None,
        'model_avg_expected_change': float(stats_row['avg_expected_change']) if stats_row and stats_row['avg_expected_change'] else None
    }
    
    return {
        'alert': alert,
        'coin_values_at_alert': coin_values_at_alert,
        'coin_values_at_evaluation': coin_values_at_evaluation,
        'price_history': price_history,
        'volume_history': volume_history,
        'market_cap_history': market_cap_history,
        'other_alerts': other_alerts_list,
        'statistics': statistics
    }

async def get_alert_statistics(
    model_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Holt Alert-Statistiken aus model_predictions Tabelle (NEUE ARCHITEKTUR).
    
    Args:
        model_id: Filter nach active_model_id (optional)
        date_from: Filter ab Datum (optional)
        date_to: Filter bis Datum (optional)
        
    Returns:
        Dict mit Statistiken
    """
    pool = await get_pool()
    
    conditions = []
    params = []
    param_idx = 1
    
    # Filter nach active_model_id (model_id wird als active_model_id interpretiert)
    if model_id:
        conditions.append(f"mp.active_model_id = ${param_idx}")
        params.append(model_id)
        param_idx += 1
    
    if date_from:
        conditions.append(f"mp.prediction_timestamp >= ${param_idx}")
        params.append(date_from)
        param_idx += 1
    
    if date_to:
        conditions.append(f"mp.prediction_timestamp <= ${param_idx}")
        params.append(date_to)
        param_idx += 1
    
    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
    
    # NEUE ARCHITEKTUR: Verwende model_predictions Tabelle
    # Hole alert_threshold aus prediction_active_models (falls model_id gegeben)
    alert_threshold = 0.95  # Default
    if model_id:
        threshold_row = await pool.fetchrow("""
            SELECT alert_threshold FROM prediction_active_models WHERE id = $1
        """, model_id)
        if threshold_row and threshold_row['alert_threshold']:
            alert_threshold = float(threshold_row['alert_threshold'])
    
    # Erweiterte Statistiken: Alerts vs. Nicht-Alerts mit detaillierten Status-Breakdowns
    if params:
        query = f"""
        SELECT 
            COUNT(*) as total_alerts,
            COUNT(*) FILTER (WHERE mp.status = 'aktiv') as pending,
            COUNT(*) FILTER (WHERE mp.status = 'inaktiv' AND mp.evaluation_result = 'success') as success,
            COUNT(*) FILTER (WHERE mp.status = 'inaktiv' AND mp.evaluation_result = 'failed') as failed,
            COUNT(*) FILTER (WHERE mp.status = 'inaktiv' AND mp.evaluation_result = 'not_applicable') as expired,
            COUNT(*) FILTER (WHERE mp.tag = 'alert') as alerts_above_threshold,
            -- Alerts (tag = 'alert') Statistiken
            COUNT(*) FILTER (
                WHERE mp.tag = 'alert' AND mp.status = 'inaktiv' AND mp.evaluation_result = 'success'
            ) as alerts_success,
            COUNT(*) FILTER (
                WHERE mp.tag = 'alert' AND mp.status = 'inaktiv' AND mp.evaluation_result = 'failed'
            ) as alerts_failed,
            COUNT(*) FILTER (
                WHERE mp.tag = 'alert' AND mp.status = 'aktiv'
            ) as alerts_pending,
            -- Nicht-Alerts (tag != 'alert') Statistiken
            COUNT(*) FILTER (
                WHERE mp.tag != 'alert' AND mp.status = 'inaktiv' AND mp.evaluation_result = 'success'
            ) as non_alerts_success,
            COUNT(*) FILTER (
                WHERE mp.tag != 'alert' AND mp.status = 'inaktiv' AND mp.evaluation_result = 'failed'
            ) as non_alerts_failed,
            COUNT(*) FILTER (
                WHERE mp.tag != 'alert' AND mp.status = 'aktiv'
            ) as non_alerts_pending,
            -- Performance-Summen (actual_price_change_pct)
            COALESCE(SUM(mp.actual_price_change_pct) FILTER (
                WHERE mp.tag = 'alert' AND mp.status = 'inaktiv' 
                AND mp.evaluation_result IN ('success', 'failed')
                AND mp.actual_price_change_pct IS NOT NULL
            ), 0) as total_performance_pct,
            COALESCE(SUM(mp.actual_price_change_pct) FILTER (
                WHERE mp.tag = 'alert' AND mp.status = 'inaktiv' AND mp.evaluation_result = 'success'
                AND mp.actual_price_change_pct IS NOT NULL
            ), 0) as alerts_profit_pct,
            COALESCE(SUM(mp.actual_price_change_pct) FILTER (
                WHERE mp.tag = 'alert' AND mp.status = 'inaktiv' AND mp.evaluation_result = 'failed'
                AND mp.actual_price_change_pct IS NOT NULL
            ), 0) as alerts_loss_pct,
            -- Success Rates
            CASE 
                WHEN COUNT(*) FILTER (
                    WHERE mp.tag = 'alert' AND mp.status = 'inaktiv' 
                    AND mp.evaluation_result IN ('success', 'failed')
                ) > 0 
                THEN (COUNT(*) FILTER (
                    WHERE mp.tag = 'alert' AND mp.status = 'inaktiv' AND mp.evaluation_result = 'success'
                )::float / 
                COUNT(*) FILTER (
                    WHERE mp.tag = 'alert' AND mp.status = 'inaktiv' 
                    AND mp.evaluation_result IN ('success', 'failed')
                )::float * 100)
                ELSE 0
            END as alerts_success_rate,
            CASE 
                WHEN COUNT(*) FILTER (
                    WHERE mp.tag != 'alert' AND mp.status = 'inaktiv' 
                    AND mp.evaluation_result IN ('success', 'failed')
                ) > 0 
                THEN (COUNT(*) FILTER (
                    WHERE mp.tag != 'alert' AND mp.status = 'inaktiv' AND mp.evaluation_result = 'success'
                )::float / 
                COUNT(*) FILTER (
                    WHERE mp.tag != 'alert' AND mp.status = 'inaktiv' 
                    AND mp.evaluation_result IN ('success', 'failed')
                )::float * 100)
                ELSE 0
            END as non_alerts_success_rate,
            CASE 
                WHEN COUNT(*) FILTER (
                    WHERE mp.status = 'inaktiv' AND mp.evaluation_result IN ('success', 'failed')
                ) > 0 
                THEN (COUNT(*) FILTER (
                    WHERE mp.status = 'inaktiv' AND mp.evaluation_result = 'success'
                )::float / 
                COUNT(*) FILTER (
                    WHERE mp.status = 'inaktiv' AND mp.evaluation_result IN ('success', 'failed')
                )::float * 100)
                ELSE 0
            END as success_rate
        FROM model_predictions mp
        {where_clause}
        """
        stats_row = await pool.fetchrow(query, *params)
    else:
        stats_row = await pool.fetchrow(f"""
            SELECT
                COUNT(*) as total_alerts,
                COUNT(*) FILTER (WHERE mp.status = 'aktiv') as pending,
                COUNT(*) FILTER (WHERE mp.status = 'inaktiv' AND mp.evaluation_result = 'success') as success,
                COUNT(*) FILTER (WHERE mp.status = 'inaktiv' AND mp.evaluation_result = 'failed') as failed,
                COUNT(*) FILTER (WHERE mp.status = 'inaktiv' AND mp.evaluation_result = 'not_applicable') as expired,
                COUNT(*) FILTER (WHERE mp.tag = 'alert') as alerts_above_threshold,
                -- Alerts (tag = 'alert') Statistiken
                COUNT(*) FILTER (
                    WHERE mp.tag = 'alert' AND mp.status = 'inaktiv' AND mp.evaluation_result = 'success'
                ) as alerts_success,
                COUNT(*) FILTER (
                    WHERE mp.tag = 'alert' AND mp.status = 'inaktiv' AND mp.evaluation_result = 'failed'
                ) as alerts_failed,
                COUNT(*) FILTER (
                    WHERE mp.tag = 'alert' AND mp.status = 'aktiv'
                ) as alerts_pending,
                -- Nicht-Alerts (tag != 'alert') Statistiken
                COUNT(*) FILTER (
                    WHERE mp.tag != 'alert' AND mp.status = 'inaktiv' AND mp.evaluation_result = 'success'
                ) as non_alerts_success,
                COUNT(*) FILTER (
                    WHERE mp.tag != 'alert' AND mp.status = 'inaktiv' AND mp.evaluation_result = 'failed'
                ) as non_alerts_failed,
                COUNT(*) FILTER (
                    WHERE mp.tag != 'alert' AND mp.status = 'aktiv'
                ) as non_alerts_pending,
                -- Performance-Summen (actual_price_change_pct)
                COALESCE(SUM(mp.actual_price_change_pct) FILTER (
                    WHERE mp.tag = 'alert' AND mp.status = 'inaktiv' 
                    AND mp.evaluation_result IN ('success', 'failed')
                    AND mp.actual_price_change_pct IS NOT NULL
                ), 0) as total_performance_pct,
                COALESCE(SUM(mp.actual_price_change_pct) FILTER (
                    WHERE mp.tag = 'alert' AND mp.status = 'inaktiv' AND mp.evaluation_result = 'success'
                    AND mp.actual_price_change_pct IS NOT NULL
                ), 0) as alerts_profit_pct,
                COALESCE(SUM(mp.actual_price_change_pct) FILTER (
                    WHERE mp.tag = 'alert' AND mp.status = 'inaktiv' AND mp.evaluation_result = 'failed'
                    AND mp.actual_price_change_pct IS NOT NULL
                ), 0) as alerts_loss_pct,
                -- Success Rates
                CASE 
                    WHEN COUNT(*) FILTER (
                        WHERE mp.tag = 'alert' AND mp.status = 'inaktiv' 
                        AND mp.evaluation_result IN ('success', 'failed')
                    ) > 0 
                    THEN (COUNT(*) FILTER (
                        WHERE mp.tag = 'alert' AND mp.status = 'inaktiv' AND mp.evaluation_result = 'success'
                    )::float / 
                    COUNT(*) FILTER (
                        WHERE mp.tag = 'alert' AND mp.status = 'inaktiv' 
                        AND mp.evaluation_result IN ('success', 'failed')
                    )::float * 100)
                    ELSE 0
                END as alerts_success_rate,
                CASE 
                    WHEN COUNT(*) FILTER (
                        WHERE mp.tag != 'alert' AND mp.status = 'inaktiv' 
                        AND mp.evaluation_result IN ('success', 'failed')
                    ) > 0 
                    THEN (COUNT(*) FILTER (
                        WHERE mp.tag != 'alert' AND mp.status = 'inaktiv' AND mp.evaluation_result = 'success'
                    )::float / 
                    COUNT(*) FILTER (
                        WHERE mp.tag != 'alert' AND mp.status = 'inaktiv' 
                        AND mp.evaluation_result IN ('success', 'failed')
                    )::float * 100)
                    ELSE 0
                END as non_alerts_success_rate,
                CASE 
                    WHEN COUNT(*) FILTER (
                        WHERE mp.status = 'inaktiv' AND mp.evaluation_result IN ('success', 'failed')
                    ) > 0 
                    THEN (COUNT(*) FILTER (
                        WHERE mp.status = 'inaktiv' AND mp.evaluation_result = 'success'
                    )::float / 
                    COUNT(*) FILTER (
                        WHERE mp.status = 'inaktiv' AND mp.evaluation_result IN ('success', 'failed')
                    )::float * 100)
                    ELSE 0
                END as success_rate
            FROM model_predictions mp
            {where_clause}
            """)
    
    # Statistiken pro Modell (NEUE ARCHITEKTUR)
    if params:
        by_model_query = f"""
        SELECT 
            mp.active_model_id,
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE mp.status = 'inaktiv' AND mp.evaluation_result IN ('success', 'failed')) as success,
            COUNT(*) FILTER (WHERE mp.status = 'inaktiv' AND mp.evaluation_result = 'failed') as failed,
            COUNT(*) FILTER (WHERE mp.status = 'aktiv') as pending
        FROM model_predictions mp
        {where_clause}
        GROUP BY mp.active_model_id
        ORDER BY total DESC
        """
        by_model_rows = await pool.fetch(by_model_query, *params)
    else:
        by_model_rows = await pool.fetch(f"""
            SELECT
                mp.active_model_id,
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE mp.status = 'inaktiv' AND mp.evaluation_result IN ('success', 'failed')) as success,
                COUNT(*) FILTER (WHERE mp.status = 'inaktiv' AND mp.evaluation_result = 'failed') as failed,
                COUNT(*) FILTER (WHERE mp.status = 'aktiv') as pending
            FROM model_predictions mp
            {where_clause}
            GROUP BY mp.active_model_id
            ORDER BY total DESC
        """)
    
    by_model = []
    for row in by_model_rows:
        if not row['active_model_id']:
            continue
        model_row = await pool.fetchrow("""
            SELECT model_id, model_name, custom_name
            FROM prediction_active_models
            WHERE id = $1
            LIMIT 1
        """, row['active_model_id'])
        
        model_id = model_row['model_id'] if model_row else None
        model_name = model_row.get('custom_name') or model_row.get('model_name', f"ID: {model_id}") if model_row else f"ID: {row['active_model_id']}"
        
        total_evaluated = row['success'] + row['failed']
        success_rate = (row['success'] / total_evaluated * 100) if total_evaluated > 0 else 0
        
        by_model.append({
            'model_id': model_id or row['active_model_id'],
            'model_name': model_name,
            'total': row['total'],
            'success': row['success'],
            'failed': row['failed'],
            'pending': row['pending'],
            'success_rate': success_rate
        })
    
    # Berechne Nicht-Alerts (aus Query-Ergebnissen)
    total_alerts = stats_row['total_alerts'] if stats_row else 0
    alerts_above_threshold = stats_row['alerts_above_threshold'] if stats_row else 0
    # non_alerts_count = success + failed + pending (nicht-alerts)
    non_alerts_count = (stats_row['non_alerts_success'] if stats_row else 0) + \
                       (stats_row['non_alerts_failed'] if stats_row else 0) + \
                       (stats_row['non_alerts_pending'] if stats_row else 0)
    
    return {
        'total_alerts': total_alerts,
        'pending': stats_row['pending'] if stats_row else 0,
        'success': stats_row['success'] if stats_row else 0,
        'failed': stats_row['failed'] if stats_row else 0,
        'expired': stats_row['expired'] if stats_row else 0,
        'alerts_above_threshold': alerts_above_threshold,
        'non_alerts_count': non_alerts_count,
        # Alerts (>= threshold) Statistiken
        'alerts_success': stats_row['alerts_success'] if stats_row else 0,
        'alerts_failed': stats_row['alerts_failed'] if stats_row else 0,
        'alerts_pending': stats_row['alerts_pending'] if stats_row else 0,
        # Nicht-Alerts (< threshold) Statistiken
        'non_alerts_success': stats_row['non_alerts_success'] if stats_row else 0,
        'non_alerts_failed': stats_row['non_alerts_failed'] if stats_row else 0,
        'non_alerts_pending': stats_row['non_alerts_pending'] if stats_row else 0,
        # Success Rates
        'alerts_success_rate': float(stats_row['alerts_success_rate']) if stats_row and stats_row.get('alerts_success_rate') is not None else 0,
        'non_alerts_success_rate': float(stats_row['non_alerts_success_rate']) if stats_row and stats_row.get('non_alerts_success_rate') is not None else 0,
        'success_rate': float(stats_row['success_rate']) if stats_row and stats_row['success_rate'] else 0,
        # Performance-Summen (in Prozent)
        'total_performance_pct': float(stats_row['total_performance_pct']) if stats_row and stats_row.get('total_performance_pct') is not None else 0,
        'alerts_profit_pct': float(stats_row['alerts_profit_pct']) if stats_row and stats_row.get('alerts_profit_pct') is not None else 0,
        'alerts_loss_pct': float(stats_row['alerts_loss_pct']) if stats_row and stats_row.get('alerts_loss_pct') is not None else 0,
        'by_model': by_model
    }

async def get_model_alert_statistics(active_model_ids: Optional[List[int]] = None) -> Dict[str, Any]:
    """
    OPTIMIERT: Holt Alert-Statistiken für mehrere aktive Modelle in einem Batch-Query.
    
    Args:
        active_model_ids: Liste von active_model_ids (optional, wenn None: alle aktiven)
        
    Returns:
        Dict mit active_model_id (als String für JSON-Kompatibilität) als Key und Dict mit Statistiken als Value
    """
    pool = await get_pool()
    
    # Wenn keine IDs gegeben, hole alle aktiven Modelle
    if active_model_ids is None:
        model_rows = await pool.fetch("""
            SELECT id, model_id FROM prediction_active_models WHERE is_active = true
        """)
        active_model_ids = [row['id'] for row in model_rows]
        model_id_map = {row['id']: row['model_id'] for row in model_rows}
    else:
        # Hole model_id für gegebene active_model_ids
        model_rows = await pool.fetch("""
            SELECT id, model_id FROM prediction_active_models WHERE id = ANY($1::bigint[])
        """, active_model_ids)
        model_id_map = {row['id']: row['model_id'] for row in model_rows}
    
    if not active_model_ids:
        return {}
    
    # NEUE ARCHITEKTUR: Verwende model_predictions Tabelle
    predictions_stats = await pool.fetch("""
        SELECT 
            active_model_id,
            COUNT(*) as total_predictions,
            COUNT(*) FILTER (WHERE prediction = 1) as positive_predictions,
            COUNT(*) FILTER (WHERE prediction = 0) as negative_predictions,
            COUNT(*) FILTER (WHERE tag = 'alert') as alerts_total,
            COUNT(*) FILTER (WHERE tag = 'alert' AND status = 'inaktiv' AND evaluation_result = 'success') as alerts_success,
            COUNT(*) FILTER (WHERE tag = 'alert' AND status = 'inaktiv' AND evaluation_result = 'failed') as alerts_failed,
            COUNT(*) FILTER (WHERE tag = 'alert' AND status = 'aktiv') as alerts_pending,
            COUNT(*) FILTER (WHERE tag = 'alert' AND status = 'inaktiv' AND evaluation_result = 'not_applicable') as alerts_expired
        FROM model_predictions
        WHERE active_model_id = ANY($1::bigint[])
        GROUP BY active_model_id
    """, active_model_ids)
    
    # Erstelle Mapping: active_model_id -> stats
    predictions_dict = {
        row['active_model_id']: {
            'total': row['total_predictions'],
            'positive': row['positive_predictions'],
            'negative': row['negative_predictions'],
            'alerts_total': row['alerts_total'],
            'alerts_success': row['alerts_success'],
            'alerts_failed': row['alerts_failed'],
            'alerts_pending': row['alerts_pending'],
            'alerts_expired': row['alerts_expired']
        }
        for row in predictions_stats
    }
    
    # Kombiniere Daten pro active_model_id
    # WICHTIG: Keys als Strings für JSON-Kompatibilität
    result = {}
    for active_model_id in active_model_ids:
        stats = predictions_dict.get(active_model_id, {
            'total': 0, 'positive': 0, 'negative': 0,
            'alerts_total': 0, 'alerts_success': 0, 'alerts_failed': 0,
            'alerts_pending': 0, 'alerts_expired': 0
        })
        
        result[str(active_model_id)] = {
            'total_predictions': stats['total'],
            'positive_predictions': stats['positive'],
            'negative_predictions': stats['negative'],
            'alerts_total': stats['alerts_total'],
            'alerts_success': stats['alerts_success'],
            'alerts_failed': stats['alerts_failed'],
            'alerts_pending': stats['alerts_pending'],
            'alerts_expired': stats['alerts_expired']
        }
    
    return result


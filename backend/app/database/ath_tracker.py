"""
ATH-Tracker für kontinuierliche Preis-Überwachung während Evaluierungszeit
Prüft alle 30 Sekunden, ob das Ziel erreicht wurde und trackt den ATH
"""
from typing import Dict, Optional, Any
from datetime import datetime, timezone, timedelta
import asyncpg
from app.database.connection import get_pool
from app.database.models import get_coin_metrics_at_timestamp
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


async def check_and_update_ath(alert_id: int, pool: Optional[asyncpg.Pool] = None) -> Optional[Dict[str, Any]]:
    """
    Prüft ob das Ziel erreicht wurde und aktualisiert den ATH-Wert.
    Wird alle 30 Sekunden aufgerufen für pending/non_alert Einträge.
    
    WICHTIG: Setzt Status NICHT auf success - das passiert erst nach evaluation_timestamp!
    Nur ATH wird aktualisiert.
    
    Args:
        alert_id: ID des Alert-Evaluations-Eintrags
        pool: Optional: DB-Pool
        
    Returns:
        Dict mit ath_price_change_pct, ath_timestamp, goal_reached (bool) oder None
    """
    if pool is None:
        pool = await get_pool()
    
    # Hole Alert-Daten
    alert = await pool.fetchrow("""
        SELECT 
            ae.*, 
            COALESCE(ae.probability, p.probability) as probability
        FROM alert_evaluations ae
        LEFT JOIN predictions p ON p.id = ae.prediction_id
        WHERE ae.id = $1
    """, alert_id)
    
    if not alert:
        logger.warning(f"⚠️ Alert {alert_id} nicht gefunden")
        return None
    
    # Nur für pending/non_alert und time_based
    if alert['status'] not in ('pending', 'non_alert'):
        return None  # Bereits evaluiert
    
    if alert['prediction_type'] != 'time_based':
        return None  # Nur für zeitbasierte Vorhersagen
    
    # Prüfe ob evaluation_timestamp bereits erreicht wurde
    eval_timestamp = alert.get('evaluation_timestamp')
    if not eval_timestamp:
        return None
    
    now = datetime.now(timezone.utc)
    
    # Wenn evaluation_timestamp noch nicht erreicht, hole aktuelle Metriken
    # Wenn evaluation_timestamp erreicht, hole Metriken zum evaluation_timestamp
    check_timestamp = min(now, eval_timestamp)
    
    try:
        # Hole aktuelle Metriken
        current_metrics = await get_coin_metrics_at_timestamp(
            alert['coin_id'],
            check_timestamp,
            pool
        )
        
        if not current_metrics or current_metrics.get('price_close') is None:
            return None  # Keine Metriken verfügbar
        
        # Berechne Preisänderung seit Alert
        price_at_alert = float(alert['price_close_at_alert'])
        price_now = float(current_metrics['price_close'])
        current_change_pct = ((price_now - price_at_alert) / price_at_alert) * 100
        
        # Hole aktuellen ATH
        current_ath = alert.get('ath_price_change_pct')
        if current_ath is None:
            current_ath = current_change_pct
            current_ath_timestamp = check_timestamp
            current_ath_price = price_now
        else:
            current_ath = float(current_ath)
            # Prüfe ob neuer ATH erreicht wurde
            if current_change_pct > current_ath:
                current_ath = current_change_pct
                current_ath_timestamp = check_timestamp
                current_ath_price = price_now
            else:
                # ATH bleibt gleich, hole Timestamp und Preis aus DB
                current_ath_timestamp = alert.get('ath_timestamp') or alert['alert_timestamp']
                current_ath_price = alert.get('ath_price_close') or price_at_alert
        
        # Prüfe ob Ziel erreicht wurde
        target_change = float(alert['price_change_percent']) if alert['price_change_percent'] else 0
        target_direction = alert['target_direction']
        
        goal_reached = False
        if target_direction == 'up':
            goal_reached = current_ath >= target_change
        else:  # 'down'
            goal_reached = current_ath <= -target_change
        
        # Update ATH in Datenbank (NUR ATH, NICHT Status!)
        await pool.execute("""
            UPDATE alert_evaluations
            SET ath_price_change_pct = $1,
                ath_timestamp = $2,
                ath_price_close = $3,
                updated_at = NOW()
            WHERE id = $4
        """, current_ath, current_ath_timestamp, current_ath_price, alert_id)
        
        return {
            'ath_price_change_pct': current_ath,
            'ath_timestamp': current_ath_timestamp,
            'ath_price_close': current_ath_price,
            'current_change_pct': current_change_pct,
            'goal_reached': goal_reached
        }
        
    except Exception as e:
        logger.error(f"❌ Fehler beim ATH-Check für Alert {alert_id}: {e}", exc_info=True)
        return None


async def evaluate_pending_alerts_ath(batch_size: int = 100) -> Dict[str, int]:
    """
    Prüft alle pending/non_alert Alerts und aktualisiert ATH-Werte.
    Wird alle 30 Sekunden aufgerufen.
    
    Returns:
        Dict mit Statistiken
    """
    pool = await get_pool()
    stats = {'checked': 0, 'ath_updated': 0, 'goal_reached': 0}
    
    # Hole alle pending/non_alert time_based Alerts, deren evaluation_timestamp noch nicht erreicht wurde
    alerts = await pool.fetch("""
        SELECT id, coin_id, alert_timestamp, evaluation_timestamp
        FROM alert_evaluations
        WHERE status IN ('pending', 'non_alert')
          AND prediction_type = 'time_based'
          AND evaluation_timestamp > NOW()  -- Noch nicht erreicht
        ORDER BY alert_timestamp ASC
        LIMIT $1
    """, batch_size)
    
    for alert in alerts:
        try:
            result = await check_and_update_ath(alert['id'], pool)
            if result:
                stats['checked'] += 1
                if result.get('ath_price_change_pct') is not None:
                    stats['ath_updated'] += 1
                if result.get('goal_reached'):
                    stats['goal_reached'] += 1
        except Exception as e:
            logger.error(f"❌ Fehler beim ATH-Check für Alert {alert['id']}: {e}", exc_info=True)
    
    return stats

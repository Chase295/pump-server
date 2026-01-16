"""
ATH-Tracker für model_predictions
Prüft alle 1 Minute die Coin-Metriken und aktualisiert ATH Highest/Lowest
"""
from typing import Dict, Optional, Any, List
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import asyncpg
from app.database.connection import get_pool
from app.database.models import get_coin_metrics_at_timestamp
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


async def update_ath_for_active_predictions(batch_size: int = 100) -> Dict[str, int]:
    """
    Prüft alle 'aktiv' Einträge und aktualisiert ATH Highest/Lowest.
    Wird alle 30 Sekunden aufgerufen.
    
    WICHTIG: Prüft ALLE Preise zwischen prediction_timestamp und evaluation_timestamp
    aus coin_metrics, um den höchsten/niedrigsten Wert zu finden.
    
    Args:
        batch_size: Anzahl der Einträge pro Batch
        
    Returns:
        Dict mit Statistiken (checked, updated_highest, updated_lowest)
    """
    pool = await get_pool()
    
    # Hole alle aktiven Einträge, die noch nicht ausgewertet wurden
    rows = await pool.fetch("""
        SELECT 
            mp.id,
            mp.coin_id,
            mp.prediction_timestamp,
            mp.evaluation_timestamp,
            mp.price_close_at_prediction,
            mp.ath_highest_pct,
            mp.ath_lowest_pct,
            mp.ath_highest_timestamp,
            mp.ath_lowest_timestamp
        FROM model_predictions mp
        WHERE mp.status = 'aktiv'
          AND mp.evaluation_timestamp > NOW()  -- Noch nicht auswertbar
        ORDER BY 
            CASE WHEN mp.ath_highest_pct IS NULL THEN 0 ELSE 1 END ASC,  -- Neue Einträge zuerst (ohne ATH)
            mp.prediction_timestamp DESC  -- Neueste zuerst
        LIMIT $1
    """, batch_size)
    
    stats = {
        'checked': 0,
        'updated_highest': 0,
        'updated_lowest': 0,
        'errors': 0
    }
    
    now = datetime.now(timezone.utc)
    
    for row in rows:
        try:
            prediction_id = row['id']
            coin_id = row['coin_id']
            prediction_timestamp = row['prediction_timestamp']
            evaluation_timestamp = row['evaluation_timestamp']
            
            # Prüfe nur bis zum evaluation_timestamp
            check_timestamp = min(now, evaluation_timestamp)
            
            # WICHTIG: Hole ALLE Preise zwischen prediction_timestamp und check_timestamp
            # aus coin_metrics, um den höchsten/niedrigsten Wert zu finden
            price_history = await pool.fetch("""
                SELECT 
                    timestamp,
                    price_close
                FROM coin_metrics
                WHERE mint = $1
                  AND timestamp >= $2
                  AND timestamp <= $3
                ORDER BY timestamp ASC
            """, coin_id, prediction_timestamp, check_timestamp)
            
            if not price_history:
                # Fallback: Hole nur den aktuellen Preis
                current_metrics = await get_coin_metrics_at_timestamp(
                    coin_id,
                    check_timestamp,
                    pool=pool
                )
                
                if not current_metrics or current_metrics.get('price_close') is None:
                    stats['checked'] += 1
                    continue
                
                price_history = [{
                    'timestamp': check_timestamp,
                    'price_close': current_metrics.get('price_close')
                }]
            
            # Hole Startpreis (price_close_at_prediction)
            price_close_at_prediction_raw = row['price_close_at_prediction']
            
            if price_close_at_prediction_raw is None:
                stats['checked'] += 1
                continue
            
            # Konvertiere zu float
            if isinstance(price_close_at_prediction_raw, Decimal):
                price_close_at_prediction = float(price_close_at_prediction_raw)
            else:
                price_close_at_prediction = float(price_close_at_prediction_raw)
            
            # Prüfe ALLE Preise in der Historie, um ATH Highest/Lowest zu finden
            current_ath_highest = float(row['ath_highest_pct']) if row['ath_highest_pct'] is not None else None
            current_ath_lowest = float(row['ath_lowest_pct']) if row['ath_lowest_pct'] is not None else None
            new_ath_highest = current_ath_highest
            new_ath_lowest = current_ath_lowest
            new_ath_highest_timestamp = row['ath_highest_timestamp']
            new_ath_lowest_timestamp = row['ath_lowest_timestamp']
            updated_highest = False
            updated_lowest = False
            
            for price_entry in price_history:
                price_close_raw = price_entry['price_close']
                price_timestamp = price_entry['timestamp']
                
                if price_close_raw is None:
                    continue
                
                # Konvertiere zu float
                if isinstance(price_close_raw, Decimal):
                    price_close = float(price_close_raw)
                else:
                    price_close = float(price_close_raw)
                
                # Berechne Preisänderung
                change_pct = ((price_close - price_close_at_prediction) / price_close_at_prediction) * 100
                
                # ATH Highest: Nur POSITIVE Werte (höchster positiver Wert)
                if change_pct > 0:
                    if new_ath_highest is None or change_pct > new_ath_highest:
                        new_ath_highest = change_pct
                        new_ath_highest_timestamp = price_timestamp
                        updated_highest = True
                
                # ATH Lowest: Nur NEGATIVE Werte (niedrigster negativer Wert)
                if change_pct < 0:
                    if new_ath_lowest is None or change_pct < new_ath_lowest:
                        new_ath_lowest = change_pct
                        new_ath_lowest_timestamp = price_timestamp
                        updated_lowest = True
            
            # Update nur wenn sich etwas geändert hat
            if updated_highest or updated_lowest:
                highest_str = f"{new_ath_highest:.2f}%" if new_ath_highest is not None else "None"
                lowest_str = f"{new_ath_lowest:.2f}%" if new_ath_lowest is not None else "None"
                logger.debug(f"📈 Update ATH für Prediction {prediction_id}: Highest={highest_str}, Lowest={lowest_str}")
                await pool.execute("""
                    UPDATE model_predictions
                    SET ath_highest_pct = $1,
                        ath_lowest_pct = $2,
                        ath_highest_timestamp = $3,
                        ath_lowest_timestamp = $4,
                        updated_at = NOW()
                    WHERE id = $5
                """,
                    new_ath_highest,
                    new_ath_lowest,
                    new_ath_highest_timestamp,
                    new_ath_lowest_timestamp,
                    prediction_id
                )
                logger.debug(f"✅ ATH für Prediction {prediction_id} aktualisiert")
                
                if updated_highest:
                    stats['updated_highest'] += 1
                if updated_lowest:
                    stats['updated_lowest'] += 1
            
            stats['checked'] += 1
            
        except Exception as e:
            logger.error(f"❌ Fehler beim ATH-Update für Prediction {row.get('id')}: {e}", exc_info=True)
            stats['errors'] += 1
    
    return stats

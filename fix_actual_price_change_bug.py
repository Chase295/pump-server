#!/usr/bin/env python3
"""
Korrigiert actual_price_change_pct in model_predictions für Alerts.

Das Problem: model_predictions mit tag='alert' haben falsche actual_price_change_pct Werte,
die von prediction_timestamp berechnet wurden. Für Alerts sollte es von alert_timestamp sein.
"""
import asyncio
from app.database.connection import get_pool

async def fix_alert_actual_price_change():
    pool = await get_pool()
    
    # Finde alle model_predictions mit tag='alert', die einen entsprechenden alert_evaluation haben
    # und aktualisiere deren actual_price_change_pct mit dem korrekten Wert aus alert_evaluations
    rows = await pool.fetch("""
        SELECT 
            mp.id as mp_id,
            mp.actual_price_change_pct as mp_change,
            ae.id as ae_id,
            ae.actual_price_change_pct as ae_change
        FROM model_predictions mp
        JOIN alert_evaluations ae ON ae.prediction_id = mp.prediction
        WHERE mp.tag = 'alert'
          AND ae.actual_price_change_pct IS NOT NULL
    """)
    
    print(f"Gefunden: {len(rows)} model_predictions mit tag='alert' die korrigiert werden müssen")
    
    fixed = 0
    for row in rows:
        mp_id = row['mp_id']
        mp_change = float(row['mp_change'])
        ae_change = float(row['ae_change'])
            
        if abs(mp_change - ae_change) > 0.01:  # Nur aktualisieren wenn sich der Wert unterscheidet
                await pool.execute("""
                    UPDATE model_predictions
                    SET actual_price_change_pct = $1,
                        updated_at = NOW()
                    WHERE id = $2
            """, ae_change, mp_id)
                
            print(f"  Korrigiert MP {mp_id}: {mp_change:.2f}% -> {ae_change:.2f}%")
                fixed += 1
        
    print(f"\n✅ Fertig: {fixed} model_predictions korrigiert")
    
async def main():
    await fix_alert_actual_price_change()

if __name__ == "__main__":
    asyncio.run(main())
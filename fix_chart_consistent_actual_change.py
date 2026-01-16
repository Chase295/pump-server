#!/usr/bin/env python3
"""
Korrigiert actual_price_change_pct in model_predictions für Chart-Konsistenz.

Das Problem: actual_price_change_pct wurde absolut berechnet, aber sollte
die Differenz der Chart-Prozente sein (relativ zum ersten Preis der Historie).
"""
import asyncio
from app.database.connection import get_pool

async def fix_actual_price_change_consistency():
    pool = await get_pool()

    # Finde ALLE Predictions mit gespeicherten actual_price_change_pct Werten
    predictions = await pool.fetch('''
        SELECT mp.id, mp.coin_id, mp.actual_price_change_pct,
               mp.prediction_timestamp, mp.evaluation_timestamp
        FROM model_predictions mp
        WHERE mp.actual_price_change_pct IS NOT NULL
        ORDER BY mp.created_at DESC
    ''')

    print(f'=== KORRIGIERE ACTUAL_PRICE_CHANGE_PCT FÜR {len(predictions)} PREDICTIONS ===\\n')

    corrected_count = 0
    for pred in predictions:
        pred_id = pred['id']
        coin_id = pred['coin_id']
        current_value = float(pred['actual_price_change_pct'])

        # Hole den ersten Preis der Historie (Chart-Basis)
        first_price_row = await pool.fetchrow("""
            SELECT price_close FROM coin_metrics
            WHERE mint = $1
            ORDER BY timestamp ASC LIMIT 1
        """, coin_id)

        if not first_price_row:
            print(f'⚠️ Prediction {pred_id}: Keine Basis-Preis-Daten gefunden')
            continue

        base_price = float(first_price_row['price_close'])

        # Hole Preise am Prediction- und Evaluation-Zeitpunkt
        pred_price_row = await pool.fetchrow("""
            SELECT price_close FROM coin_metrics
            WHERE mint = $1 AND timestamp <= $2
            ORDER BY timestamp DESC LIMIT 1
        """, coin_id, pred['prediction_timestamp'])

        eval_price_row = await pool.fetchrow("""
            SELECT price_close FROM coin_metrics
            WHERE mint = $1 AND timestamp >= $2
            ORDER BY timestamp ASC LIMIT 1
        """, coin_id, pred['evaluation_timestamp'])

        if not pred_price_row or not eval_price_row:
            print(f'⚠️ Prediction {pred_id}: Keine Preis-Daten für Prediction/Evaluation gefunden')
            continue

        pred_price = float(pred_price_row['price_close'])
        eval_price = float(eval_price_row['price_close'])

        # Berechne Chart-Prozente
        pred_pct = ((pred_price - base_price) / base_price) * 100
        eval_pct = ((eval_price - base_price) / base_price) * 100

        # Korrekte "Tatsächliche Änderung" = Differenz der Chart-Prozente
        correct_value = eval_pct - pred_pct

        if abs(correct_value - current_value) > 0.01:
            # Aktualisiere den Wert in der Datenbank
            await pool.execute("""
                UPDATE model_predictions
                SET actual_price_change_pct = $1, updated_at = NOW()
                WHERE id = $2
            """, correct_value, pred_id)

            print(f'✅ Prediction {pred_id}: {current_value:.2f}% → {correct_value:.2f}% (korrigiert)')
            corrected_count += 1
        else:
            print(f'✅ Prediction {pred_id}: {current_value:.2f}% (bereits korrekt)')

    print(f'\\n=== ZUSAMMENFASSUNG ===')
    print(f'Korrigierte Predictions: {corrected_count}')
    print(f'Unveränderte Predictions: {len(predictions) - corrected_count}')

if __name__ == "__main__":
    asyncio.run(fix_actual_price_change_consistency())
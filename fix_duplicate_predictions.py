#!/usr/bin/env python3
"""
Entfernt Duplikate aus model_predictions.

Behält nur den neuesten Eintrag pro coin_id + active_model_id + tag Kombination.
"""

import asyncio
from app.database.connection import get_pool

async def cleanup_duplicates():
    """Entfernt Duplikate und behält nur den neuesten Eintrag pro Gruppe"""
    pool = await get_pool()

    # Finde alle Duplikate
    duplicates = await pool.fetch("""
        SELECT coin_id, active_model_id, tag, COUNT(*) as count,
               array_agg(id ORDER BY created_at DESC) as ids_ordered_by_newest
        FROM model_predictions
        GROUP BY coin_id, active_model_id, tag
        HAVING COUNT(*) > 1
        ORDER BY count DESC
    """)

    print(f"Gefunden: {len(duplicates)} Duplikat-Gruppen")

    total_deleted = 0

    for dup in duplicates:
        coin_id = dup['coin_id']
        active_model_id = dup['active_model_id']
        tag = dup['tag']
        count = dup['count']
        ids_ordered = dup['ids_ordered_by_newest']  # Neueste zuerst

        # Behalte nur die neueste ID, lösche alle anderen
        keep_id = ids_ordered[0]
        delete_ids = ids_ordered[1:]

        if delete_ids:
            # Lösche die alten Duplikate
            deleted = await pool.fetch("""
                DELETE FROM model_predictions
                WHERE id = ANY($1)
                RETURNING id
            """, delete_ids)

            deleted_count = len(deleted)
            total_deleted += deleted_count

            print(f"  Gelöscht: {deleted_count} alte Einträge für Coin {coin_id[:8]}... ({tag}) - behalten: ID {keep_id}")

    print(f"\n✅ Fertig: {total_deleted} Duplikat-Einträge entfernt aus {len(duplicates)} Gruppen")

if __name__ == "__main__":
    asyncio.run(cleanup_duplicates())
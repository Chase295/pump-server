"""
MCP Tools for Alert Management

Provides tools for viewing and managing alerts and alert statistics.
All tools delegate to existing service functions to avoid code duplication.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.database.alert_models import (
    get_alerts as db_get_alerts,
    get_alert_details as db_get_alert_details,
    get_alert_statistics as db_get_alert_statistics,
    get_model_alert_statistics as db_get_model_alert_statistics,
)
from app.database.connection import get_pool

logger = logging.getLogger(__name__)


async def get_alerts(
    status: Optional[str] = None,
    model_id: Optional[int] = None,
    coin_id: Optional[str] = None,
    prediction_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    unique_coins: bool = True,
    include_non_alerts: bool = False,
    limit: int = 100,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Holt Alerts mit optionalen Filtern.

    Args:
        status: Filter nach Status ('pending', 'success', 'failed', 'expired')
        model_id: Filter nach active_model_id
        coin_id: Filter nach Coin-ID
        prediction_type: Filter nach Typ ('time_based', 'classic')
        date_from: Filter ab Datum (ISO-Format)
        date_to: Filter bis Datum (ISO-Format)
        unique_coins: Nur ältester Alert pro Coin (default: True)
        include_non_alerts: Auch Predictions unter Alert-Threshold zeigen (default: False)
        limit: Max. Anzahl Ergebnisse (default: 100)
        offset: Offset für Pagination (default: 0)

    Returns:
        Dict mit Liste von Alerts
    """
    try:
        # Parse date strings to datetime if provided
        parsed_date_from = datetime.fromisoformat(date_from) if date_from else None
        parsed_date_to = datetime.fromisoformat(date_to) if date_to else None

        result = await db_get_alerts(
            status=status,
            model_id=model_id,
            coin_id=coin_id,
            prediction_type=prediction_type,
            date_from=parsed_date_from,
            date_to=parsed_date_to,
            unique_coins=unique_coins,
            include_non_alerts=include_non_alerts,
            limit=limit,
            offset=offset
        )

        # Serialize datetime objects in alerts
        alerts = result.get("alerts", [])
        for alert in alerts:
            for key in list(alert.keys()):
                if isinstance(alert[key], datetime):
                    alert[key] = str(alert[key])

        return {
            "success": True,
            "alerts": alerts,
            "total": result.get("total", 0),
            "count": len(alerts),
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        return {
            "success": False,
            "error": str(e),
            "alerts": [],
            "total": 0
        }


async def get_alert_details(
    alert_id: int,
    chart_before_minutes: int = 10,
    chart_after_minutes: int = 10
) -> Dict[str, Any]:
    """
    Holt detaillierte Informationen zu einem bestimmten Alert.

    Args:
        alert_id: ID des Alerts
        chart_before_minutes: Minuten vor Alert für Chart-Daten (default: 10)
        chart_after_minutes: Minuten nach Evaluation für Chart-Daten (default: 10)

    Returns:
        Dict mit Alert-Details
    """
    try:
        result = await db_get_alert_details(
            alert_id=alert_id,
            chart_before_minutes=chart_before_minutes,
            chart_after_minutes=chart_after_minutes
        )

        if not result:
            return {
                "success": False,
                "error": f"Alert with ID {alert_id} not found",
            }

        return {
            "success": True,
            "alert": result,
        }
    except Exception as e:
        logger.error(f"Error getting alert details for {alert_id}: {e}")
        return {
            "success": False,
            "error": str(e),
        }


async def get_alert_statistics(
    model_id: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
) -> Dict[str, Any]:
    """
    Holt Alert-Statistiken, optional gefiltert nach Modell und Zeitraum.

    Args:
        model_id: Filter nach active_model_id (optional)
        date_from: Filter ab Datum (ISO-Format, optional)
        date_to: Filter bis Datum (ISO-Format, optional)

    Returns:
        Dict mit Alert-Statistiken
    """
    try:
        parsed_date_from = datetime.fromisoformat(date_from) if date_from else None
        parsed_date_to = datetime.fromisoformat(date_to) if date_to else None

        result = await db_get_alert_statistics(
            model_id=model_id,
            date_from=parsed_date_from,
            date_to=parsed_date_to
        )

        return {
            "success": True,
            "statistics": result,
        }
    except Exception as e:
        logger.error(f"Error getting alert statistics: {e}")
        return {
            "success": False,
            "error": str(e),
            "statistics": None
        }


async def get_all_models_alert_statistics(
    active_model_ids: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    Holt Alert-Statistiken für alle oder ausgewählte aktive Modelle (Batch-Abfrage).

    Args:
        active_model_ids: Liste von active_model_ids (optional, wenn None: alle aktiven Modelle)

    Returns:
        Dict mit Statistiken pro Modell
    """
    try:
        result = await db_get_model_alert_statistics(
            active_model_ids=active_model_ids
        )

        return {
            "success": True,
            "model_statistics": result,
        }
    except Exception as e:
        logger.error(f"Error getting model alert statistics: {e}")
        return {
            "success": False,
            "error": str(e),
            "model_statistics": None
        }


async def delete_model_alerts(active_model_id: int) -> Dict[str, Any]:
    """
    Löscht alle Alert-Evaluierungen für ein Modell.

    Args:
        active_model_id: ID des aktiven Modells

    Returns:
        Dict mit Ergebnis der Löschung
    """
    try:
        pool = await get_pool()

        # Check if model exists
        model = await pool.fetchrow(
            "SELECT id FROM prediction_active_models WHERE id = $1",
            active_model_id
        )
        if not model:
            return {
                "success": False,
                "error": f"Model with ID {active_model_id} not found",
            }

        # Delete alert evaluations
        result = await pool.execute("""
            DELETE FROM alert_evaluations
            WHERE prediction_id IN (
                SELECT id FROM predictions WHERE active_model_id = $1
            )
        """, active_model_id)

        deleted_count = int(result.split(" ")[-1]) if result else 0

        return {
            "success": True,
            "message": f"Deleted {deleted_count} alert evaluations for model {active_model_id}",
            "active_model_id": active_model_id,
            "deleted_alerts": deleted_count,
        }
    except Exception as e:
        logger.error(f"Error deleting alerts for model {active_model_id}: {e}")
        return {
            "success": False,
            "error": str(e),
        }

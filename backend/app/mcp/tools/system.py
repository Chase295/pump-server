"""
MCP Tools for System/Health

Provides tools for health checks and service statistics.
"""
import logging
import time
from datetime import datetime
from typing import Any, Dict

from app.database.connection import get_pool
from app.database.models import get_active_models

logger = logging.getLogger(__name__)

# Store startup time for uptime calculation
_startup_time = time.time()


async def health_check() -> Dict[str, Any]:
    """
    Führt einen Health-Check des Services durch.

    Returns:
        Dict mit Health-Status
    """
    try:
        pool = await get_pool()

        # DB-Verbindung prüfen
        db_connected = False
        db_latency_ms = None
        try:
            start = time.time()
            await pool.fetchval("SELECT 1")
            db_latency_ms = round((time.time() - start) * 1000, 2)
            db_connected = True
        except Exception as e:
            logger.warning(f"DB health check failed: {e}")

        # Aktive Modelle zählen
        active_models_count = 0
        try:
            models = await get_active_models(include_inactive=False)
            active_models_count = len(models)
        except Exception:
            pass

        # Predictions in letzter Stunde
        predictions_last_hour = 0
        try:
            row = await pool.fetchrow("""
                SELECT COUNT(*) as count
                FROM predictions
                WHERE created_at > NOW() - INTERVAL '1 hour'
            """)
            predictions_last_hour = row['count'] if row else 0
        except Exception:
            pass

        # Uptime berechnen
        uptime_seconds = int(time.time() - _startup_time)

        # Status bestimmen
        status = "healthy" if db_connected else "degraded"

        return {
            "success": True,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "database": {
                    "connected": db_connected,
                    "latency_ms": db_latency_ms,
                },
                "models": {
                    "active_count": active_models_count,
                },
                "predictions": {
                    "last_hour": predictions_last_hour,
                },
            },
            "uptime_seconds": uptime_seconds,
            "uptime_human": _format_uptime(uptime_seconds),
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e),
        }


async def get_stats() -> Dict[str, Any]:
    """
    Holt umfassende Service-Statistiken.

    Returns:
        Dict mit Service-Statistiken
    """
    try:
        pool = await get_pool()

        # Predictions-Statistiken
        predictions_stats = await pool.fetchrow("""
            SELECT
                COUNT(*) as total_predictions,
                COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '1 hour') as predictions_1h,
                COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') as predictions_24h,
                COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '7 days') as predictions_7d,
                COUNT(*) FILTER (WHERE prediction = 1) as positive_predictions,
                COUNT(*) FILTER (WHERE prediction = 0) as negative_predictions,
                AVG(probability) as avg_probability,
                AVG(prediction_duration_ms) as avg_duration_ms,
                COUNT(DISTINCT coin_id) as unique_coins
            FROM predictions
        """)

        # Modell-Statistiken
        model_stats = await pool.fetchrow("""
            SELECT
                COUNT(*) as total_models,
                COUNT(*) FILTER (WHERE is_active = true) as active_models,
                COUNT(*) FILTER (WHERE is_active = false) as inactive_models
            FROM prediction_active_models
        """)

        # Webhook-Statistiken
        webhook_stats = await pool.fetchrow("""
            SELECT
                COUNT(*) as total_webhooks,
                COUNT(*) FILTER (WHERE response_status >= 200 AND response_status < 300) as successful_webhooks,
                COUNT(*) FILTER (WHERE response_status IS NULL OR response_status < 200 OR response_status >= 300) as failed_webhooks
            FROM prediction_webhook_log
            WHERE sent_at > NOW() - INTERVAL '24 hours'
        """)

        # Alert-Statistiken (positive predictions mit hoher Wahrscheinlichkeit)
        alerts_stats = await pool.fetchrow("""
            SELECT
                COUNT(*) as total_alerts,
                COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') as alerts_24h
            FROM predictions
            WHERE prediction = 1 AND probability >= 0.7
        """)

        # Formatiere Ergebnisse
        total_preds = predictions_stats['total_predictions'] if predictions_stats else 0
        positive = predictions_stats['positive_predictions'] if predictions_stats else 0
        negative = predictions_stats['negative_predictions'] if predictions_stats else 0

        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "predictions": {
                "total": total_preds,
                "last_hour": predictions_stats['predictions_1h'] if predictions_stats else 0,
                "last_24h": predictions_stats['predictions_24h'] if predictions_stats else 0,
                "last_7d": predictions_stats['predictions_7d'] if predictions_stats else 0,
                "positive": positive,
                "negative": negative,
                "positive_rate_percent": round(positive / total_preds * 100, 2) if total_preds > 0 else 0,
                "avg_probability": round(predictions_stats['avg_probability'], 4) if predictions_stats and predictions_stats['avg_probability'] else None,
                "avg_duration_ms": round(predictions_stats['avg_duration_ms'], 2) if predictions_stats and predictions_stats['avg_duration_ms'] else None,
                "unique_coins": predictions_stats['unique_coins'] if predictions_stats else 0,
            },
            "models": {
                "total": model_stats['total_models'] if model_stats else 0,
                "active": model_stats['active_models'] if model_stats else 0,
                "inactive": model_stats['inactive_models'] if model_stats else 0,
            },
            "webhooks_24h": {
                "total": webhook_stats['total_webhooks'] if webhook_stats else 0,
                "success": webhook_stats['successful_webhooks'] if webhook_stats else 0,
                "failed": webhook_stats['failed_webhooks'] if webhook_stats else 0,
            },
            "alerts": {
                "total": alerts_stats['total_alerts'] if alerts_stats else 0,
                "last_24h": alerts_stats['alerts_24h'] if alerts_stats else 0,
            },
            "uptime_seconds": int(time.time() - _startup_time),
        }

    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {
            "success": False,
            "error": str(e),
        }


def _format_uptime(seconds: int) -> str:
    """Formatiert Uptime in menschenlesbares Format."""
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, secs = divmod(remainder, 60)

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")

    return " ".join(parts)

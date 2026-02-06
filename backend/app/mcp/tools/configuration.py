"""
MCP Tools for Configuration

Provides tools for managing model configuration and retrieving statistics.
All tools delegate to existing service functions to avoid code duplication.
"""
import logging
from typing import Any, Dict, List, Optional

from app.database.models import (
    update_alert_config as db_update_alert_config,
    get_model_statistics as db_get_model_statistics,
    get_n8n_status_for_model as db_get_n8n_status_for_model,
    get_ignore_settings as db_get_ignore_settings,
    update_ignore_settings as db_update_ignore_settings,
    get_max_log_entries_settings as db_get_max_log_entries_settings,
    update_max_log_entries_settings as db_update_max_log_entries_settings,
)
from app.database.connection import get_pool

logger = logging.getLogger(__name__)


async def update_alert_config(
    active_model_id: int,
    n8n_webhook_url: Optional[str] = None,
    n8n_enabled: Optional[bool] = None,
    n8n_send_mode: Optional[List[str]] = None,
    alert_threshold: Optional[float] = None,
    coin_filter_mode: Optional[str] = None,
    coin_whitelist: Optional[List[str]] = None,
    min_scan_interval_seconds: Optional[int] = None
) -> Dict[str, Any]:
    """
    Aktualisiert die Alert-Konfiguration für ein aktives Modell.

    Args:
        active_model_id: ID des aktiven Modells
        n8n_webhook_url: n8n Webhook URL (optional, leerer String = löschen)
        n8n_enabled: n8n aktivieren/deaktivieren (optional)
        n8n_send_mode: Send-Mode als Liste (optional)
            - 'all': Alle Vorhersagen senden
            - 'alerts_only': Nur Alerts (positive mit hoher Wahrscheinlichkeit)
            - 'positive_only': Nur positive Vorhersagen
            - 'negative_only': Nur negative Vorhersagen
        alert_threshold: Alert-Schwellenwert 0.0-1.0 (optional)
        coin_filter_mode: 'all' oder 'whitelist' (optional)
        coin_whitelist: Liste erlaubter Coin-Adressen (optional)
        min_scan_interval_seconds: Minimaler Scan-Interval in Sekunden (optional)

    Returns:
        Dict mit Ergebnis der Aktualisierung
    """
    try:
        # Validierung
        if alert_threshold is not None and not (0.0 <= alert_threshold <= 1.0):
            return {
                "success": False,
                "error": f"alert_threshold must be between 0.0 and 1.0, got: {alert_threshold}"
            }

        if n8n_send_mode is not None:
            allowed_modes = ['all', 'alerts_only', 'positive_only', 'negative_only']
            for mode in n8n_send_mode:
                if mode not in allowed_modes:
                    return {
                        "success": False,
                        "error": f"Invalid n8n_send_mode: {mode}. Allowed: {allowed_modes}"
                    }

        if coin_filter_mode is not None and coin_filter_mode not in ['all', 'whitelist']:
            return {
                "success": False,
                "error": f"coin_filter_mode must be 'all' or 'whitelist', got: {coin_filter_mode}"
            }

        # Aktualisiere Konfiguration
        success = await db_update_alert_config(
            active_model_id=active_model_id,
            n8n_webhook_url=n8n_webhook_url,
            n8n_enabled=n8n_enabled,
            n8n_send_mode=n8n_send_mode,
            alert_threshold=alert_threshold,
            coin_filter_mode=coin_filter_mode,
            coin_whitelist=coin_whitelist,
            min_scan_interval_seconds=min_scan_interval_seconds
        )

        if success:
            # Erstelle Zusammenfassung der Änderungen
            changes = {}
            if n8n_webhook_url is not None:
                changes["n8n_webhook_url"] = n8n_webhook_url if n8n_webhook_url else "(cleared)"
            if n8n_enabled is not None:
                changes["n8n_enabled"] = n8n_enabled
            if n8n_send_mode is not None:
                changes["n8n_send_mode"] = n8n_send_mode
            if alert_threshold is not None:
                changes["alert_threshold"] = alert_threshold
            if coin_filter_mode is not None:
                changes["coin_filter_mode"] = coin_filter_mode
            if coin_whitelist is not None:
                changes["coin_whitelist"] = f"{len(coin_whitelist)} coins"
            if min_scan_interval_seconds is not None:
                changes["min_scan_interval_seconds"] = min_scan_interval_seconds

            return {
                "success": True,
                "message": f"Alert config for model {active_model_id} updated successfully",
                "changes": changes
            }
        else:
            return {
                "success": False,
                "error": f"Failed to update alert config for model {active_model_id}"
            }

    except ValueError as e:
        logger.warning(f"Validation error updating alert config: {e}")
        return {
            "success": False,
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"Error updating alert config for model {active_model_id}: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def get_model_statistics(active_model_id: int) -> Dict[str, Any]:
    """
    Holt detaillierte Statistiken für ein aktives Modell.

    Args:
        active_model_id: ID des aktiven Modells

    Returns:
        Dict mit detaillierten Statistiken
    """
    try:
        stats = await db_get_model_statistics(active_model_id)

        # Berechne zusätzliche Metriken
        total = stats.get("total_predictions", 0)
        positive = stats.get("positive_predictions", 0)
        negative = stats.get("negative_predictions", 0)

        positive_rate = round(positive / total * 100, 2) if total > 0 else 0
        negative_rate = round(negative / total * 100, 2) if total > 0 else 0

        return {
            "success": True,
            "active_model_id": active_model_id,
            "statistics": {
                "total_predictions": total,
                "positive_predictions": positive,
                "negative_predictions": negative,
                "positive_rate_percent": positive_rate,
                "negative_rate_percent": negative_rate,
                "avg_probability": round(stats.get("avg_probability", 0), 4) if stats.get("avg_probability") else None,
                "avg_probability_positive": round(stats.get("avg_probability_positive", 0), 4) if stats.get("avg_probability_positive") else None,
                "avg_probability_negative": round(stats.get("avg_probability_negative", 0), 4) if stats.get("avg_probability_negative") else None,
                "min_probability": round(stats.get("min_probability", 0), 4) if stats.get("min_probability") else None,
                "max_probability": round(stats.get("max_probability", 0), 4) if stats.get("max_probability") else None,
                "avg_duration_ms": round(stats.get("avg_duration_ms", 0), 2) if stats.get("avg_duration_ms") else None,
                "unique_coins": stats.get("unique_coins", 0),
                "alerts_count": stats.get("alerts_count", 0),
                "first_prediction": str(stats.get("first_prediction")) if stats.get("first_prediction") else None,
                "last_prediction": str(stats.get("last_prediction")) if stats.get("last_prediction") else None,
                "webhook_stats": {
                    "total": stats.get("webhook_total", 0),
                    "success": stats.get("webhook_success", 0),
                    "failed": stats.get("webhook_failed", 0),
                    "success_rate": stats.get("webhook_success_rate"),
                }
            }
        }

    except Exception as e:
        logger.error(f"Error getting statistics for model {active_model_id}: {e}")
        return {
            "success": False,
            "error": str(e),
            "statistics": None
        }


async def get_n8n_status(active_model_id: int) -> Dict[str, Any]:
    """
    Prüft den n8n Webhook-Status für ein Modell.

    Args:
        active_model_id: ID des aktiven Modells

    Returns:
        Dict mit n8n-Status (ok, error, unknown, no_url)
    """
    try:
        result = await db_get_n8n_status_for_model(active_model_id)
        return {
            "success": True,
            "active_model_id": active_model_id,
            "n8n_status": result,
        }
    except Exception as e:
        logger.error(f"Error getting n8n status for model {active_model_id}: {e}")
        return {
            "success": False,
            "error": str(e),
        }


async def get_ignore_settings(active_model_id: int) -> Dict[str, Any]:
    """
    Holt die Coin-Ignore-Einstellungen für ein Modell.

    Args:
        active_model_id: ID des aktiven Modells

    Returns:
        Dict mit Ignore-Einstellungen (ignore_bad_seconds, ignore_positive_seconds, ignore_alert_seconds)
    """
    try:
        pool = await get_pool()
        result = await db_get_ignore_settings(pool, active_model_id)

        if result is None:
            return {
                "success": False,
                "error": f"Model with ID {active_model_id} not found",
            }

        return {
            "success": True,
            "active_model_id": active_model_id,
            "settings": result,
        }
    except Exception as e:
        logger.error(f"Error getting ignore settings for model {active_model_id}: {e}")
        return {
            "success": False,
            "error": str(e),
        }


async def update_ignore_settings(
    active_model_id: int,
    ignore_bad_seconds: int,
    ignore_positive_seconds: int,
    ignore_alert_seconds: int
) -> Dict[str, Any]:
    """
    Aktualisiert die Coin-Ignore-Einstellungen für ein Modell.

    Args:
        active_model_id: ID des aktiven Modells
        ignore_bad_seconds: Sekunden, die negative Coins ignoriert werden (0-86400)
        ignore_positive_seconds: Sekunden, die positive Coins ignoriert werden (0-86400)
        ignore_alert_seconds: Sekunden, die Alert-Coins ignoriert werden (0-86400)

    Returns:
        Dict mit Ergebnis
    """
    try:
        pool = await get_pool()
        success = await db_update_ignore_settings(
            pool, active_model_id,
            ignore_bad_seconds, ignore_positive_seconds, ignore_alert_seconds
        )

        if success:
            return {
                "success": True,
                "message": f"Ignore settings for model {active_model_id} updated",
                "active_model_id": active_model_id,
                "settings": {
                    "ignore_bad_seconds": ignore_bad_seconds,
                    "ignore_positive_seconds": ignore_positive_seconds,
                    "ignore_alert_seconds": ignore_alert_seconds,
                }
            }
        else:
            return {
                "success": False,
                "error": f"Model with ID {active_model_id} not found",
            }
    except ValueError as e:
        return {
            "success": False,
            "error": str(e),
        }
    except Exception as e:
        logger.error(f"Error updating ignore settings for model {active_model_id}: {e}")
        return {
            "success": False,
            "error": str(e),
        }


async def get_max_log_entries(active_model_id: int) -> Dict[str, Any]:
    """
    Holt die Max-Log-Entries-Einstellungen für ein Modell.

    Args:
        active_model_id: ID des aktiven Modells

    Returns:
        Dict mit Max-Log-Entries-Einstellungen
    """
    try:
        pool = await get_pool()
        result = await db_get_max_log_entries_settings(pool, active_model_id)

        if result is None:
            return {
                "success": False,
                "error": f"Model with ID {active_model_id} not found",
            }

        return {
            "success": True,
            "active_model_id": active_model_id,
            "settings": result,
        }
    except Exception as e:
        logger.error(f"Error getting max log entries for model {active_model_id}: {e}")
        return {
            "success": False,
            "error": str(e),
        }


async def update_max_log_entries(
    active_model_id: int,
    max_log_entries_per_coin_negative: int,
    max_log_entries_per_coin_positive: int,
    max_log_entries_per_coin_alert: int
) -> Dict[str, Any]:
    """
    Aktualisiert die Max-Log-Entries-Einstellungen für ein Modell.

    Args:
        active_model_id: ID des aktiven Modells
        max_log_entries_per_coin_negative: Max negative Einträge pro Coin (0-1000, 0=unbegrenzt)
        max_log_entries_per_coin_positive: Max positive Einträge pro Coin (0-1000, 0=unbegrenzt)
        max_log_entries_per_coin_alert: Max Alert-Einträge pro Coin (0-1000, 0=unbegrenzt)

    Returns:
        Dict mit Ergebnis
    """
    try:
        pool = await get_pool()
        success = await db_update_max_log_entries_settings(
            pool, active_model_id,
            max_log_entries_per_coin_negative,
            max_log_entries_per_coin_positive,
            max_log_entries_per_coin_alert
        )

        if success:
            return {
                "success": True,
                "message": f"Max log entries settings for model {active_model_id} updated",
                "active_model_id": active_model_id,
                "settings": {
                    "max_log_entries_per_coin_negative": max_log_entries_per_coin_negative,
                    "max_log_entries_per_coin_positive": max_log_entries_per_coin_positive,
                    "max_log_entries_per_coin_alert": max_log_entries_per_coin_alert,
                }
            }
        else:
            return {
                "success": False,
                "error": f"Model with ID {active_model_id} not found",
            }
    except ValueError as e:
        return {
            "success": False,
            "error": str(e),
        }
    except Exception as e:
        logger.error(f"Error updating max log entries for model {active_model_id}: {e}")
        return {
            "success": False,
            "error": str(e),
        }

"""
MCP Tools for System/Health

Provides tools for health checks, service statistics, configuration,
logs, and admin/debug operations.
"""
import logging
import os
import subprocess
import time
from datetime import datetime
from typing import Any, Dict

from app.database.connection import get_pool
from app.database.models import get_active_models
from app.utils.config import load_persistent_config, save_persistent_config

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
            WHERE created_at > NOW() - INTERVAL '24 hours'
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


async def get_system_config() -> Dict[str, Any]:
    """
    Holt die aktuelle persistente Konfiguration.

    Returns:
        Dict mit Konfiguration (database_url, training_service_url, etc.)
    """
    try:
        config = load_persistent_config()
        return {
            "success": True,
            "config": config,
        }
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {
            "success": False,
            "error": str(e),
        }


async def update_configuration(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Speichert die persistente Konfiguration.

    Args:
        config: Konfiguration als Dict (database_url, training_service_url, n8n_webhook_url, etc.)

    Returns:
        Dict mit Ergebnis
    """
    try:
        success = save_persistent_config(config)

        if success:
            return {
                "success": True,
                "message": "Configuration saved successfully",
                "config": config,
            }
        else:
            return {
                "success": False,
                "error": "Failed to save configuration",
            }
    except Exception as e:
        logger.error(f"Error saving config: {e}")
        return {
            "success": False,
            "error": str(e),
        }


async def get_logs(tail: int = 100) -> Dict[str, Any]:
    """
    Holt die letzten Log-Zeilen des Services.

    Args:
        tail: Anzahl der Log-Zeilen (default: 100)

    Returns:
        Dict mit Log-Inhalt
    """
    try:
        # Try Docker logs first
        try:
            container_name = os.getenv("HOSTNAME", "pump-server")
            docker_check = subprocess.run(
                ["which", "docker"],
                capture_output=True,
                text=True,
                timeout=2
            )

            if docker_check.returncode == 0:
                result = subprocess.run(
                    ["docker", "logs", "--tail", str(tail), container_name],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if result.returncode == 0 and result.stdout:
                    return {
                        "success": True,
                        "source": "docker",
                        "lines": result.stdout.strip().split("\n"),
                        "count": len(result.stdout.strip().split("\n")),
                    }
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # Fallback: Read from log files
        log_paths = [
            ("/app/logs/fastapi.log", "FastAPI"),
            ("/app/logs/streamlit.log", "Streamlit"),
            ("/var/log/supervisor/supervisord.log", "Supervisor"),
        ]

        all_logs = []
        for log_path, log_name in log_paths:
            try:
                if os.path.exists(log_path):
                    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        for line in lines:
                            all_logs.append(f"[{log_name}] {line.rstrip()}")
            except Exception:
                pass

        if all_logs:
            recent_logs = all_logs[-tail:]
            return {
                "success": True,
                "source": "files",
                "lines": recent_logs,
                "count": len(recent_logs),
            }

        return {
            "success": True,
            "source": "none",
            "lines": [],
            "count": 0,
            "message": "Keine Logs verfügbar",
        }

    except Exception as e:
        logger.error(f"Error reading logs: {e}")
        return {
            "success": False,
            "error": str(e),
        }


async def restart_system() -> Dict[str, Any]:
    """
    Initiiert einen Service-Neustart über SIGTERM.

    Supervisor startet den Service automatisch neu.

    Returns:
        Dict mit Neustart-Status
    """
    try:
        import signal

        logger.warning("Service-Neustart angefordert über MCP")

        os.kill(os.getpid(), signal.SIGTERM)

        return {
            "success": True,
            "message": "Service wird neu gestartet... Bitte warten Sie einen Moment.",
            "auto_restart_enabled": True,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error restarting system: {e}")
        return {
            "success": False,
            "error": str(e),
        }


async def delete_old_logs(active_model_id: int) -> Dict[str, Any]:
    """
    Löscht ALLE alten Logs (alert_evaluations, predictions, model_predictions) für ein Modell.

    ACHTUNG: Diese Aktion ist nicht rückgängig zu machen!

    Args:
        active_model_id: ID des aktiven Modells

    Returns:
        Dict mit Lösch-Ergebnis
    """
    try:
        pool = await get_pool()

        # Check if model exists
        model_row = await pool.fetchrow(
            "SELECT id, model_id FROM prediction_active_models WHERE id = $1",
            active_model_id
        )
        if not model_row:
            return {
                "success": False,
                "error": f"Model with ID {active_model_id} not found",
            }

        # Delete alert_evaluations
        deleted_alerts_rows = await pool.fetch("""
            DELETE FROM alert_evaluations
            WHERE prediction_id IN (
                SELECT id FROM predictions WHERE active_model_id = $1
            )
            RETURNING id
        """, active_model_id)
        deleted_alerts = len(deleted_alerts_rows) if deleted_alerts_rows else 0

        # Delete predictions (old table)
        deleted_predictions_rows = await pool.fetch("""
            DELETE FROM predictions
            WHERE active_model_id = $1
            RETURNING id
        """, active_model_id)
        deleted_predictions = len(deleted_predictions_rows) if deleted_predictions_rows else 0

        # Delete model_predictions (new table)
        deleted_model_predictions_rows = await pool.fetch("""
            DELETE FROM model_predictions
            WHERE active_model_id = $1
            RETURNING id
        """, active_model_id)
        deleted_model_predictions = len(deleted_model_predictions_rows) if deleted_model_predictions_rows else 0

        return {
            "success": True,
            "message": f"All logs deleted for model {active_model_id}",
            "active_model_id": active_model_id,
            "deleted_alerts": deleted_alerts,
            "deleted_predictions": deleted_predictions,
            "deleted_model_predictions": deleted_model_predictions,
        }
    except Exception as e:
        logger.error(f"Error deleting old logs for model {active_model_id}: {e}")
        return {
            "success": False,
            "error": str(e),
        }


async def migrate_performance_metrics() -> Dict[str, Any]:
    """
    Führt die Datenbank-Migration für Performance-Metriken aus.

    Fügt Spalten für Training-Metriken zur prediction_active_models Tabelle hinzu.

    Returns:
        Dict mit Migrations-Ergebnis
    """
    try:
        pool = await get_pool()

        await pool.execute("""
            ALTER TABLE prediction_active_models
            ADD COLUMN IF NOT EXISTS training_accuracy NUMERIC(5, 4),
            ADD COLUMN IF NOT EXISTS training_f1 NUMERIC(5, 4),
            ADD COLUMN IF NOT EXISTS training_precision NUMERIC(5, 4),
            ADD COLUMN IF NOT EXISTS training_recall NUMERIC(5, 4),
            ADD COLUMN IF NOT EXISTS roc_auc NUMERIC(5, 4),
            ADD COLUMN IF NOT EXISTS mcc NUMERIC(5, 4),
            ADD COLUMN IF NOT EXISTS confusion_matrix JSONB,
            ADD COLUMN IF NOT EXISTS simulated_profit_pct NUMERIC(8, 4)
        """)

        await pool.execute("COMMENT ON COLUMN prediction_active_models.training_accuracy IS 'Training Accuracy (0.0000-1.0000)'")
        await pool.execute("COMMENT ON COLUMN prediction_active_models.training_f1 IS 'Training F1-Score (0.0000-1.0000)'")
        await pool.execute("COMMENT ON COLUMN prediction_active_models.training_precision IS 'Training Precision (0.0000-1.0000)'")
        await pool.execute("COMMENT ON COLUMN prediction_active_models.training_recall IS 'Training Recall (0.0000-1.0000)'")
        await pool.execute("COMMENT ON COLUMN prediction_active_models.roc_auc IS 'ROC AUC Score (0.0000-1.0000)'")
        await pool.execute("COMMENT ON COLUMN prediction_active_models.mcc IS 'Matthews Correlation Coefficient (-1.0000-1.0000)'")
        await pool.execute("COMMENT ON COLUMN prediction_active_models.confusion_matrix IS 'Confusion Matrix als JSON'")
        await pool.execute("COMMENT ON COLUMN prediction_active_models.simulated_profit_pct IS 'Simulierte Profitabilität in Prozent'")

        await pool.execute("CREATE INDEX IF NOT EXISTS idx_active_models_accuracy ON prediction_active_models(training_accuracy)")
        await pool.execute("CREATE INDEX IF NOT EXISTS idx_active_models_f1 ON prediction_active_models(training_f1)")
        await pool.execute("CREATE INDEX IF NOT EXISTS idx_active_models_profit ON prediction_active_models(simulated_profit_pct)")

        return {
            "success": True,
            "message": "Performance-Metriken Migration erfolgreich ausgeführt",
        }
    except Exception as e:
        logger.error(f"Error during performance metrics migration: {e}")
        return {
            "success": False,
            "error": str(e),
        }


async def debug_active_models() -> Dict[str, Any]:
    """
    Debug: Zeigt alle aktiven Modelle mit vollständigen Details.

    Returns:
        Dict mit Liste aller aktiven Modelle
    """
    try:
        models = await get_active_models()
        return {
            "success": True,
            "active_models": models,
            "count": len(models),
        }
    except Exception as e:
        logger.error(f"Error in debug_active_models: {e}")
        return {
            "success": False,
            "error": str(e),
        }


async def debug_coin_metrics() -> Dict[str, Any]:
    """
    Debug: Zeigt coin_metrics Statistiken (Gesamtanzahl, neuester/ältester Eintrag, unique Coins).

    Returns:
        Dict mit coin_metrics Statistiken
    """
    try:
        pool = await get_pool()

        row = await pool.fetchrow("""
            SELECT COUNT(*) as total,
                   MAX(timestamp) as latest,
                   MIN(timestamp) as earliest,
                   COUNT(DISTINCT mint) as unique_coins
            FROM coin_metrics
        """)

        if row:
            return {
                "success": True,
                "total": row['total'],
                "latest": str(row['latest']) if row['latest'] else None,
                "earliest": str(row['earliest']) if row['earliest'] else None,
                "unique_coins": row['unique_coins'],
            }
        else:
            return {
                "success": True,
                "message": "Keine Daten",
                "total": 0,
            }
    except Exception as e:
        logger.error(f"Error in debug_coin_metrics: {e}")
        return {
            "success": False,
            "error": str(e),
        }

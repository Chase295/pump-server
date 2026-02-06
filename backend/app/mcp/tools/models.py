"""
MCP Tools for Model Management

Provides tools for listing, importing, and managing ML models.
All tools delegate to existing service functions to avoid code duplication.
"""
import json
import logging
from typing import Any, Dict, List, Optional

from app.database.models import (
    get_available_models as db_get_available_models,
    get_active_models as db_get_active_models,
    import_model as db_import_model,
    activate_model as db_activate_model,
    deactivate_model as db_deactivate_model,
    get_model_from_training_service,
    rename_active_model as db_rename_active_model,
    delete_active_model as db_delete_active_model,
    update_model_performance_metrics as db_update_model_performance_metrics,
)
from app.prediction.model_manager import download_model_file

logger = logging.getLogger(__name__)


async def list_active_models(include_inactive: bool = False) -> Dict[str, Any]:
    """
    Liste aller aktiven (und optional inaktiven) ML-Modelle.

    Args:
        include_inactive: Wenn True, werden auch pausierte Modelle zurückgegeben

    Returns:
        Dict mit Liste der Modelle und Metadaten
    """
    try:
        models = await db_get_active_models(include_inactive=include_inactive)

        # Formatiere Output für bessere Lesbarkeit
        formatted_models = []
        for m in models:
            formatted_models.append({
                "id": m.get("id"),
                "model_id": m.get("model_id"),
                "name": m.get("custom_name") or m.get("model_name"),
                "model_type": m.get("model_type"),
                "is_active": m.get("is_active", False),
                "target_direction": m.get("target_direction"),
                "future_minutes": m.get("future_minutes"),
                "alert_threshold": m.get("alert_threshold"),
                "total_predictions": m.get("total_predictions", 0),
                "stats": m.get("stats"),
                "training_accuracy": m.get("training_accuracy"),
                "training_f1": m.get("training_f1"),
            })

        return {
            "success": True,
            "models": formatted_models,
            "total": len(formatted_models),
            "active_count": sum(1 for m in formatted_models if m.get("is_active")),
            "inactive_count": sum(1 for m in formatted_models if not m.get("is_active")),
        }
    except Exception as e:
        logger.error(f"Error listing active models: {e}")
        return {
            "success": False,
            "error": str(e),
            "models": [],
            "total": 0
        }


async def list_available_models() -> Dict[str, Any]:
    """
    Liste aller verfügbaren Modelle zum Import vom Training-Service.

    Zeigt nur Modelle die noch nicht importiert wurden.

    Returns:
        Dict mit Liste der verfügbaren Modelle
    """
    try:
        models = await db_get_available_models()

        # Formatiere Output
        formatted_models = []
        for m in models:
            formatted_models.append({
                "id": m.get("id"),
                "name": m.get("name"),
                "model_type": m.get("model_type"),
                "target_direction": m.get("target_direction"),
                "future_minutes": m.get("future_minutes"),
                "features_count": len(m.get("features", [])),
                "training_accuracy": m.get("training_accuracy"),
                "training_f1": m.get("training_f1"),
                "training_precision": m.get("training_precision"),
                "training_recall": m.get("training_recall"),
            })

        return {
            "success": True,
            "models": formatted_models,
            "total": len(formatted_models),
        }
    except Exception as e:
        logger.error(f"Error listing available models: {e}")
        return {
            "success": False,
            "error": str(e),
            "models": [],
            "total": 0
        }


async def import_model(model_id: int) -> Dict[str, Any]:
    """
    Importiert ein Modell vom Training-Service.

    Args:
        model_id: ID des Modells im Training-Service

    Returns:
        Dict mit Ergebnis des Imports
    """
    try:
        # 1. Download Model-Datei
        logger.info(f"Downloading model {model_id}...")
        local_path = await download_model_file(model_id)

        if not local_path:
            return {
                "success": False,
                "error": f"Could not download model file for model {model_id}",
            }

        # 2. Hole Model-Daten für URL
        model_data = await get_model_from_training_service(model_id)
        model_file_url = model_data.get("model_file_path") if model_data else None

        # 3. Import in Datenbank
        active_model_id = await db_import_model(
            model_id=model_id,
            local_model_path=local_path,
            model_file_url=model_file_url
        )

        return {
            "success": True,
            "message": f"Model {model_id} successfully imported",
            "active_model_id": active_model_id,
            "local_path": local_path,
        }
    except ValueError as e:
        logger.warning(f"Import validation error: {e}")
        return {
            "success": False,
            "error": str(e),
        }
    except Exception as e:
        logger.error(f"Error importing model {model_id}: {e}")
        return {
            "success": False,
            "error": str(e),
        }


async def get_model_details(active_model_id: int) -> Dict[str, Any]:
    """
    Holt Details eines aktiven Modells.

    Args:
        active_model_id: ID des aktiven Modells (nicht model_id!)

    Returns:
        Dict mit Modell-Details
    """
    try:
        models = await db_get_active_models(include_inactive=True)

        model = next((m for m in models if m.get("id") == active_model_id), None)

        if not model:
            return {
                "success": False,
                "error": f"Model with active_model_id {active_model_id} not found",
            }

        return {
            "success": True,
            "model": {
                "id": model.get("id"),
                "model_id": model.get("model_id"),
                "name": model.get("custom_name") or model.get("model_name"),
                "model_type": model.get("model_type"),
                "is_active": model.get("is_active", False),
                "target_variable": model.get("target_variable"),
                "target_direction": model.get("target_direction"),
                "target_value": model.get("target_value"),
                "future_minutes": model.get("future_minutes"),
                "features": model.get("features", []),
                "features_count": len(model.get("features", [])),
                "alert_threshold": model.get("alert_threshold"),
                "n8n_enabled": model.get("n8n_enabled"),
                "n8n_webhook_url": model.get("n8n_webhook_url"),
                "n8n_send_mode": model.get("n8n_send_mode"),
                "ignore_bad_seconds": model.get("ignore_bad_seconds"),
                "ignore_positive_seconds": model.get("ignore_positive_seconds"),
                "ignore_alert_seconds": model.get("ignore_alert_seconds"),
                "total_predictions": model.get("total_predictions", 0),
                "stats": model.get("stats"),
                "training_accuracy": model.get("training_accuracy"),
                "training_f1": model.get("training_f1"),
                "training_precision": model.get("training_precision"),
                "training_recall": model.get("training_recall"),
                "created_at": str(model.get("created_at")) if model.get("created_at") else None,
                "last_prediction_at": str(model.get("last_prediction_at")) if model.get("last_prediction_at") else None,
            }
        }
    except Exception as e:
        logger.error(f"Error getting model details: {e}")
        return {
            "success": False,
            "error": str(e),
        }


async def activate_model(active_model_id: int) -> Dict[str, Any]:
    """
    Aktiviert ein pausiertes Modell.

    Args:
        active_model_id: ID des aktiven Modells

    Returns:
        Dict mit Ergebnis
    """
    try:
        success = await db_activate_model(active_model_id)

        if success:
            return {
                "success": True,
                "message": f"Model {active_model_id} activated successfully",
            }
        else:
            return {
                "success": False,
                "error": f"Could not activate model {active_model_id}",
            }
    except Exception as e:
        logger.error(f"Error activating model {active_model_id}: {e}")
        return {
            "success": False,
            "error": str(e),
        }


async def deactivate_model(active_model_id: int) -> Dict[str, Any]:
    """
    Deaktiviert (pausiert) ein aktives Modell.

    Args:
        active_model_id: ID des aktiven Modells

    Returns:
        Dict mit Ergebnis
    """
    try:
        success = await db_deactivate_model(active_model_id)

        if success:
            return {
                "success": True,
                "message": f"Model {active_model_id} deactivated successfully",
            }
        else:
            return {
                "success": False,
                "error": f"Could not deactivate model {active_model_id}",
            }
    except Exception as e:
        logger.error(f"Error deactivating model {active_model_id}: {e}")
        return {
            "success": False,
            "error": str(e),
        }


async def rename_model(active_model_id: int, new_name: str) -> Dict[str, Any]:
    """
    Benennt ein aktives Modell um.

    Args:
        active_model_id: ID des aktiven Modells
        new_name: Neuer Name für das Modell

    Returns:
        Dict mit Ergebnis
    """
    try:
        if not new_name or not new_name.strip():
            return {
                "success": False,
                "error": "new_name darf nicht leer sein",
            }

        success = await db_rename_active_model(active_model_id, new_name.strip())

        if success:
            return {
                "success": True,
                "message": f"Model {active_model_id} renamed to '{new_name.strip()}'",
                "active_model_id": active_model_id,
                "new_name": new_name.strip(),
            }
        else:
            return {
                "success": False,
                "error": f"Model with ID {active_model_id} not found",
            }
    except Exception as e:
        logger.error(f"Error renaming model {active_model_id}: {e}")
        return {
            "success": False,
            "error": str(e),
        }


async def delete_model(active_model_id: int) -> Dict[str, Any]:
    """
    Löscht ein aktives Modell und alle zugehörigen Predictions.

    ACHTUNG: Diese Aktion ist nicht rückgängig zu machen!

    Args:
        active_model_id: ID des aktiven Modells

    Returns:
        Dict mit Ergebnis
    """
    try:
        success = await db_delete_active_model(active_model_id)

        if success:
            return {
                "success": True,
                "message": f"Model {active_model_id} and all associated predictions deleted",
                "active_model_id": active_model_id,
            }
        else:
            return {
                "success": False,
                "error": f"Model with ID {active_model_id} not found",
            }
    except Exception as e:
        logger.error(f"Error deleting model {active_model_id}: {e}")
        return {
            "success": False,
            "error": str(e),
        }


async def update_model_metrics(active_model_id: int, model_id: int) -> Dict[str, Any]:
    """
    Aktualisiert die Performance-Metriken eines Modells vom Training-Service.

    Args:
        active_model_id: ID des aktiven Modells
        model_id: ID des Modells im Training-Service

    Returns:
        Dict mit Ergebnis
    """
    try:
        success = await db_update_model_performance_metrics(active_model_id, model_id)

        if success:
            return {
                "success": True,
                "message": f"Performance metrics for model {active_model_id} updated from training service",
                "active_model_id": active_model_id,
            }
        else:
            return {
                "success": False,
                "error": f"Could not update metrics for model {active_model_id}",
            }
    except Exception as e:
        logger.error(f"Error updating metrics for model {active_model_id}: {e}")
        return {
            "success": False,
            "error": str(e),
        }

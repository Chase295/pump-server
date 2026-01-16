"""
FastAPI Routes für ML Prediction Service
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends, Response, status, BackgroundTasks, Query
from fastapi.responses import PlainTextResponse
import asyncpg

from app.api.schemas import (
    PredictRequest, PredictionResponse, PredictionResult, PredictionDetail,
    PredictionsListResponse, ModelInfo, ModelsListResponse, AvailableModelsResponse,
    AvailableModel, ModelImportRequest, ImportModelResponse, RenameModelRequest,
    UpdateAlertThresholdRequest, UpdateN8nSettingsRequest, UpdateAlertConfigRequest,
    UpdateIgnoreSettingsRequest, IgnoreSettingsResponse,
    UpdateMaxLogEntriesRequest, MaxLogEntriesResponse,
    HealthResponse, StatsResponse, ModelStatisticsResponse,
    CoinDetailsResponse
)
from app.database.connection import get_pool
from app.database.models import (
    get_available_models, get_active_models, import_model,
    activate_model, deactivate_model, delete_active_model, rename_active_model,
    update_alert_threshold, update_n8n_settings, update_alert_config, save_prediction, get_predictions, get_latest_prediction, get_model_statistics,
    get_n8n_status_for_model, update_model_performance_metrics,
    update_ignore_settings, get_ignore_settings,
    update_max_log_entries_settings, get_max_log_entries_settings,
    get_coin_price_history, get_coin_predictions_for_model
)
from app.utils.config import load_persistent_config, save_persistent_config
from app.database.alert_models import get_alerts, get_alert_details, get_alert_statistics, get_model_alert_statistics, get_coin_evaluations_for_model
from app.database.evaluation_job import evaluate_pending_predictions
from app.prediction.engine import predict_coin_all_models
from app.prediction.model_manager import download_model_file
# from app.training.engine import train_model  # Training module entfernt
# from app.training.model_loader import test_model  # Training module entfernt
# from app.queue.job_manager import create_training_job, get_job_status  # Temporär deaktiviert
# from app.database.models_ml_training import (  # Training module entfernt
#     create_ml_model_job, get_ml_model, list_ml_models,
#     create_test_job, create_comparison_job,
#     get_ml_jobs, get_ml_job
# )
from app.utils.metrics import get_health_status, generate_metrics
from app.utils.logging_config import get_logger, set_request_id
from app.utils.config import MODEL_STORAGE_PATH
import os
import json

def _parse_send_mode_for_response(value: Any) -> List[str]:
    """
    Konvertiert n8n_send_mode von DB-Format (JSONB Array oder String) zu Python List.
    Für Rückwärtskompatibilität mit alten String-Werten.
    """
    if value is None:
        return ['all']
    
    # Wenn es bereits eine Liste ist
    if isinstance(value, list):
        # Prüfe, ob die Liste verschachtelte JSON-Strings enthält (z.B. ['["all"]'])
        if len(value) == 1 and isinstance(value[0], str):
            try:
                # Versuche das erste Element als JSON zu parsen
                parsed = json.loads(value[0])
                if isinstance(parsed, list):
                    return parsed
            except (json.JSONDecodeError, TypeError):
                pass
        # Wenn die Liste bereits korrekt ist (z.B. ['all', 'alerts_only']), direkt zurückgeben
        return value
    
    # Wenn es ein String ist (Rückwärtskompatibilität)
    if isinstance(value, str):
        try:
            # Versuche als JSON zu parsen (falls es ein JSON-String ist)
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
            return [value]
        except (json.JSONDecodeError, TypeError):
            return [value]
    
    # Wenn es ein dict ist (asyncpg gibt JSONB manchmal als dict zurück)
    if isinstance(value, dict):
        if 'value' in value:
            return value['value'] if isinstance(value['value'], list) else [value['value']]
        return list(value.values()) if value else ['all']
    
    # Fallback
    return ['all']

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["ML Prediction Service"])

# ============================================================
# Dependency: DB Pool
# ============================================================

async def get_db_pool() -> asyncpg.Pool:
    """Dependency für DB-Pool"""
    return await get_pool()

# ============================================================
# Models Endpoints
# ============================================================

@router.get("/models/available", response_model=AvailableModelsResponse)
async def get_available_models_endpoint():
    """
    Liste aller verfügbaren Modelle aus ml_models (für Import).
    
    Filter: status = 'READY' AND is_deleted = false
    """
    try:
        models = await get_available_models()
        
        available_models = [
            AvailableModel(
                id=m['id'],
                name=m['name'],
                model_type=m['model_type'],
                target_variable=m['target_variable'],
                target_operator=m['target_operator'],
                target_value=m['target_value'],
                future_minutes=m['future_minutes'],
                price_change_percent=m['price_change_percent'],
                target_direction=m['target_direction'],
                features=m['features'],
                phases=m['phases'],
                training_accuracy=m['training_accuracy'],
                training_f1=m['training_f1'],
                created_at=m['created_at']
            )
            for m in models
        ]
        
        return AvailableModelsResponse(
            models=available_models,
            total=len(available_models)
        )
    except Exception as e:
        logger.error(f"❌ Fehler beim Laden verfügbarer Modelle: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/available/{model_id}", response_model=AvailableModel)
async def get_available_model_details_endpoint(model_id: int):
    """
    Details eines verfügbaren Modells vom Training-Service abrufen.
    """
    try:
        from app.database.models import get_model_from_training_service
        
        model = await get_model_from_training_service(model_id)
        
        if not model:
            raise HTTPException(status_code=404, detail=f"Modell {model_id} nicht gefunden")
        
        return AvailableModel(
            id=model['id'],
            name=model['name'],
            model_type=model['model_type'],
            target_variable=model['target_variable'],
            target_operator=model.get('target_operator'),
            target_value=model.get('target_value'),
            future_minutes=model.get('future_minutes'),
            price_change_percent=model.get('price_change_percent'),
            target_direction=model.get('target_direction'),
            features=model.get('features', []),
            phases=model.get('phases'),
            training_accuracy=model.get('training_accuracy'),
            training_f1=model.get('training_f1'),
            created_at=model.get('created_at')
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Fehler beim Laden der Modell-Details: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/import", response_model=ImportModelResponse, status_code=status.HTTP_201_CREATED)
async def import_model_endpoint(request: ModelImportRequest):
    """
    Importiert Modell vom Training Service.
    
    Lädt Modell-Datei herunter und speichert in prediction_active_models.
    
    ⚠️ WICHTIG: Prüft doppelt ob Modell bereits importiert ist (auch wenn gelöscht).
    """
    try:
        import asyncio
        from datetime import datetime
        
        logger.info(f"📥 Import-Anfrage für Modell ID: {request.model_id} um {datetime.now().isoformat()}")
        logger.info(f"🔍 Prüfe ob Modell {request.model_id} bereits importiert ist...")
        
        # 1. Prüfe ob Modell bereits importiert (VOR Download - spart Zeit)
        # Verwende direkte DB-Abfrage für atomare Prüfung (verhindert Race Conditions)
        from app.database.connection import get_pool
        pool = await get_pool()
        existing_db = await pool.fetchrow("""
            SELECT id, is_active FROM prediction_active_models WHERE model_id = $1
        """, request.model_id)
        
        if existing_db:
            existing_id = existing_db['id']
            is_active = existing_db.get('is_active', False)
            status = "aktiv" if is_active else "pausiert"
            logger.warning(f"⚠️ Modell {request.model_id} ist bereits importiert (active_model_id: {existing_id}, Status: {status})")
            raise HTTPException(
                status_code=400, 
                detail=f"Modell {request.model_id} ist bereits importiert (active_model_id: {existing_id}, Status: {status}). Lösche es zuerst, um es erneut zu importieren."
            )
        
        logger.info(f"✅ Modell {request.model_id} ist noch nicht importiert - fahre fort...")
        
        # 2. Lade Modell-Datei vom Training Service
        logger.info(f"📥 Lade Modell {request.model_id} vom Training Service...")
        local_model_path = await download_model_file(request.model_id)
        logger.info(f"✅ Modell-Datei heruntergeladen: {local_model_path}")
        
        # 2.1. Validiere Modell-Datei (prüft Existenz, Ladbarkeit und Struktur)
        logger.info(f"🔍 Validiere Modell-Datei: {local_model_path}")
        try:
            from app.prediction.model_manager import validate_model_file
            validation_result = validate_model_file(local_model_path)
            logger.info(f"✅ Modell-Datei erfolgreich validiert: {validation_result.get('model_type', 'Unknown')}")
        except (FileNotFoundError, ValueError) as e:
            # Lösche heruntergeladene Datei wieder
            try:
                import os
                if os.path.exists(local_model_path):
                    os.remove(local_model_path)
                    logger.info(f"🗑️ Ungültige Modell-Datei gelöscht: {local_model_path}")
            except:
                pass
            error_msg = f"Modell-Datei ist ungültig: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
        except Exception as e:
            # Lösche heruntergeladene Datei wieder
            try:
                import os
                if os.path.exists(local_model_path):
                    os.remove(local_model_path)
                    logger.info(f"🗑️ Fehlerhafte Modell-Datei gelöscht: {local_model_path}")
            except:
                pass
            error_msg = f"Fehler beim Validieren der Modell-Datei: {str(e)}"
            logger.error(f"❌ {error_msg}", exc_info=True)
            raise HTTPException(status_code=500, detail=error_msg)
        
        # 3. Importiere Modell in prediction_active_models (prüft nochmal intern)
        logger.info(f"💾 Speichere Modell {request.model_id} in Datenbank...")
        try:
            active_model_id = await import_model(
                model_id=request.model_id,
                local_model_path=local_model_path,
                model_file_url=request.model_file_url
            )
            logger.info(f"✅ Modell {request.model_id} erfolgreich importiert (active_model_id: {active_model_id})")
        except ValueError as e:
            # Modell bereits importiert - das sollte nicht passieren, da wir oben prüfen
            logger.error(f"❌ Modell {request.model_id} ist bereits importiert (zweite Prüfung): {e}")
            # Lösche heruntergeladene Datei wieder
            try:
                import os
                if os.path.exists(local_model_path):
                    os.remove(local_model_path)
                    logger.info(f"🗑️ Heruntergeladene Datei gelöscht: {local_model_path}")
            except:
                pass
            raise HTTPException(status_code=400, detail=str(e))
        
        # 4. Hole Modell-Informationen
        active_models = await get_active_models()
        imported_model = next((m for m in active_models if m['id'] == active_model_id), None)
        
        if not imported_model:
            # Versuche auch inaktive Modelle
            active_models_all = await get_active_models(include_inactive=True)
            imported_model = next((m for m in active_models_all if m['id'] == active_model_id), None)
        
        if not imported_model:
            logger.error(f"❌ Importiertes Modell {active_model_id} nicht gefunden nach Import")
            raise HTTPException(status_code=404, detail="Importiertes Modell nicht gefunden")
        
        return ImportModelResponse(
            active_model_id=active_model_id,
            model_id=request.model_id,
            model_name=imported_model['name'],
            local_model_path=local_model_path,
            message=f"Modell {request.model_id} erfolgreich importiert"
        )
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"⚠️ Validierungsfehler beim Import: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Fehler beim Modell-Import: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models", response_model=ModelsListResponse)
async def get_models_endpoint(include_inactive: str = "false"):
    """
    Liste aller Modelle (Alias für /models/active)
    """
    return await get_active_models_endpoint(include_inactive)


@router.get("/models/{active_model_id}", response_model=ModelInfo)
async def get_active_model_endpoint(active_model_id: int):
    """
    Details eines aktiven Modells abrufen
    """
    try:
        # Hole alle aktiven Modelle und finde das richtige
        models = await get_active_models(include_inactive=True)
        model = next((m for m in models if m['id'] == active_model_id), None)

        if not model:
            raise HTTPException(status_code=404, detail="Modell nicht gefunden")

        # Konvertiere zu ModelInfo Response
        return ModelInfo(
            id=model['id'],
            model_id=model['model_id'],
            name=model['name'],
            custom_name=model.get('custom_name'),
            model_type=model['model_type'],
            target_variable=model['target_variable'],
            target_operator=model.get('target_operator'),
            target_value=model.get('target_value'),
            future_minutes=model.get('future_minutes'),
            price_change_percent=model.get('price_change_percent'),
            target_direction=model.get('target_direction'),
            features=model.get('features', []),
            phases=model.get('phases'),
            params=model.get('params'),
            is_active=model.get('is_active', True),
            total_predictions=model.get('total_predictions', 0),
            last_prediction_at=model.get('last_prediction_at'),
            alert_threshold=model.get('alert_threshold', 0.7),
            n8n_webhook_url=model.get('n8n_webhook_url'),
            n8n_send_mode=_parse_send_mode_for_response(model.get('n8n_send_mode', 'all')),
            n8n_enabled=model.get('n8n_enabled', True),
            coin_filter_mode=model.get('coin_filter_mode', 'all'),
            coin_whitelist=model.get('coin_whitelist'),
            # 🔄 NEU: Coin-Ignore-Einstellungen
            ignore_bad_seconds=model.get('ignore_bad_seconds'),
            ignore_positive_seconds=model.get('ignore_positive_seconds'),
            ignore_alert_seconds=model.get('ignore_alert_seconds'),
            # 📊 Max-Log-Entries-Einstellungen
            max_log_entries_per_coin_negative=model.get('max_log_entries_per_coin_negative', 0),
            max_log_entries_per_coin_positive=model.get('max_log_entries_per_coin_positive', 0),
            max_log_entries_per_coin_alert=model.get('max_log_entries_per_coin_alert', 0),
            send_ignored_to_n8n=model.get('send_ignored_to_n8n', False),
            stats=model.get('stats'),
            created_at=model.get('created_at')
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Fehler beim Laden des Modells {active_model_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/active", response_model=ModelsListResponse)
async def get_active_models_endpoint(include_inactive: str = "false"):
    """
    Liste aller aktiven Modelle (aus prediction_active_models)
    
    Args:
        include_inactive: Query-Parameter als String ("true" oder "false")
    """
    try:
        # Konvertiere String zu bool
        include_inactive_bool = include_inactive.lower() == "true"
        models = await get_active_models(include_inactive=include_inactive_bool)
        
        model_infos = [
            ModelInfo(
                id=m['id'],
                model_id=m['model_id'],
                name=m['name'],
                custom_name=m.get('custom_name'),
                model_type=m['model_type'],
                target_variable=m['target_variable'],
                target_operator=m['target_operator'],
                target_value=m['target_value'],
                future_minutes=m['future_minutes'],
                price_change_percent=m['price_change_percent'],
                target_direction=m['target_direction'],
                features=m['features'],
                phases=m['phases'],
                params=m['params'],
                is_active=m['is_active'],
                total_predictions=m['total_predictions'],
                average_probability=m.get('average_probability'),
                last_prediction_at=m['last_prediction_at'],
                alert_threshold=m.get('alert_threshold', 0.7),
                n8n_webhook_url=m.get('n8n_webhook_url'),
                n8n_send_mode=_parse_send_mode_for_response(m.get('n8n_send_mode', 'all')),
                n8n_enabled=m.get('n8n_enabled', True),  # WICHTIG: Muss explizit übergeben werden!
                coin_filter_mode=m.get('coin_filter_mode', 'all'),
                coin_whitelist=m.get('coin_whitelist'),
                ignore_bad_seconds=m.get('ignore_bad_seconds', 0),
                ignore_positive_seconds=m.get('ignore_positive_seconds', 0),
                ignore_alert_seconds=m.get('ignore_alert_seconds', 0),
                max_log_entries_per_coin_negative=m.get('max_log_entries_per_coin_negative', 0),
                max_log_entries_per_coin_positive=m.get('max_log_entries_per_coin_positive', 0),
                max_log_entries_per_coin_alert=m.get('max_log_entries_per_coin_alert', 0),
                send_ignored_to_n8n=m.get('send_ignored_to_n8n', False),
                stats=m.get('stats'),
                created_at=m['created_at']
            )
            for m in models
        ]
        
        return ModelsListResponse(
            models=model_infos,
            total=len(model_infos)
        )
    except Exception as e:
        logger.error(f"❌ Fehler beim Laden aktiver Modelle: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/{active_model_id}/activate", status_code=status.HTTP_200_OK)
async def activate_model_endpoint(active_model_id: int):
    """Aktiviert Modell (setzt is_active = true)"""
    try:
        success = await activate_model(active_model_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Modell {active_model_id} nicht gefunden")
        return {"message": f"Modell {active_model_id} aktiviert", "active_model_id": active_model_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Fehler beim Aktivieren: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/{active_model_id}/deactivate", status_code=status.HTTP_200_OK)
async def deactivate_model_endpoint(active_model_id: int):
    """Deaktiviert Modell (setzt is_active = false)"""
    try:
        success = await deactivate_model(active_model_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Modell {active_model_id} nicht gefunden")
        return {"message": f"Modell {active_model_id} deaktiviert", "active_model_id": active_model_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Fehler beim Deaktivieren: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/models/{active_model_id}/rename", status_code=status.HTTP_200_OK)
async def rename_model_endpoint(active_model_id: int, request: RenameModelRequest):
    """Benennt Modell um (setzt custom_name)"""
    try:
        success = await rename_active_model(active_model_id, request.name)
        if not success:
            raise HTTPException(status_code=404, detail=f"Modell {active_model_id} nicht gefunden")
        return {"message": f"Modell {active_model_id} umbenannt zu '{request.name}'", "active_model_id": active_model_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Fehler beim Umbenennen: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/models/{active_model_id}/alert-threshold", status_code=status.HTTP_200_OK)
async def update_alert_threshold_endpoint(active_model_id: int, request: UpdateAlertThresholdRequest):
    """Aktualisiert Alert-Threshold für ein Modell"""
    try:
        success = await update_alert_threshold(active_model_id, request.alert_threshold)
        if not success:
            raise HTTPException(status_code=404, detail=f"Modell {active_model_id} nicht gefunden")
        return {
            "message": f"Alert-Threshold für Modell {active_model_id} auf {request.alert_threshold:.0%} gesetzt",
            "active_model_id": active_model_id,
            "alert_threshold": request.alert_threshold
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Fehler beim Aktualisieren des Alert-Thresholds: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/models/{active_model_id}/n8n-settings", status_code=status.HTTP_200_OK)
async def update_n8n_settings_endpoint(active_model_id: int, request: UpdateN8nSettingsRequest):
    """Aktualisiert n8n Einstellungen für ein aktives Modell"""
    try:
        success = await update_n8n_settings(
            active_model_id, 
            n8n_webhook_url=request.n8n_webhook_url, 
            n8n_send_mode=request.n8n_send_mode,
            n8n_enabled=request.n8n_enabled
        )
        if not success:
            raise HTTPException(status_code=404, detail=f"Modell {active_model_id} nicht gefunden oder keine Änderungen vorgenommen")
        return {
            "message": f"n8n Einstellungen für Modell {active_model_id} aktualisiert",
            "active_model_id": active_model_id,
            "n8n_webhook_url": request.n8n_webhook_url,
            "n8n_send_mode": request.n8n_send_mode,
            "n8n_enabled": request.n8n_enabled
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Fehler beim Aktualisieren der n8n Einstellungen: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/models/{active_model_id}/alert-config", status_code=status.HTTP_200_OK)
async def update_alert_config_endpoint(active_model_id: int, request: UpdateAlertConfigRequest):
    """Aktualisiert komplette Alert-Konfiguration für ein aktives Modell"""
    try:
        success = await update_alert_config(
            active_model_id=active_model_id,
            n8n_webhook_url=request.n8n_webhook_url,
            n8n_enabled=request.n8n_enabled,
            n8n_send_mode=request.n8n_send_mode,
            alert_threshold=request.alert_threshold,
            coin_filter_mode=request.coin_filter_mode,
            coin_whitelist=request.coin_whitelist,
            min_scan_interval_seconds=request.min_scan_interval_seconds,
            send_ignored_to_n8n=request.send_ignored_to_n8n
        )
        if not success:
            raise HTTPException(status_code=404, detail=f"Modell {active_model_id} nicht gefunden oder keine Änderungen vorgenommen")

        return {
            "message": f"Alert-Konfiguration für Modell {active_model_id} erfolgreich aktualisiert",
            "active_model_id": active_model_id,
            "config": {
                "n8n_webhook_url": request.n8n_webhook_url,
                "n8n_enabled": request.n8n_enabled,
                "n8n_send_mode": request.n8n_send_mode,
                "alert_threshold": request.alert_threshold,
                "coin_filter_mode": request.coin_filter_mode,
                "coin_whitelist": request.coin_whitelist,
                "min_scan_interval_seconds": request.min_scan_interval_seconds
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Fehler beim Aktualisieren der Alert-Konfiguration: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/models/{active_model_id}/ignore-settings", status_code=status.HTTP_200_OK)
async def update_ignore_settings_endpoint(
    active_model_id: int,
    request: UpdateIgnoreSettingsRequest,
    pool: asyncpg.Pool = Depends(get_pool)
):
    """Aktualisiert Coin-Ignore-Einstellungen für ein Modell"""
    logger.info(f"🔥 DEBUG API: Ignore-Settings Update für Modell {active_model_id}")
    logger.info(f"🔥 DEBUG API: Eingehende Daten: bad={request.ignore_bad_seconds}, positive={request.ignore_positive_seconds}, alert={request.ignore_alert_seconds}")

    try:
        logger.info(f"🔥 DEBUG API: Rufe update_ignore_settings auf...")
        success = await update_ignore_settings(
            pool=pool,
            active_model_id=active_model_id,
            ignore_bad_seconds=request.ignore_bad_seconds,
            ignore_positive_seconds=request.ignore_positive_seconds,
            ignore_alert_seconds=request.ignore_alert_seconds
        )
        logger.info(f"🔥 DEBUG API: update_ignore_settings returned: {success}")

        if not success:
            logger.error(f"🔥 DEBUG API: Modell {active_model_id} nicht gefunden!")
            raise HTTPException(status_code=404, detail=f"Modell {active_model_id} nicht gefunden")

        response_data = {
            "message": f"Coin-Ignore-Einstellungen für Modell {active_model_id} aktualisiert",
            "active_model_id": active_model_id,
            "ignore_bad_seconds": request.ignore_bad_seconds,
            "ignore_positive_seconds": request.ignore_positive_seconds,
            "ignore_alert_seconds": request.ignore_alert_seconds
        }
        logger.info(f"🔥 DEBUG API: Sende Response: {response_data}")
        return response_data
    except ValueError as e:
        logger.error(f"🔥 DEBUG API: ValueError: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Fehler beim Aktualisieren der Ignore-Einstellungen: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/{active_model_id}/ignore-settings", response_model=IgnoreSettingsResponse)
async def get_ignore_settings_endpoint(
    active_model_id: int,
    pool: asyncpg.Pool = Depends(get_pool)
):
    """Holt aktuelle Coin-Ignore-Einstellungen für ein Modell"""
    try:
        settings = await get_ignore_settings(pool=pool, active_model_id=active_model_id)
        if settings is None:
            raise HTTPException(status_code=404, detail=f"Modell {active_model_id} nicht gefunden")
        return settings
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Fehler beim Laden der Ignore-Einstellungen: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/models/{active_model_id}/max-log-entries", status_code=status.HTTP_200_OK)
async def update_max_log_entries_endpoint(
    active_model_id: int,
    request: UpdateMaxLogEntriesRequest,
    pool: asyncpg.Pool = Depends(get_pool)
):
    """Aktualisiert Max-Log-Entries-Einstellungen für ein Modell"""
    try:
        success = await update_max_log_entries_settings(
            pool=pool,
            active_model_id=active_model_id,
            max_log_entries_per_coin_negative=request.max_log_entries_per_coin_negative,
            max_log_entries_per_coin_positive=request.max_log_entries_per_coin_positive,
            max_log_entries_per_coin_alert=request.max_log_entries_per_coin_alert
        )

        if not success:
            raise HTTPException(status_code=404, detail=f"Modell {active_model_id} nicht gefunden")

        return {
            "message": f"Max-Log-Entries-Einstellungen für Modell {active_model_id} aktualisiert",
            "active_model_id": active_model_id,
            "max_log_entries_per_coin_negative": request.max_log_entries_per_coin_negative,
            "max_log_entries_per_coin_positive": request.max_log_entries_per_coin_positive,
            "max_log_entries_per_coin_alert": request.max_log_entries_per_coin_alert
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Fehler beim Aktualisieren der Max-Log-Entries-Einstellungen: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/{active_model_id}/max-log-entries", response_model=MaxLogEntriesResponse)
async def get_max_log_entries_endpoint(
    active_model_id: int,
    pool: asyncpg.Pool = Depends(get_pool)
):
    """Holt aktuelle Max-Log-Entries-Einstellungen für ein Modell"""
    try:
        settings = await get_max_log_entries_settings(pool=pool, active_model_id=active_model_id)
        if settings is None:
            raise HTTPException(status_code=404, detail=f"Modell {active_model_id} nicht gefunden")

        return MaxLogEntriesResponse(**settings)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Fehler beim Laden der Ignore-Einstellungen: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/models/{active_model_id}/max-log-entries", status_code=status.HTTP_200_OK)
async def update_max_log_entries_endpoint(
    active_model_id: int,
    request: UpdateMaxLogEntriesRequest,
    pool: asyncpg.Pool = Depends(get_pool)
):
    """Aktualisiert Max-Log-Entries-Einstellungen für ein Modell"""
    try:
        success = await update_max_log_entries_settings(
            pool=pool,
            active_model_id=active_model_id,
            max_log_entries_per_coin_negative=request.max_log_entries_per_coin_negative,
            max_log_entries_per_coin_positive=request.max_log_entries_per_coin_positive,
            max_log_entries_per_coin_alert=request.max_log_entries_per_coin_alert
        )

        if not success:
            raise HTTPException(status_code=404, detail=f"Modell {active_model_id} nicht gefunden")

        return {
            "message": f"Max-Log-Entries-Einstellungen für Modell {active_model_id} aktualisiert",
            "active_model_id": active_model_id,
            "max_log_entries_per_coin_negative": request.max_log_entries_per_coin_negative,
            "max_log_entries_per_coin_positive": request.max_log_entries_per_coin_positive,
            "max_log_entries_per_coin_alert": request.max_log_entries_per_coin_alert
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Fehler beim Aktualisieren der Max-Log-Entries-Einstellungen: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/{active_model_id}/max-log-entries", response_model=MaxLogEntriesResponse)
async def get_max_log_entries_endpoint(
    active_model_id: int,
    pool: asyncpg.Pool = Depends(get_pool)
):
    """Holt aktuelle Max-Log-Entries-Einstellungen für ein Modell"""
    try:
        settings = await get_max_log_entries_settings(pool=pool, active_model_id=active_model_id)
        if settings is None:
            raise HTTPException(status_code=404, detail=f"Modell {active_model_id} nicht gefunden")
        return MaxLogEntriesResponse(**settings)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Fehler beim Laden der Max-Log-Entries-Einstellungen: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/{active_model_id}/n8n-status")
async def get_n8n_status_endpoint(active_model_id: int):
    """Gibt den n8n-Status für ein Modell zurück"""
    try:
        status = await get_n8n_status_for_model(active_model_id)
        return status
    except Exception as e:
        logger.error(f"❌ Fehler beim Abrufen des n8n-Status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/{active_model_id}/statistics", response_model=ModelStatisticsResponse)
async def get_model_statistics_endpoint(active_model_id: int):
    """Detaillierte Statistiken für ein aktives Modell"""
    try:
        stats = await get_model_statistics(active_model_id)
        return ModelStatisticsResponse(**stats)
    except Exception as e:
        logger.error(f"❌ Fehler beim Laden der Modell-Statistiken: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/debug/active-models", status_code=status.HTTP_200_OK)
async def debug_active_models(pool: asyncpg.Pool = Depends(get_db_pool)):
    """Debug: Zeigt alle aktiven Modelle"""
    try:
        from app.database.models import get_active_models
        models = await get_active_models()
        return {"active_models": models, "count": len(models)}
    except Exception as e:
        logger.error(f"❌ Debug Fehler: {e}", exc_info=True)
        return {"error": str(e)}

@router.get("/debug/coin-metrics", status_code=status.HTTP_200_OK)
async def debug_coin_metrics(pool: asyncpg.Pool = Depends(get_db_pool)):
    """Debug: Zeigt coin_metrics Statistiken"""
    try:
        # Hole Statistiken
        row = await pool.fetchrow("""
            SELECT COUNT(*) as total,
                   MAX(timestamp) as latest,
                   MIN(timestamp) as earliest,
                   COUNT(DISTINCT mint) as unique_coins
            FROM coin_metrics
        """)
        return dict(row) if row else {"message": "Keine Daten"}
    except Exception as e:
        logger.error(f"❌ Debug coin_metrics Fehler: {e}", exc_info=True)
        return {"error": str(e)}


@router.post("/admin/migrate-performance-metrics", status_code=status.HTTP_200_OK)
async def migrate_performance_metrics():
    """Führt die Datenbank-Migration für Performance-Metriken aus"""
    try:
        pool = await get_pool()

        # Führe die Migration aus
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

        # Füge Kommentare hinzu
        await pool.execute("COMMENT ON COLUMN prediction_active_models.training_accuracy IS 'Training Accuracy (0.0000-1.0000)'")
        await pool.execute("COMMENT ON COLUMN prediction_active_models.training_f1 IS 'Training F1-Score (0.0000-1.0000)'")
        await pool.execute("COMMENT ON COLUMN prediction_active_models.training_precision IS 'Training Precision (0.0000-1.0000)'")
        await pool.execute("COMMENT ON COLUMN prediction_active_models.training_recall IS 'Training Recall (0.0000-1.0000)'")
        await pool.execute("COMMENT ON COLUMN prediction_active_models.roc_auc IS 'ROC AUC Score (0.0000-1.0000)'")
        await pool.execute("COMMENT ON COLUMN prediction_active_models.mcc IS 'Matthews Correlation Coefficient (-1.0000-1.0000)'")
        await pool.execute("COMMENT ON COLUMN prediction_active_models.confusion_matrix IS 'Confusion Matrix als JSON: {\"tp\": int, \"tn\": int, \"fp\": int, \"fn\": int}'")
        await pool.execute("COMMENT ON COLUMN prediction_active_models.simulated_profit_pct IS 'Simulierte Profitabilität in Prozent (-999.9999 bis 999.9999)'")

        # Füge Indizes hinzu
        await pool.execute("CREATE INDEX IF NOT EXISTS idx_active_models_accuracy ON prediction_active_models(training_accuracy)")
        await pool.execute("CREATE INDEX IF NOT EXISTS idx_active_models_f1 ON prediction_active_models(training_f1)")
        await pool.execute("CREATE INDEX IF NOT EXISTS idx_active_models_profit ON prediction_active_models(simulated_profit_pct)")

        return {"message": "Performance-Metriken Migration erfolgreich ausgeführt"}

    except Exception as e:
        logger.error(f"❌ Fehler bei der Migration: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Migration fehlgeschlagen: {str(e)}")


@router.post("/models/{active_model_id}/update-metrics", status_code=status.HTTP_200_OK)
async def update_model_metrics_endpoint(active_model_id: int):
    """Aktualisiert Performance-Metriken eines Modells aus dem Training-Service"""
    try:
        # Hole model_id aus der Datenbank
        pool = await get_pool()
        row = await pool.fetchrow("""
            SELECT model_id FROM prediction_active_models WHERE id = $1
        """, active_model_id)

        if not row:
            raise HTTPException(status_code=404, detail=f"Modell {active_model_id} nicht gefunden")

        model_id = row['model_id']

        # Aktualisiere Metriken
        success = await update_model_performance_metrics(active_model_id, model_id)
        if not success:
            raise HTTPException(status_code=500, detail="Fehler beim Aktualisieren der Metriken")

        return {"message": f"Performance-Metriken für Modell {active_model_id} aktualisiert"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Fehler beim Aktualisieren der Metriken: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/models/{active_model_id}", status_code=status.HTTP_200_OK)
async def delete_model_endpoint(active_model_id: int):
    """Löscht Modell (aus prediction_active_models + lokale Datei)"""
    try:
        logger.info(f"🗑️ Lösche Modell (active_model_id: {active_model_id})...")

        # Hole Modell-Informationen für lokale Datei (auch inaktive Modelle prüfen)
        from app.database.models import get_active_models
        active_models = await get_active_models(include_inactive=True)
        model_to_delete = next((m for m in active_models if m['id'] == active_model_id), None)

        if not model_to_delete:
            logger.warning(f"⚠️ Modell {active_model_id} nicht gefunden")
            raise HTTPException(status_code=404, detail=f"Modell {active_model_id} nicht gefunden")

        model_id = model_to_delete.get('model_id')
        model_name = model_to_delete.get('name', 'Unknown')
        logger.info(f"🗑️ Lösche Modell: {model_name} (model_id: {model_id}, active_model_id: {active_model_id})")

        # Lösche lokale Datei
        local_path = model_to_delete.get('local_model_path')
        if local_path and os.path.exists(local_path):
            try:
                os.remove(local_path)
                logger.info(f"✅ Lokale Modell-Datei gelöscht: {local_path}")
            except Exception as e:
                logger.warning(f"⚠️ Fehler beim Löschen der lokalen Datei: {e}")
        elif local_path:
            logger.debug(f"ℹ️ Modell-Datei existiert nicht: {local_path}")

        # Lösche aus DB
        success = await delete_active_model(active_model_id)
        if not success:
            logger.error(f"❌ Fehler beim Löschen aus Datenbank: active_model_id {active_model_id}")
            raise HTTPException(status_code=404, detail=f"Modell {active_model_id} konnte nicht aus Datenbank gelöscht werden")

        logger.info(f"✅ Modell {active_model_id} erfolgreich gelöscht (model_id: {model_id})")
        return {
            "message": f"Modell {active_model_id} gelöscht",
            "active_model_id": active_model_id,
            "model_id": model_id,
            "model_name": model_name
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Fehler beim Löschen: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# Predictions Endpoints
# ============================================================

@router.post("/predict", response_model=PredictionResponse)
async def predict_endpoint(request: PredictRequest):
    """
    Manuelle Vorhersage für einen Coin.

    Macht Vorhersagen mit allen aktiven Modellen (oder nur bestimmten).
    """
    try:
        # Hole aktive Modelle (exakt wie in der Debug-Route)
        from app.database.models import get_active_models
        active_models = await get_active_models()
        logger.info(f"🔍 Predict: {len(active_models)} aktive Modelle gefunden für coin {request.coin_id}")

        if not active_models:
            logger.warning("⚠️ Predict: Keine aktiven Modelle gefunden")
            # Debug: Verwende direkten Pool-Zugriff
            pool = await get_pool()
            active_models = await get_active_models()
            logger.info(f"🔍 Predict: Nach direktem Pool-Zugriff: {len(active_models)} aktive Modelle gefunden")
            if not active_models:
                raise HTTPException(status_code=400, detail="Keine aktiven Modelle gefunden")
        
        # Filter nach model_ids (wenn angegeben)
        if request.model_ids:
            active_models = [m for m in active_models if m['model_id'] in request.model_ids]
            if not active_models:
                raise HTTPException(status_code=404, detail="Keine der angegebenen Modelle sind aktiv")
        
        # Timestamp (aktuell wenn nicht angegeben)
        timestamp = request.timestamp or datetime.now(timezone.utc)
        
        # Hole Pool für Vorhersagen
        pool = await get_pool()

        # Mache Vorhersagen
        results = await predict_coin_all_models(
            coin_id=request.coin_id,
            timestamp=timestamp,
            active_models=active_models,
            pool=pool
        )
        
        # Speichere Vorhersagen in DB (genau wie Event-Handler)
        if results:
            from app.database.models import save_model_prediction, get_coin_metrics_at_timestamp, update_coin_scan_cache
            
            # Hole Metriken für diesen Coin zum Zeitpunkt der Vorhersage
            metrics = await get_coin_metrics_at_timestamp(request.coin_id, timestamp, pool=pool)
            
            # Hole Phase-ID für diesen Coin (aus coin_metrics)
            phase_id = None
            if metrics:
                # Hole Phase-ID aus dem neuesten coin_metrics Eintrag
                phase_row = await pool.fetchrow("""
                    SELECT phase_id_at_time
                    FROM coin_metrics
                    WHERE mint = $1
                      AND timestamp <= $2
                    ORDER BY timestamp DESC
                    LIMIT 1
                """, request.coin_id, timestamp)
                if phase_row:
                    phase_id = phase_row['phase_id_at_time']
            
            for result in results:
                try:
                    model_id = result.get('active_model_id')
                    prediction = result['prediction']
                    probability = result['probability']
                    
                    # Finde das entsprechende Modell-Config
                    model_config = next((m for m in active_models if m.get('id') == model_id), None)
                    if not model_config:
                        logger.warning(f"⚠️ Modell-Config nicht gefunden für active_model_id={model_id}")
                        continue
                    
                    alert_threshold = model_config.get('alert_threshold', 0.7)
                    future_minutes = model_config.get('future_minutes', 10)
                    
                    # Speichere Vorhersage in DB
                    await save_model_prediction(
                        coin_id=request.coin_id,
                        prediction_timestamp=timestamp,
                        model_id=result['model_id'],
                        active_model_id=model_id,
                        prediction=prediction,
                        probability=probability,
                        alert_threshold=alert_threshold,
                        future_minutes=future_minutes,
                        metrics=metrics,
                        phase_id_at_time=phase_id,
                        pool=pool
                    )
                    
                    # Aktualisiere Cache (für Ignore-Logik)
                    await update_coin_scan_cache(
                        pool=pool,
                        coin_id=request.coin_id,
                        active_model_id=model_id,
                        prediction=prediction,
                        probability=probability,
                        alert_threshold=alert_threshold,
                        ignore_bad_seconds=model_config.get('ignore_bad_seconds', 0),
                        ignore_positive_seconds=model_config.get('ignore_positive_seconds', 0),
                        ignore_alert_seconds=model_config.get('ignore_alert_seconds', 0)
                    )
                    
                except Exception as e:
                    logger.error(f"❌ Fehler beim Speichern für Modell {model_id}: {e}", exc_info=True)
        
        # Sende Vorhersagen an n8n (genau wie Event-Handler)
        if results:
            from app.prediction.n8n_client import send_to_n8n
            logger.info(f"📤 Sende {len(results)} Vorhersagen an n8n (manueller Predict)")
            n8n_result = await send_to_n8n(
                coin_id=request.coin_id,
                timestamp=timestamp,
                predictions=results,
                active_models=active_models
            )
            logger.info(f"📤 n8n Ergebnis (manueller Predict): {n8n_result}")
        
        # Konvertiere zu Response-Format
        prediction_results = [
            PredictionResult(
                model_id=r['model_id'],
                active_model_id=r['active_model_id'],
                model_name=r['model_name'],
                prediction=r['prediction'],
                probability=r['probability']
            )
            for r in results
        ]
        
        return PredictionResponse(
            coin_id=request.coin_id,
            timestamp=timestamp,
            predictions=prediction_results,
            total_models=len(prediction_results)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Fehler bei Vorhersage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predictions", response_model=PredictionsListResponse)
async def get_predictions_endpoint(
    coin_id: Optional[str] = None,
    model_id: Optional[int] = None,
    active_model_id: Optional[int] = None,
    prediction: Optional[int] = None,  # 0 oder 1
    min_probability: Optional[float] = None,
    max_probability: Optional[float] = None,
    phase_id: Optional[int] = None,
    date_from: Optional[str] = None,  # ISO-Format String
    date_to: Optional[str] = None,  # ISO-Format String
    limit: int = 100,
    offset: int = 0
):
    """Liste aller Vorhersagen (mit Filtern)"""
    try:
        # Konvertiere ISO-Strings zu datetime
        date_from_dt = None
        if date_from:
            try:
                date_from_dt = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            except Exception as e:
                logger.warning(f"⚠️ Ungültiges date_from Format: {date_from}, Fehler: {e}")
        
        date_to_dt = None
        if date_to:
            try:
                date_to_dt = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            except Exception as e:
                logger.warning(f"⚠️ Ungültiges date_to Format: {date_to}, Fehler: {e}")
        
        predictions = await get_predictions(
            coin_id=coin_id,
            model_id=model_id,
            active_model_id=active_model_id,
            prediction=prediction,
            min_probability=min_probability,
            max_probability=max_probability,
            phase_id=phase_id,
            date_from=date_from_dt,
            date_to=date_to_dt,
            limit=limit,
            offset=offset
        )
        
        prediction_details = [
            PredictionDetail(
                id=p['id'],
                coin_id=p['coin_id'],
                data_timestamp=p['data_timestamp'],
                model_id=p['model_id'],
                active_model_id=p['active_model_id'],
                prediction=p['prediction'],
                probability=p['probability'],
                phase_id_at_time=p['phase_id_at_time'],
                features=p['features'],
                prediction_duration_ms=p['prediction_duration_ms'],
                created_at=p['created_at']
            )
            for p in predictions
        ]
        
        # TODO: Total count (später implementieren wenn nötig)
        total = len(prediction_details)
        
        return PredictionsListResponse(
            predictions=prediction_details,
            total=total,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(f"❌ Fehler beim Laden von Vorhersagen: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predictions/latest/{coin_id}", response_model=PredictionDetail)
async def get_latest_prediction_endpoint(coin_id: str, model_id: Optional[int] = None):
    """Neueste Vorhersage für einen Coin"""
    try:
        prediction = await get_latest_prediction(coin_id, model_id)
        if not prediction:
            raise HTTPException(status_code=404, detail=f"Keine Vorhersage für Coin {coin_id} gefunden")
        
        return PredictionDetail(
            id=prediction['id'],
            coin_id=prediction['coin_id'],
            data_timestamp=prediction['data_timestamp'],
            model_id=prediction['model_id'],
            active_model_id=prediction['active_model_id'],
            prediction=prediction['prediction'],
            probability=prediction['probability'],
            phase_id_at_time=prediction['phase_id_at_time'],
            features=prediction['features'],
            prediction_duration_ms=prediction['prediction_duration_ms'],
            created_at=prediction['created_at']
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Fehler beim Laden der neuesten Vorhersage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# System Endpoints
# ============================================================

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health Check (JSON mit Status, aktive Modelle, etc.)"""
    try:
        health = await get_health_status()
        return HealthResponse(**health)
    except Exception as e:
        logger.error(f"❌ Fehler beim Health Check: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics", response_class=PlainTextResponse)
async def metrics_endpoint():
    """Prometheus Metrics (Text-Format)"""
    try:
        metrics_bytes = generate_metrics()
        return Response(
            content=metrics_bytes,
            media_type="text/plain; version=0.0.4; charset=utf-8"
        )
    except Exception as e:
        logger.error(f"❌ Fehler beim Generieren der Metriken: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=StatsResponse)
async def stats_endpoint():
    """Statistiken"""
    try:
        from app.database.models import get_predictions
        from datetime import datetime, timedelta, timezone
        
        # Hole alle Vorhersagen (letzte Stunde)
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        predictions_last_hour = await get_predictions(limit=10000)
        predictions_last_hour_count = sum(
            1 for p in predictions_last_hour
            if p['created_at'] >= one_hour_ago
        )
        
        # Aktive Modelle
        active_models = await get_active_models()
        active_models_count = len(active_models)
        
        # Total Predictions (ungefähr)
        all_predictions = await get_predictions(limit=100000)
        total_predictions = len(all_predictions)
        
        # Zeitbasierte Statistiken (24h, 7d)
        one_day_ago = datetime.now(timezone.utc) - timedelta(days=1)
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        
        predictions_last_24h_count = sum(
            1 for p in all_predictions
            if p['created_at'] >= one_day_ago
        )
        
        predictions_last_7d_count = sum(
            1 for p in all_predictions
            if p['created_at'] >= seven_days_ago
        )
        
        # Coins tracked (unique coin_ids)
        unique_coins = len(set(p['coin_id'] for p in all_predictions))
        
        # Durchschnittliche Vorhersage-Dauer
        durations = [p.get('prediction_duration_ms') for p in all_predictions if p.get('prediction_duration_ms') is not None]
        avg_prediction_time_ms = sum(durations) / len(durations) if durations else None
        
        # Webhook-Statistiken
        from app.database.connection import get_pool
        pool = await get_pool()
        webhook_stats = await pool.fetchrow("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE response_status >= 200 AND response_status < 300) as success,
                COUNT(*) FILTER (WHERE response_status IS NULL OR response_status < 200 OR response_status >= 300) as failed
            FROM prediction_webhook_log
        """)
        
        webhook_total = webhook_stats['total'] if webhook_stats else 0
        webhook_success = webhook_stats['success'] if webhook_stats else 0
        webhook_failed = webhook_stats['failed'] if webhook_stats else 0
        
        return StatsResponse(
            total_predictions=total_predictions,
            predictions_last_hour=predictions_last_hour_count,
            predictions_last_24h=predictions_last_24h_count,
            predictions_last_7d=predictions_last_7d_count,
            active_models=active_models_count,
            coins_tracked=unique_coins,
            avg_prediction_time_ms=avg_prediction_time_ms,
            webhook_total=webhook_total,
            webhook_success=webhook_success,
            webhook_failed=webhook_failed
        )
    except Exception as e:
        logger.error(f"❌ Fehler beim Laden der Statistiken: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs", response_class=PlainTextResponse)
async def logs_endpoint(tail: int = 100):
    """
    Gibt die letzten N Log-Zeilen zurück.
    
    Liest die Logs aus dem Container (stdout/stderr via Supervisor).
    Da Supervisor die Logs an stdout/stderr weiterleitet, lesen wir sie über Docker.
    """
    try:
        import subprocess
        
        # Versuche Docker-Logs zu lesen (funktioniert wenn Docker verfügbar ist)
        try:
            # Prüfe ob wir im Container sind (HOSTNAME ist gesetzt)
            container_name = os.getenv("HOSTNAME", "ml-prediction-service")
            
            # Prüfe ob Docker verfügbar ist
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
                    return Response(
                        content=result.stdout,
                        media_type="text/plain"
                    )
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            # Docker nicht verfügbar - versuche Logs aus Datei zu lesen
            logger.debug(f"Docker nicht verfügbar: {e}")
        
        # Fallback: Versuche Logs aus Log-Dateien zu lesen
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
                        # Füge Log-Name hinzu
                        for line in lines:
                            all_logs.append((f"[{log_name}]", line))
            except Exception as e:
                logger.debug(f"Konnte Log-Datei {log_path} nicht lesen: {e}")
        
        if all_logs:
            # Neueste Logs zuerst (letzte tail Zeilen)
            recent_logs = all_logs[-tail:]
            # Kombiniere Logs
            combined_logs = [f"{name} {line}" for name, line in recent_logs]
            return Response(
                content="".join(combined_logs),
                media_type="text/plain"
            )
        
        # Letzter Fallback: Info-Message
        return Response(
            content=f"ℹ️ Keine Logs verfügbar.\n\n"
                   f"💡 Tipp: Logs können direkt mit `docker logs ml-prediction-service --tail {tail}` angezeigt werden.\n"
                   f"💡 Oder: Logs werden über stdout/stderr ausgegeben und sind im Docker-Container sichtbar.\n",
            media_type="text/plain"
        )
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Laden der Logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# Coolify-kompatible Endpoints (ohne /api Prefix)
# ============================================================

coolify_router = APIRouter(tags=["System"])

@coolify_router.get("/health", response_model=HealthResponse)
async def health_check_coolify():
    """Health Check für Coolify (ohne /api Prefix)"""
    return await health_check()

@coolify_router.get("/metrics", response_class=PlainTextResponse)
async def metrics_endpoint_coolify():
    """Metrics für Coolify (ohne /api Prefix)"""
    return await metrics_endpoint()


    """Health Check für Coolify (ohne /api Prefix)"""
    return await health_check()

@coolify_router.get("/metrics", response_class=PlainTextResponse)
async def metrics_endpoint_coolify():
    """Metrics für Coolify (ohne /api Prefix)"""
    return await metrics_endpoint()


# ============================================================
# Alerts Endpoints
# ============================================================

@router.get("/alerts/statistics")
async def get_alert_statistics_endpoint(
    model_id: Optional[int] = None,
    active_model_id: Optional[int] = None,  # NEU: Unterstützung für active_model_id
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None
):
    """Alert-Statistiken (NEUE ARCHITEKTUR: verwendet model_predictions)"""
    try:
        # Verwende active_model_id wenn gegeben, sonst model_id (für Kompatibilität)
        result = await get_alert_statistics(
            model_id=active_model_id or model_id, date_from=date_from, date_to=date_to
        )
        return result
    except Exception as e:
        logger.error(f"❌ Fehler beim Abrufen der Alert-Statistiken: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/alert-statistics")
async def get_models_alert_statistics_endpoint():
    """OPTIMIERT: Alert-Statistiken für alle aktiven Modelle (Batch-Query)"""
    try:
        result = await get_model_alert_statistics()
        return result
    except Exception as e:
        logger.error(f"❌ Fehler beim Abrufen der Modell-Alert-Statistiken: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/model-predictions")
async def get_model_predictions_endpoint(
    model_id: Optional[int] = None,
    active_model_id: Optional[int] = None,
    tag: Optional[str] = None,  # 'negativ', 'positiv', 'alert'
    status: Optional[str] = None,  # 'aktiv', 'inaktiv'
    coin_id: Optional[str] = None,
    # Neue erweiterte Filter
    probability_operator: Optional[str] = None,  # '>', '<', '='
    probability_value: Optional[float] = None,
    prediction_statuses: Optional[List[str]] = Query(None),  # ['negativ', 'positiv', 'alert']
    evaluation_statuses: Optional[List[str]] = Query(None),  # ['success', 'failed', 'wait']
    ath_highest_operator: Optional[str] = None,  # '>', '<', '='
    ath_highest_value: Optional[float] = None,
    ath_lowest_operator: Optional[str] = None,  # '>', '<', '='
    ath_lowest_value: Optional[float] = None,
    actual_change_operator: Optional[str] = None,  # '>', '<', '='
    actual_change_value: Optional[float] = None,
    alert_time_from: Optional[str] = None,
    alert_time_to: Optional[str] = None,
    evaluation_time_from: Optional[str] = None,
    evaluation_time_to: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    Hole alle Vorhersagen aus model_predictions - EINFACH, ohne UNION-Queries!
    """
    try:
        pool = await get_pool()
        
        conditions = []
        params = []
        param_idx = 1
        
        if model_id:
            conditions.append(f"model_id = ${param_idx}")
            params.append(model_id)
            param_idx += 1
        
        if active_model_id:
            conditions.append(f"active_model_id = ${param_idx}")
            params.append(active_model_id)
            param_idx += 1
        
        if tag:
            conditions.append(f"tag = ${param_idx}")
            params.append(tag)
            param_idx += 1
        
        if status:
            conditions.append(f"status = ${param_idx}")
            params.append(status)
            param_idx += 1
        
        if coin_id:
            conditions.append(f"coin_id = ${param_idx}")
            params.append(coin_id)
            param_idx += 1

        # Neue erweiterte Filter
        if probability_operator and probability_value is not None:
            operator_map = {'>': '>', '<': '<', '=': '='}
            if probability_operator in operator_map:
                conditions.append(f"probability {operator_map[probability_operator]} ${param_idx}")
                params.append(probability_value)
                param_idx += 1

        if prediction_statuses and len(prediction_statuses) > 0:
            placeholders = ', '.join([f"${param_idx + i}" for i in range(len(prediction_statuses))])
            conditions.append(f"tag IN ({placeholders})")
            params.extend(prediction_statuses)
            param_idx += len(prediction_statuses)

        if evaluation_statuses and len(evaluation_statuses) > 0:
            # Map evaluation statuses to database values
            status_map = {
                'success': 'success',
                'failed': 'failed',
                'wait': 'aktiv'  # 'wait' means still active/pending
            }
            db_statuses = [status_map.get(s, s) for s in evaluation_statuses if s in status_map]
            if db_statuses:
                if 'wait' in evaluation_statuses and 'aktiv' in db_statuses:
                    # For 'wait', include both 'aktiv' and NULL evaluation_result
                    conditions.append(f"(evaluation_result IS NULL OR status = 'aktiv')")
                else:
                    placeholders = ', '.join([f"${param_idx + i}" for i in range(len(db_statuses))])
                    conditions.append(f"evaluation_result IN ({placeholders})")
                    params.extend(db_statuses)
                    param_idx += len(db_statuses)

        if ath_highest_operator and ath_highest_value is not None:
            operator_map = {'>': '>', '<': '<', '=': '='}
            if ath_highest_operator in operator_map:
                conditions.append(f"ath_highest_pct {operator_map[ath_highest_operator]} ${param_idx}")
                params.append(ath_highest_value)
                param_idx += 1

        if ath_lowest_operator and ath_lowest_value is not None:
            operator_map = {'>': '>', '<': '<', '=': '='}
            if ath_lowest_operator in operator_map:
                conditions.append(f"ath_lowest_pct {operator_map[ath_lowest_operator]} ${param_idx}")
                params.append(ath_lowest_value)
                param_idx += 1

        if actual_change_operator and actual_change_value is not None:
            operator_map = {'>': '>', '<': '<', '=': '='}
            if actual_change_operator in operator_map:
                conditions.append(f"actual_price_change_pct {operator_map[actual_change_operator]} ${param_idx}")
                params.append(actual_change_value)
                param_idx += 1

        if alert_time_from:
            conditions.append(f"prediction_timestamp >= ${param_idx}")
            params.append(alert_time_from)
            param_idx += 1

        if alert_time_to:
            conditions.append(f"prediction_timestamp <= ${param_idx}")
            params.append(alert_time_to)
            param_idx += 1

        if evaluation_time_from:
            conditions.append(f"evaluation_timestamp >= ${param_idx}")
            params.append(evaluation_time_from)
            param_idx += 1

        if evaluation_time_to:
            conditions.append(f"evaluation_timestamp <= ${param_idx}")
            params.append(evaluation_time_to)
            param_idx += 1

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        # Hole Vorhersagen
        query = f"""
            SELECT * FROM model_predictions
            {where_clause}
            ORDER BY prediction_timestamp DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        
        params.extend([limit, offset])
        rows = await pool.fetch(query, *params)
        
        # Hole Gesamtanzahl
        count_query = f"SELECT COUNT(*) FROM model_predictions {where_clause}"
        count_params = params[:-2]  # Ohne limit und offset
        total = await pool.fetchval(count_query, *count_params) if count_params else await pool.fetchval(count_query)

        # Hole Modell-Ziel-Informationen (falls active_model_id angegeben)
        model_target = None
        if active_model_id:
            model_info = await pool.fetchrow("""
                SELECT price_change_percent, target_direction, alert_threshold
                FROM prediction_active_models
                WHERE id = $1
            """, active_model_id)

            if model_info:
                target_pct = model_info['price_change_percent']
                direction = model_info['target_direction']

                if target_pct:
                    if direction == 'up':
                        model_target = f'Mind. +{target_pct:.1f}% Preissteigerung'
                    elif direction == 'down':
                        model_target = f'Max. -{target_pct:.1f}% Preisreduktion'
                    else:
                        model_target = f'{target_pct:.1f}% ({direction})'
                else:
                    model_target = 'Kein Ziel definiert'

        return {
            "predictions": [dict(row) for row in rows],
            "model_target": model_target,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    
    except Exception as e:
        logger.error(f"❌ Fehler beim Abrufen von model_predictions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts")
async def get_alerts_endpoint(
    status: Optional[str] = None,
    model_id: Optional[int] = None,
    active_model_id: Optional[int] = None,  # NEU: Filter nach active_model_id
    coin_id: Optional[str] = None,
    prediction_type: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    unique_coins: bool = True,
    include_non_alerts: bool = False,  # NEU: Auch Vorhersagen unter Threshold anzeigen
    limit: int = 100,
    offset: int = 0
):
    """Liste aller Alerts mit Filtern. Wenn include_non_alerts=True, werden auch Vorhersagen unter dem Alert-Threshold angezeigt."""
    try:
        # Wenn active_model_id gegeben, konvertiere zu model_id
        if active_model_id and not model_id:
            pool = await get_db_pool()
            model_row = await pool.fetchrow("""
                SELECT model_id FROM prediction_active_models WHERE id = $1
            """, active_model_id)
            if model_row:
                model_id = model_row['model_id']
        
        result = await get_alerts(
            status=status, model_id=model_id, coin_id=coin_id,
            prediction_type=prediction_type, date_from=date_from, date_to=date_to,
            unique_coins=unique_coins, include_non_alerts=include_non_alerts,
            limit=limit, offset=offset
        )
        return result
    except Exception as e:
        logger.error(f"❌ Fehler beim Abrufen der Alerts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/{active_model_id}/coins/{coin_id}/details", response_model=CoinDetailsResponse)
async def get_coin_details_endpoint(
    active_model_id: int,
    coin_id: str,
    prediction_id: Optional[int] = None,  # NEU: Optional prediction_id für spezifische Vorhersage
    time_window_minutes: Optional[int] = None,  # Optional: Falls nicht gesetzt, wird automatisch berechnet
    time_offset_minutes: int = 0
):
    """
    Holt detaillierte Informationen für einen Coin inkl. Preis-Historie, Vorhersagen und Auswertungen.
    
    Args:
        active_model_id: ID des aktiven Modells
        coin_id: Coin-Mint-Adresse
        prediction_id: Optional: ID einer spezifischen Vorhersage (aus model_predictions)
                       Wenn gesetzt, wird Zeitraum automatisch berechnet: 10min vor prediction bis 10min nach evaluation
        time_window_minutes: Optional: Zeitfenster in Minuten (nur wenn prediction_id nicht gesetzt)
        time_offset_minutes: Offset in Minuten (nur wenn prediction_id nicht gesetzt)
    
    Returns:
        CoinDetailsResponse mit Preis-Historie, Vorhersagen und Auswertungen
    """
    try:
        pool = await get_pool()
        
        # NEU: Wenn prediction_id gesetzt, hole spezifische Vorhersage aus model_predictions
        if prediction_id:
            prediction_row = await pool.fetchrow("""
                SELECT 
                    prediction_timestamp,
                    evaluation_timestamp,
                    price_close_at_prediction
                FROM model_predictions
                WHERE id = $1
                  AND coin_id = $2
                  AND active_model_id = $3
            """, prediction_id, coin_id, active_model_id)
            
            if not prediction_row:
                raise HTTPException(
                    status_code=404,
                    detail=f"Vorhersage {prediction_id} für Coin {coin_id[:20]}... und Modell {active_model_id} nicht gefunden"
                )
            
            prediction_timestamp = prediction_row['prediction_timestamp']
            evaluation_timestamp = prediction_row['evaluation_timestamp']
            
            # Berechne Zeitraum: 10 Minuten vor prediction bis 10 Minuten nach evaluation
            start_timestamp = prediction_timestamp - timedelta(minutes=10)
            end_timestamp = evaluation_timestamp + timedelta(minutes=10)
            
            logger.info(f"📊 Coin-Details für {coin_id[:20]}... (Prediction ID: {prediction_id}) - Zeitraum: {start_timestamp} bis {end_timestamp}")
        else:
            # ALT: Finde erste Vorhersage für diesen Coin und Modell (aus predictions Tabelle für Rückwärtskompatibilität)
            first_prediction = await pool.fetchrow("""
                SELECT data_timestamp
                FROM predictions
                WHERE coin_id = $1
                  AND active_model_id = $2
                ORDER BY data_timestamp ASC
                LIMIT 1
            """, coin_id, active_model_id)
            
            if not first_prediction:
                raise HTTPException(
                    status_code=404,
                    detail=f"Keine Vorhersagen für Coin {coin_id[:20]}... und Modell {active_model_id} gefunden"
                )
            
            prediction_timestamp = first_prediction['data_timestamp']
            
            # Berechne Start- und End-Zeitpunkt
            # Start: 5 Minuten vor erster Vorhersage (Kontext) + Offset
            time_window = time_window_minutes or 60
            start_timestamp = prediction_timestamp - timedelta(minutes=5) + timedelta(minutes=time_offset_minutes)
            # End: Start + Zeitfenster
            end_timestamp = start_timestamp + timedelta(minutes=time_window)
            
            logger.info(f"📊 Coin-Details für {coin_id[:20]}... - Zeitfenster: {start_timestamp} bis {end_timestamp}")
        
        # Hole alle Daten parallel
        
        price_history = await get_coin_price_history(
            coin_id=coin_id,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp
        )
        
        logger.info(f"✅ Preis-Historie: {len(price_history)} Einträge")
        
        predictions = await get_coin_predictions_for_model(
            coin_id=coin_id,
            active_model_id=active_model_id,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp
        )
        
        logger.info(f"✅ Vorhersagen: {len(predictions)} Einträge")
        
        evaluations = await get_coin_evaluations_for_model(
            coin_id=coin_id,
            active_model_id=active_model_id,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp
        )
        
        logger.info(f"✅ Auswertungen: {len(evaluations)} Einträge")
        
        return CoinDetailsResponse(
            coin_id=coin_id,
            model_id=active_model_id,
            prediction_timestamp=prediction_timestamp,
            price_history=price_history,
            predictions=predictions,
            evaluations=evaluations
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Coin-Details für {coin_id} und Modell {active_model_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Abrufen der Coin-Details: {str(e)}"
        )

@router.get("/alerts/{alert_id}")
async def get_alert_details_endpoint(
    alert_id: int,
    chart_before_minutes: int = 10,
    chart_after_minutes: int = 10
):
    """Detaillierte Informationen zu einem Alert"""
    try:
        result = await get_alert_details(
            alert_id=alert_id,
            chart_before_minutes=chart_before_minutes,
            chart_after_minutes=chart_after_minutes
        )
        if not result:
            raise HTTPException(status_code=404, detail=f"Alert {alert_id} nicht gefunden")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Fehler beim Abrufen der Alert-Details: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/models/{active_model_id}/statistics")
async def reset_model_statistics_endpoint(active_model_id: int):
    """Setzt Statistiken für ein Modell zurück (löscht alle Vorhersagen)"""
    try:
        pool = await get_db_pool()
        
        # Prüfe ob Modell existiert
        model_row = await pool.fetchrow("""
            SELECT id FROM prediction_active_models WHERE id = $1
        """, active_model_id)
        
        if not model_row:
            raise HTTPException(status_code=404, detail=f"Modell {active_model_id} nicht gefunden")
        
        # Lösche alle Vorhersagen für dieses Modell
        deleted_count = await pool.execute("""
            DELETE FROM predictions WHERE active_model_id = $1
        """, active_model_id)
        
        # Setze total_predictions auf 0
        await pool.execute("""
            UPDATE prediction_active_models
            SET total_predictions = 0,
                last_prediction_at = NULL,
                updated_at = NOW()
            WHERE id = $1
        """, active_model_id)
        
        logger.info(f"✅ Statistiken für Modell {active_model_id} zurückgesetzt ({deleted_count} Vorhersagen gelöscht)")
        
        return {
            "success": True,
            "active_model_id": active_model_id,
            "deleted_predictions": deleted_count
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Fehler beim Zurücksetzen der Statistiken: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/model-predictions/{active_model_id}")
async def delete_model_predictions_endpoint(active_model_id: int):
    """Löscht alle Predictions für ein Modell (NEUE API)"""
    try:
        pool = await get_pool()
        
        # Prüfe ob Modell existiert
        model_row = await pool.fetchrow("""
            SELECT id FROM prediction_active_models WHERE id = $1
        """, active_model_id)
        
        if not model_row:
            raise HTTPException(status_code=404, detail=f"Modell {active_model_id} nicht gefunden")
        
        # Lösche alle Predictions für dieses Modell
        # WICHTIG: RETURNING COUNT(*) funktioniert nicht in DELETE - verwende RETURNING id
        # WICHTIG: Lösche ALLE Predictions (aktiv UND inaktiv), unabhängig vom Status!
        deleted_rows = await pool.fetch("""
            DELETE FROM model_predictions
            WHERE active_model_id = $1
            RETURNING id, status
        """, active_model_id)
        
        deleted_count = len(deleted_rows) if deleted_rows else 0
        
        # Zähle aktiv vs. inaktiv
        deleted_active = sum(1 for r in deleted_rows if r.get('status') == 'aktiv')
        deleted_inactive = sum(1 for r in deleted_rows if r.get('status') == 'inaktiv')
        
        logger.info(f"🗑️ {deleted_count} Predictions für Modell {active_model_id} gelöscht (Aktiv: {deleted_active}, Inaktiv: {deleted_inactive})")
        
        return {
            "success": True,
            "deleted_predictions": deleted_count
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Fehler beim Löschen der Predictions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/admin/delete-old-logs/{active_model_id}")
async def delete_old_logs_endpoint(active_model_id: int):
    """Löscht ALLE alten Logs (alert_evaluations und predictions) für ein Modell"""
    try:
        pool = await get_pool()
        
        # Prüfe ob Modell existiert
        model_row = await pool.fetchrow("""
            SELECT id, model_id FROM prediction_active_models WHERE id = $1
        """, active_model_id)
        
        if not model_row:
            raise HTTPException(status_code=404, detail=f"Modell {active_model_id} nicht gefunden")
        
        model_id = model_row['model_id']
        
        # Lösche aus alert_evaluations (alte Tabelle)
        # alert_evaluations hat prediction_id, nicht active_model_id direkt
        # Lösche über prediction_id -> predictions -> active_model_id
        deleted_alerts_rows = await pool.fetch("""
            DELETE FROM alert_evaluations
            WHERE prediction_id IN (
                SELECT id FROM predictions WHERE active_model_id = $1
            )
            RETURNING id
        """, active_model_id)
        deleted_alerts = len(deleted_alerts_rows) if deleted_alerts_rows else 0
        
        # Lösche aus predictions (alte Tabelle) - über active_model_id (direkt)
        deleted_predictions_rows = await pool.fetch("""
            DELETE FROM predictions
            WHERE active_model_id = $1
            RETURNING id
        """, active_model_id)
        deleted_predictions = len(deleted_predictions_rows) if deleted_predictions_rows else 0
        
        # Lösche auch aus model_predictions (neue Tabelle)
        # WICHTIG: Lösche ALLE Predictions (aktiv UND inaktiv), unabhängig vom Status!
        deleted_model_predictions_rows = await pool.fetch("""
            DELETE FROM model_predictions
            WHERE active_model_id = $1
            RETURNING id
        """, active_model_id)
        deleted_model_predictions = len(deleted_model_predictions_rows) if deleted_model_predictions_rows else 0
        
        logger.info(f"🗑️ {deleted_model_predictions} Predictions (aktiv + inaktiv) aus model_predictions gelöscht für Modell {active_model_id}")
        
        # Lösche auch alle Test/Demo-Einträge (coin_id beginnt mit "Test")
        deleted_test_rows = await pool.fetch("""
            DELETE FROM model_predictions
            WHERE coin_id LIKE 'Test%'
            RETURNING id
        """)
        deleted_test = len(deleted_test_rows) if deleted_test_rows else 0
        if deleted_test > 0:
            logger.info(f"🗑️ {deleted_test} Test/Demo-Einträge gelöscht")
        
        total_deleted = (deleted_alerts or 0) + (deleted_predictions or 0) + (deleted_model_predictions or 0) + deleted_test
        
        logger.info(f"🗑️ Alte Logs gelöscht für Modell {active_model_id}: {total_deleted} Einträge (alert_evaluations: {deleted_alerts or 0}, predictions: {deleted_predictions or 0}, model_predictions: {deleted_model_predictions or 0})")
        
        # WICHTIG: Prüfe ob wirklich ALLE gelöscht wurden
        remaining_count = await pool.fetchval("""
            SELECT COUNT(*) FROM model_predictions WHERE active_model_id = $1
        """, active_model_id)
        
        if remaining_count > 0:
            logger.warning(f"⚠️ Nach dem Löschen sind noch {remaining_count} Predictions für Modell {active_model_id} vorhanden! Das sollte nicht passieren.")
        else:
            logger.info(f"✅ Bestätigt: Alle Predictions für Modell {active_model_id} wurden gelöscht (0 verbleibend)")
        
        return {
            "success": True,
            "deleted_alert_evaluations": deleted_alerts or 0,
            "deleted_predictions": deleted_predictions or 0,
            "deleted_model_predictions": deleted_model_predictions or 0,
            "deleted_test_entries": deleted_test,
            "total_deleted": total_deleted
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Fehler beim Löschen der alten Logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/models/{active_model_id}/alerts")
async def delete_model_alerts_endpoint(active_model_id: int):
    """Löscht alle Alerts für ein Modell (ALTE API - für Rückwärtskompatibilität)"""
    try:
        pool = await get_db_pool()
        
        # Prüfe ob Modell existiert
        model_row = await pool.fetchrow("""
            SELECT id, model_id FROM prediction_active_models WHERE id = $1
        """, active_model_id)
        
        if not model_row:
            raise HTTPException(status_code=404, detail=f"Modell {active_model_id} nicht gefunden")
        
        model_id = model_row['model_id']
        
        # Lösche alle Alerts für dieses Modell (über prediction_id)
        deleted_count = await pool.execute("""
            DELETE FROM alert_evaluations
            WHERE prediction_id IN (
                SELECT id FROM predictions WHERE active_model_id = $1
            )
        """, active_model_id)
        
        logger.info(f"✅ Alerts für Modell {active_model_id} gelöscht ({deleted_count} Alerts gelöscht)")
        
        return {
            "success": True,
            "active_model_id": active_model_id,
            "deleted_alerts": deleted_count
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Fehler beim Löschen der Alerts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SYSTEM ROUTES
# ============================================================================

async def restart_service_async():
    """
    Asynchroner Service-Neustart (für automatischen Restart nach Config-Update).
    """
    import asyncio
    import signal
    import os
    
    # Warte kurz, damit die Response zurückgegeben werden kann
    await asyncio.sleep(1)
    
    logger.warning("🔄 Service-Neustart angefordert über API (automatisch)")
    
    # Sende SIGTERM an den aktuellen Prozess
    os.kill(os.getpid(), signal.SIGTERM)

@router.post("/system/restart", status_code=status.HTTP_200_OK)
async def restart_service():
    """
    Service-Neustart initiieren.

    Sendet ein SIGTERM Signal an den aktuellen Prozess, wodurch Supervisor
    den Service automatisch neu startet (--reload Flag erforderlich).
    """
    try:
        import signal
        import os

        logger.warning("🔄 Service-Neustart angefordert über API")

        # Sende SIGTERM an den aktuellen Prozess, um einen Graceful Shutdown zu initiieren
        # Wenn der Service mit --reload gestartet wurde, wird er automatisch neu gestartet
        os.kill(os.getpid(), signal.SIGTERM)

        return {
            "message": "Service wird neu gestartet... Bitte warten Sie einen Moment.",
            "requires_manual_restart": False,
            "auto_restart_enabled": True,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Fehler beim Service-Neustart: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config")
async def get_config():
    """
    Aktuelle persistente Konfiguration abrufen.
    """
    try:
        config = load_persistent_config()
        return {
            "success": True,
            "config": config,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Fehler beim Laden der Konfiguration: {e}")
        raise HTTPException(status_code=500, detail=f"Konfiguration konnte nicht geladen werden: {e}")

@router.post("/config")
async def update_config(config_update: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Persistente Konfiguration aktualisieren.
    """
    try:
        # Lade aktuelle Konfiguration
        current_config = load_persistent_config()

        # Aktualisiere mit neuen Werten
        updated_config = {**current_config, **config_update}

        # Validiere wichtige Felder
        if "database_url" in updated_config and not updated_config["database_url"].startswith("postgresql://"):
            raise HTTPException(status_code=400, detail="Datenbank-URL muss mit 'postgresql://' beginnen")

        if "training_service_url" in updated_config and not updated_config["training_service_url"].startswith("http"):
            raise HTTPException(status_code=400, detail="Training-Service-URL muss mit 'http' beginnen")

        # Speichere neue Konfiguration
        if save_persistent_config(updated_config):
            logger.info("✅ Konfiguration erfolgreich aktualisiert")
            
            # Aktualisiere in-memory config (wird beim Neustart neu geladen)
            # Die Config wird beim Neustart automatisch aus der Datei geladen
            
            # Starte Service automatisch neu (als Background Task, damit Response zurückgegeben werden kann)
            background_tasks.add_task(restart_service_async)
            
            return {
                "success": True,
                "message": "Konfiguration wurde gespeichert. Service wird automatisch neu gestartet.",
                "config": updated_config,
                "requires_restart": False,
                "auto_restart": True,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Konfiguration konnte nicht gespeichert werden")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Fehler beim Aktualisieren der Konfiguration: {e}")
        raise HTTPException(status_code=500, detail=f"Konfiguration konnte nicht aktualisiert werden: {e}")

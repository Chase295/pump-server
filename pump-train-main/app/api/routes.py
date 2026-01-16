"""
FastAPI Routes für ML Training Service
"""
import os
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Response, status, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.responses import FileResponse
from app.api.schemas import (
    SimpleTrainModelRequest, SimpleTimeBasedRequest, TrainModelRequest,
    TestModelRequest, UpdateModelRequest, CompareModelsRequest,
    ModelResponse, TestResultResponse, ComparisonResponse,
    JobResponse, CreateJobResponse, HealthResponse,
    ConfigResponse, ConfigUpdateRequest, ConfigUpdateResponse
)
from app.database.models import (
    create_model, get_model, update_model, list_models, delete_model,
    create_test_result, get_test_result, get_test_results, list_all_test_results, delete_test_result,
    create_comparison, get_comparison, list_comparisons, delete_comparison,
    create_job, get_job, list_jobs,
    get_coin_phases, get_all_available_features
)
from app.database.connection import get_pool
from app.training.engine import train_model
from app.training.model_loader import test_model
from app.utils.metrics import get_health_status, generate_metrics
from app.utils.config import MODEL_STORAGE_PATH
from app.utils.exceptions import (
    ModelNotFoundError, InvalidModelParametersError, DatabaseError,
    JobNotFoundError, JobProcessingError, TrainingError, TestError,
    ComparisonError, DataError, ValidationError, MLTrainingError
)
from app.utils.logging_config import get_logger, log_with_context, get_request_id

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["ML Training Service"])

# ============================================================
# Models Endpoints
# ============================================================

@router.post("/models/create/simple", response_model=CreateJobResponse, status_code=status.HTTP_201_CREATED)
async def create_simple_model_job(request: SimpleTrainModelRequest):
    """
    Erstellt einen TRAIN-Job mit vereinfachter regelbasierter Vorhersage

    🎯 Einfache Alternative zu /models/create
    Verwende stattdessen: /models/create/simple

    Beispiel:
    ```json
    {
      "name": "MyModel",
      "model_type": "xgboost",
      "target": "price_close > 0.05",
      "features": "auto",
      "train_start": "2025-12-27T16:00:00Z",
      "train_end": "2025-12-27T18:00:00Z"
    }
    ```
    """
    try:
        # Parse die Ziel-Regel
        var, op, val_str = request.target.split()
        target_value = float(val_str)

        # Erstelle vollständigen TrainModelRequest
        full_request = TrainModelRequest(
            name=request.name,
            model_type=request.model_type,
            use_time_based_prediction=False,  # Regelbasierte Vorhersage
            target_var=var,
            operator=op,
            target_value=target_value,
            features=request.features,
            train_start=request.train_start,
            train_end=request.train_end,
            description=request.description,
            params=request.hyperparameters,
            validation_split=request.validation_split
        )

        # Verwende die bestehende Logik
        return await create_model_job(full_request)

    except Exception as e:
        logger.error(f"Fehler bei vereinfachter Modell-Erstellung: {e}")
        raise HTTPException(status_code=400, detail=f"Fehler bei vereinfachter Modell-Erstellung: {str(e)}")


@router.post("/models/create/simple/time-based", response_model=CreateJobResponse, status_code=status.HTTP_201_CREATED)
async def create_simple_time_based_model(
    name: str,
    model_type: str,
    future_minutes: str,
    min_percent_change: str,
    direction: str,
    features: Optional[str] = None,
    train_start: Optional[str] = None,
    train_end: Optional[str] = None
):
    """
    Erstellt ein einfaches zeitbasiertes ML-Modell (vereinfachte Parameter)

    **Parameter:**
    - `name`: Modell-Name
    - `model_type`: "xgboost" oder "random_forest"
    - `future_minutes`: Minuten in die Zukunft (z.B. 10)
    - `min_percent_change`: Mindest-Preisänderung in Prozent (z.B. 7.0 für 7%)
    - `direction`: "up" oder "down"
    - `features`: Kommaseparierte Liste der Features (Default: "price_close,volume_sol")
    - `train_start`: Start-Zeitpunkt (ISO-Format, Default: 1h ago)
    - `train_end`: Ende-Zeitpunkt (ISO-Format, Default: now)

    **Beispiel:**
    ```json
    {
      "name": "MemeCoin_TimeBased_7pct_10min",
      "model_type": "xgboost",
      "future_minutes": 10,
      "min_percent_change": 7.0,
      "direction": "up",
      "features": "price_close,volume_sol,market_cap_close",
      "train_start": "2025-12-31T10:00:00Z",
      "train_end": "2025-12-31T11:00:00Z"
    }
    ```
    """
    """
    Erstellt ein einfaches zeitbasiertes ML-Modell (vereinfachte Parameter)

    **Parameter:**
    - `name`: Modell-Name
    - `model_type`: "xgboost" oder "random_forest"
    - `future_minutes`: Minuten in die Zukunft (z.B. 10)
    - `min_percent_change`: Mindest-Preisänderung in Prozent (z.B. 5.0 für 5%)
    - `direction`: "up" oder "down"
    - `features`: Liste der Features (Default: ["price_close", "volume_sol"])
    - `train_start`: Start-Zeitpunkt (ISO-Format, Default: 1h ago)
    - `train_end`: Ende-Zeitpunkt (ISO-Format, Default: now)

    **Beispiel:**
    ```json
    {
      "name": "MemeCoin_TimeBased_7pct_10min",
      "model_type": "xgboost",
      "future_minutes": 10,
      "min_percent_change": 7.0,
      "direction": "up",
      "features": ["price_close", "volume_sol"],
      "train_start": "2025-12-31T10:00:00Z",
      "train_end": "2025-12-31T11:00:00Z"
    }
    ```
    """
    try:
        # Validiere und konvertiere Parameter
        try:
            future_minutes_int = int(future_minutes)
            if future_minutes_int <= 0:
                raise ValueError("future_minutes muss > 0 sein")
        except ValueError:
            raise HTTPException(status_code=400, detail=f"future_minutes muss eine positive ganze Zahl sein, nicht: {future_minutes}")

        try:
            min_percent_change_float = float(min_percent_change)
            if min_percent_change_float <= 0 or min_percent_change_float > 100:
                raise ValueError("min_percent_change muss zwischen 0 und 100 liegen")
        except ValueError:
            raise HTTPException(status_code=400, detail=f"min_percent_change muss zwischen 0 und 100 liegen, nicht: {min_percent_change}")

        if direction not in ["up", "down"]:
            raise HTTPException(status_code=400, detail=f"direction muss 'up' oder 'down' sein, nicht: {direction}")

        if model_type not in ["xgboost", "random_forest"]:
            raise HTTPException(status_code=400, detail=f"model_type muss 'xgboost' oder 'random_forest' sein, nicht: {model_type}")

        # Parse features (kommaseparierte Liste oder None)
        if features is None:
            features_list = ["price_close", "volume_sol"]
        elif isinstance(features, str):
            if features.lower().strip() == "auto":
                # Schritt-für-Schritt alle verfügbaren Features validieren
                from app.database.connection import get_pool

                try:
                    pool = await get_pool()
                    async with pool.acquire() as conn:
                        # Teste eine kleine Datenmenge (1 Stunde)
                        test_start = "2025-12-31T10:00:00Z"
                        test_end = "2025-12-31T11:00:00Z"

                        # Hole eine Beispiel-Zeile um verfügbare Spalten zu testen
                        sample_query = f"""
                        SELECT * FROM coin_data
                        WHERE timestamp >= '{test_start}'::timestamptz
                        AND timestamp <= '{test_end}'::timestamptz
                        LIMIT 1
                        """
                        sample_row = await conn.fetchrow(sample_query)

                        if sample_row:
                            # Teste alle potenziellen Features systematisch
                            candidate_features = [
                                # Basis OHLC (immer verfügbar)
                                "price_open", "price_high", "price_low", "price_close",
                                "volume_sol", "market_cap_close",

                                # Erweiterte Features (testen)
                                "buy_volume_sol", "sell_volume_sol", "net_volume_sol",
                                "dev_sold_amount", "buy_pressure_ratio", "unique_signer_ratio",
                                "whale_buy_volume_sol", "whale_sell_volume_sol",
                                "volatility_pct", "avg_trade_size_sol", "phase_id_at_time",

                                # ATH Features (testen)
                                "ath_price_sol", "price_vs_ath_pct", "minutes_since_ath"
                            ]

                            valid_features = []
                            for feature in candidate_features:
                                if feature in sample_row and sample_row[feature] is not None:
                                    # Zusätzliche Validierung: Prüfe ob numerisch
                                    try:
                                        val = float(sample_row[feature])
                                        if not (val != val):  # NaN check
                                            valid_features.append(feature)
                                    except (ValueError, TypeError):
                                        continue

                            features_list = valid_features
                            logger.info(f"✅ AUTO-Mode validiert: {len(features_list)} von {len(candidate_features)} Features verfügbar")
                            logger.info(f"📊 Verfügbare Features: {features_list}")

                        else:
                            # Fallback wenn keine Daten
                            features_list = ["price_close", "volume_sol", "market_cap_close"]
                            logger.warning("⚠️ Keine Test-Daten gefunden, verwende Fallback-Features")

                except Exception as e:
                    logger.error(f"❌ Fehler bei Feature-Validierung: {e}")
                    features_list = ["price_close", "volume_sol", "market_cap_close"]
                    logger.warning("🔄 Fallback wegen DB-Fehler")
            else:
                features_list = [f.strip() for f in features.split(",") if f.strip()]
        else:
            features_list = features

        # Verwende Standard-Zeitbereich wenn nicht angegeben
        if train_start is None or train_end is None:
            from datetime import datetime, timezone, timedelta
            now = datetime.now(timezone.utc)
            if train_end is None:
                train_end = now.isoformat()
            if train_start is None:
                train_start = (now - timedelta(hours=1)).isoformat()

        # Verwende Standard-Zeitbereich wenn nicht angegeben
        if train_start is None or train_end is None:
            from datetime import datetime, timezone, timedelta
            now = datetime.now(timezone.utc)
            if train_end is None:
                train_end = now.isoformat()
            if train_start is None:
                train_start = (now - timedelta(hours=1)).isoformat()

        # Konvertiere datetime-Strings zu datetime-Objekten für create_job
        from datetime import datetime, timezone
        train_start_dt = train_start
        train_end_dt = train_end
        if isinstance(train_start_dt, str):
            train_start_dt = datetime.fromisoformat(train_start_dt.replace('Z', '+00:00'))
        if isinstance(train_end_dt, str):
            train_end_dt = datetime.fromisoformat(train_end_dt.replace('Z', '+00:00'))
        if train_start_dt.tzinfo is None:
            train_start_dt = train_start_dt.replace(tzinfo=timezone.utc)
        if train_end_dt.tzinfo is None:
            train_end_dt = train_end_dt.replace(tzinfo=timezone.utc)

        # Verwende target_var aus Parametern oder Default
        target_var = target_var if 'target_var' in locals() and target_var else "price_close"

        # Aktiviere Feature-Engineering für auto-Modus
        use_engineered = True if features.lower().strip() == "auto" else False

        # Erstelle vollständigen TrainModelRequest
        full_request = TrainModelRequest(
            name=name,
            model_type=model_type,
            use_time_based_prediction=True,  # Zeitbasierte Vorhersage
            use_engineered_features=use_engineered,  # Feature-Engineering aktivieren für auto
            features=features_list,
            future_minutes=future_minutes_int,
            min_percent_change=min_percent_change_float,
            direction=direction,
            train_start=train_start_dt,
            train_end=train_end_dt,
            target_var=target_var,  # Erforderlich für zeitbasierte Vorhersage
            operator=None,    # Nicht verwendet bei zeitbasierter Vorhersage
            target_value=None # Nicht verwendet bei zeitbasierter Vorhersage
        )

        # Automatische Label-Anpassung bei Problemen
        try:
            return await create_model_job(full_request)
        except HTTPException as e:
            # Wenn es ein Label-Problem ist, automatisch eine schwächere Bedingung versuchen
            if "Labels sind nicht ausgewogen" in str(e.detail) and "Keine positiven Labels" in str(e.detail):
                logger.warning(f"⚠️ Label-Problem erkannt: {e.detail}")
                logger.info(f"🔧 Versuche automatisch mit schwächerer Bedingung: {min_percent_change/2}% statt {min_percent_change}%")

                # Erstelle neue Request mit schwächerer Bedingung
                fallback_request = TrainModelRequest(
                    name=f"{name}_auto_adjusted",
                    model_type=model_type,
                    use_time_based_prediction=True,
                    features=features_list,
                    future_minutes=future_minutes_int,
                    min_percent_change=min_percent_change_float/2,  # Halbiere die Bedingung
                    direction=direction,
                    train_start=train_start_dt,
                    train_end=train_end_dt,
                    target_var=None,
                    operator=None,
                    target_value=None
                )

                logger.info("🔄 Erstelle Job mit automatisch angepasster Bedingung...")
                return await create_model_job(fallback_request)
            else:
                # Andere Fehler weiterwerfen
                raise

    except Exception as e:
        logger.error(f"Fehler bei zeitbasierter Modell-Erstellung: {e}")
        raise HTTPException(status_code=400, detail=f"Fehler bei zeitbasierter Modell-Erstellung: {str(e)}")


@router.post("/models/create/time-based", response_model=CreateJobResponse, status_code=status.HTTP_201_CREATED)
async def create_time_based_model_job(
    name: str,
    model_type: str,
    target_var: str = "market_cap_close",
    future_minutes: int = 15,
    min_percent_change: float = 0.05,
    direction: str = "both",
    features: List[str] = None,
    train_start: datetime = None,
    train_end: datetime = None,
    hyperparameters: Optional[Dict[str, Any]] = None
):
    """
    Erstellt einen TRAIN-Job mit zeitbasierter Vorhersage (wie in der UI)

    🎯 Zeitbasierte Vorhersage: "Wird die Variable X in Y Minuten um Z% steigen?"

    Beispiel:
    ```json
    {
      "name": "TimeBased_Model",
      "model_type": "xgboost",
      "target_var": "market_cap_close",
      "future_minutes": 15,
      "min_percent_change": 0.05,
      "direction": "both",
      "features": ["price_open", "price_high", "price_low", "price_close"],
      "train_start": "2025-12-27T16:00:00Z",
      "train_end": "2025-12-27T18:00:00Z"
    }
    ```
    """
    try:
        # Verwende Standard-Features wenn keine angegeben
        if features is None:
            features = ["price_open", "price_high", "price_low", "price_close", "volume_sol", "market_cap_close"]

        # Verwende aktuelle Zeit als Default falls keine Zeiten angegeben
        if train_start is None or train_end is None:
            from datetime import datetime, timezone, timedelta
            now = datetime.now(timezone.utc)
            if train_end is None:
                train_end = now
            if train_start is None:
                train_start = train_end - timedelta(hours=2)  # 2 Stunden vorher

        # Erstelle vollständigen TrainModelRequest
        full_request = TrainModelRequest(
            name=name,
            model_type=model_type,
            use_time_based_prediction=True,  # Zeitbasierte Vorhersage
            target_var=target_var,
            operator=None,
            target_value=None,
            future_minutes=future_minutes,
            min_percent_change=min_percent_change,
            direction=direction,
            features=features,
            train_start=train_start,
            train_end=train_end,
            params=hyperparameters
        )

        # Verwende die bestehende Logik
        return await create_model_job(full_request)

    except Exception as e:
        logger.error(f"Fehler bei zeitbasierter Modell-Erstellung: {e}")
        raise HTTPException(status_code=400, detail=f"Fehler bei zeitbasierter Modell-Erstellung: {str(e)}")


@router.post("/models/create/advanced", response_model=CreateJobResponse, status_code=status.HTTP_201_CREATED)
async def create_model_job_advanced_endpoint(
    name: str,
    model_type: str,
    features: str,  # Komma-separiert
    target_var: str = "price_close",
    use_time_based_prediction: bool = True,
    future_minutes: int = 5,
    min_percent_change: float = 2.0,
    direction: str = "up",
    train_start: str = "2026-01-06T10:00:00Z",
    train_end: str = "2026-01-06T10:05:00Z",
    use_engineered_features: bool = False,  # Feature Engineering aktivieren
    use_flag_features: bool = Query(True, description="Flag-Features aktivieren? (Standard: true)"),  # NEU: Flag-Features
    use_smote: bool = False,  # SMOTE für unbalancierte Daten
    # ⚖️ Flexible Gewichtungs-Parameter
    scale_pos_weight: float = None,  # XGBoost: Gewicht für positive Klasse (z.B. 100 für 1% Labels)
    class_weight: str = None,  # "balanced" oder None - für Random Forest
    # 🔄 Coin-Phasen Filter (NEU!)
    phases: str = None  # Komma-separiert: z.B. "1,2,3" für Phase 1, 2 und 3
):
    """
    🚀 ADVANCED MODEL CREATION - Vollständig konfigurierbarer Endpoint
    
    Dieser Endpoint bietet maximale Flexibilität beim Erstellen von ML-Modellen.
    
    📊 FEATURES:
    - Zeitbasierte Vorhersage (z.B. "+5% in 10 Minuten")
    - Feature Engineering (66 zusätzliche Features)
    - SMOTE für unbalancierte Daten
    - scale_pos_weight für XGBoost
    
    ⚖️ BALANCE-OPTIONEN:
    - use_smote: Synthetische Oversampling (⚠️ kann zu Overfitting führen)
    - scale_pos_weight: XGBoost-intern, besser für stark unbalancierte Daten
      → Bei 1% positiven Labels: scale_pos_weight ≈ 100
      → Bei 5% positiven Labels: scale_pos_weight ≈ 20
    - class_weight: "balanced" für Random Forest
    
    📝 BEISPIEL:
    POST /api/models/create/advanced?name=PumpDetector&model_type=xgboost&features=price_close,volume_sol&future_minutes=10&min_percent_change=15&use_engineered_features=true&scale_pos_weight=100
    """
    print(f"🚀 ADVANCED ENDPOINT: {name}, {model_type}, features={features}, engineering={use_engineered_features}, smote={use_smote}, scale_pos_weight={scale_pos_weight}")

    # Baue einfaches Request-Objekt
    from app.api.schemas import TrainModelRequest
    from datetime import datetime

    try:
        # Baue params Dictionary für XGBoost-Optionen
        custom_params = {}
        if scale_pos_weight is not None:
            custom_params['scale_pos_weight'] = scale_pos_weight
        if class_weight is not None:
            custom_params['class_weight'] = class_weight
        # NEU: Flag-Features zu params hinzufügen (IMMER, auch wenn andere Parameter nicht gesetzt sind)
        custom_params['use_flag_features'] = use_flag_features
        logger.info(f"🚩 use_flag_features in custom_params gesetzt: {use_flag_features}")
        
        # 🔄 Phasen parsen (falls angegeben)
        parsed_phases = None
        if phases:
            try:
                parsed_phases = [int(p.strip()) for p in phases.split(',')]
                print(f"   📍 Phases: {parsed_phases}")
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Ungültiges phases Format: '{phases}'. Verwende z.B. '1,2,3'")
        
        request = TrainModelRequest(
            name=name,
            model_type=model_type,
            features=features.split(',') if features else ['price_close'],
            train_start=datetime.fromisoformat(train_start.replace('Z', '+00:00')),
            train_end=datetime.fromisoformat(train_end.replace('Z', '+00:00')),
            use_time_based_prediction=use_time_based_prediction,
            future_minutes=future_minutes,
            min_percent_change=min_percent_change,
            direction=direction,
            target_var=target_var,
            use_engineered_features=use_engineered_features,
            use_smote=use_smote,
            phases=parsed_phases,  # 🔄 Coin-Phasen Filter
            params=custom_params if custom_params else None  # ⚖️ XGBoost-Parameter
        )

        print(f"✅ Request erstellt: {request.name}")
        result = await create_model_job(request)
        print(f"✅ Job erstellt: {result}")
        return result

    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Debug-Fehler: {str(e)}")
    """
    Erstellt einen TRAIN-Job für ML-Modell-Training
    """
    # DEBUG: Logging VOR try-catch
    print(f"🚀 DEBUG: create_model_job_endpoint called with name={request.name}")

    try:
        # DEBUG: Sofortiges Logging bei Request-Eingang
        logger.info(f"📨 API REQUEST: create_model_job_endpoint - name={request.name}")
        logger.info(f"📊 Request data: model_type={request.model_type}, features={len(request.features) if request.features else 0}, time_based={request.use_time_based_prediction}")

        result = await create_model_job(request)
        logger.info(f"✅ API REQUEST erfolgreich abgeschlossen")
        return result

    except Exception as e:
        # DETAILLIERTES ERROR LOGGING
        print(f"💥 DEBUG: Exception in endpoint: {e}")
        logger.error(f"💥 API ENDPOINT FEHLER: {e}")
        logger.error(f"📋 Request: name={request.name}, model_type={request.model_type}")
        logger.error(f"🎯 Features: {request.features}")
        logger.error(f"⏰ Time-based: {request.use_time_based_prediction}")

        import traceback
        tb = traceback.format_exc()
        print(f"🔍 DEBUG TRACEBACK: {tb}")
        logger.error(f"🔍 TRACEBACK: {tb}")

        # Re-raise für FastAPI Error Handling
        raise HTTPException(status_code=500, detail=f"API-Fehler: {str(e)}")

async def validate_data_availability(train_start: str, train_end: str):
    """
    Prüft ob Daten im angegebenen Zeitraum verfügbar sind
    Verhinderte "Keine Trainingsdaten gefunden!" Fehler
    """
    try:
        pool = await get_pool()

        # Konvertiere Zeitstempel
        start_dt = datetime.fromisoformat(train_start.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(train_end.replace('Z', '+00:00'))

        # Prüfe Datenverfügbarkeit (einfache Count-Abfrage)
        async with pool.acquire() as conn:
            count_result = await conn.fetchrow("""
                SELECT COUNT(*) as total_rows,
                       COUNT(DISTINCT mint) as unique_coins,
                       MIN(timestamp) as min_time,
                       MAX(timestamp) as max_time
                FROM coin_metrics
                WHERE timestamp >= $1 AND timestamp <= $2
            """, start_dt, end_dt)

        total_rows = count_result['total_rows']
        unique_coins = count_result['unique_coins']

        if total_rows == 0:
            # Detaillierte Fehlermeldung mit verfügbarem Datenbereich
            available_result = await conn.fetchrow("""
                SELECT MIN(timestamp) as min_time, MAX(timestamp) as max_time
                FROM coin_data
            """)

            min_available = available_result['min_time']
            max_available = available_result['max_time']

            error_msg = (
                f"Keine Daten im Zeitraum {train_start} bis {train_end} gefunden!\n"
                f"Verfügbare Daten: {min_available} bis {max_available}\n"
                f"Empfehlung: Verwende einen Zeitraum innerhalb des verfügbaren Bereichs."
            )
            logger.error(error_msg)
            raise HTTPException(status_code=400, detail=error_msg)

        # Warnung bei wenig Daten
        if total_rows < 100:
            logger.warning(f"⚠️ Wenig Daten gefunden: {total_rows} Zeilen, {unique_coins} Coins")
        else:
            logger.info(f"✅ Daten verfügbar: {total_rows} Zeilen, {unique_coins} Coins")

    except HTTPException:
        raise  # Re-raise HTTPException
    except Exception as e:
        logger.error(f"Fehler bei Datenverfügbarkeitsprüfung: {e}")
        # Bei Datenbankfehlern trotzdem fortfahren (Fallback)
        logger.warning("Datenverfügbarkeitsprüfung fehlgeschlagen - fahre trotzdem fort")


async def create_model_job(request: TrainModelRequest):
    """
    Erstellt einen TRAIN-Job (Modell wird asynchron trainiert)

    ⚠️ WICHTIG: Modell wird NICHT sofort erstellt!
    Job wird in Queue eingereiht und später vom Worker verarbeitet.
    """
    # DEBUG: Sofortiges Logging am Anfang
    logger.info(f"🚀 create_model_job gestartet: {request.name}")
    logger.info(f"📊 Request: model_type={request.model_type}, features={request.features}, time_based={request.use_time_based_prediction}")

    try:
        # Parameter-Validierung (inline)
        errors = []

        # 1. Zeitbasierte vs regelbasierte Validierung
        if request.use_time_based_prediction:
            # Zeitbasierte Vorhersage: Pflichtfelder prüfen
            if request.future_minutes is None or request.future_minutes <= 0:
                errors.append("future_minutes muss > 0 sein bei zeitbasierter Vorhersage")
            if request.min_percent_change is None or request.min_percent_change <= 0:
                errors.append("min_percent_change muss > 0 sein bei zeitbasierter Vorhersage")
            if request.direction not in ["up", "down"]:
                errors.append("direction muss 'up' oder 'down' sein")
            # target_var wird automatisch auf 'price_close' gesetzt bei zeitbasierter Vorhersage
        else:
            # Regelbasierte Vorhersage wird nicht mehr unterstützt
            errors.append("Nur zeitbasierte Vorhersage wird unterstützt. Setze use_time_based_prediction=true")

        # 2. Zeitbereich prüfen (vernünftige Länge)
        if request.train_start and request.train_end:
            # request.train_start und request.train_end sind bereits datetime Objekte
            start = request.train_start
            end = request.train_end
            duration_hours = (end - start).total_seconds() / 3600

            if duration_hours < 0.083:  # Weniger als 5 Minuten
                errors.append(f"Trainingszeitraum zu kurz: {duration_hours:.1f}h (Minimum: 0.083h = 5 Minuten)")
            elif duration_hours > 24 * 30:  # Mehr als 30 Tage
                errors.append(f"Trainingszeitraum zu lang: {duration_hours:.1f}h (Maximum: 720h)")

        # 3. Features prüfen
        if not request.features:
            errors.append("features Liste darf nicht leer sein")
        else:
            # Ungültige Features prüfen (auto ist jetzt erlaubt)
            invalid_features = []  # Keine ungültigen Features mehr
            for feature in request.features:
                if feature in invalid_features:
                    errors.append(f"Ungültiges Feature: '{feature}'")

        # 4. Modelltyp prüfen
        if request.model_type not in ["xgboost", "random_forest"]:
            errors.append(f"model_type muss 'xgboost' oder 'random_forest' sein, nicht: {request.model_type}")

        # 5. CV-Splits prüfen
        if request.cv_splits is not None:
            if not (2 <= request.cv_splits <= 10):
                errors.append(f"cv_splits muss zwischen 2 und 10 liegen, nicht: {request.cv_splits}")

        # Fehler ausgeben falls vorhanden
        if errors:
            error_msg = f"Parameter-Validierung fehlgeschlagen ({len(errors)} Fehler):\n" + "\n".join(f"- {err}" for err in errors)
            raise HTTPException(status_code=400, detail=error_msg)

        # 🔍 Datenverfügbarkeit prüfen (deaktiviert für Debugging)
        # await validate_data_availability(request.train_start, request.train_end)
        # Erstelle Job in ml_jobs mit job_type: TRAIN
        # Modell-Name wird in progress_msg temporär gespeichert
        
        # NEU: Zeitbasierte Parameter in train_params speichern (falls aktiviert)
        final_params = request.params or {}
        if request.use_time_based_prediction:
            # Speichere zeitbasierte Parameter in train_params
            logger.info(f"DEBUG: use_time_based_prediction=True, min_percent_change={request.min_percent_change}")
            final_params = {
                **final_params,
                "_time_based": {
                    "enabled": True,
                    "future_minutes": request.future_minutes,
                    "min_percent_change": request.min_percent_change,
                    "direction": request.direction
                }
            }
        
        # NEU: Feature-Engineering Parameter hinzufügen
        if request.use_engineered_features:
            final_params['use_engineered_features'] = True
            if request.feature_engineering_windows:
                final_params['feature_engineering_windows'] = request.feature_engineering_windows
            else:
                final_params['feature_engineering_windows'] = [5, 10, 15]  # Default
        
        # NEU: SMOTE Parameter
        if not request.use_smote:
            final_params['use_smote'] = False
        
        # NEU: TimeSeriesSplit Parameter
        if not request.use_timeseries_split:
            final_params['use_timeseries_split'] = False
        if request.cv_splits:
            final_params['cv_splits'] = request.cv_splits
        
        # NEU: Marktstimmung Parameter (Phase 2)
        if request.use_market_context:
            final_params['use_market_context'] = True
        
        # NEU: Feature-Ausschluss Parameter (Phase 2)
        if request.exclude_features:
            final_params['exclude_features'] = request.exclude_features
        
        # NEU: use_flag_features aus params extrahieren (falls vorhanden)
        use_flag_features = final_params.get('use_flag_features', True)  # Standard: True
        
        # ✅ FIX: Bei zeitbasierter Vorhersage automatisch target_var setzen
        effective_target_var = request.target_var
        if request.use_time_based_prediction and not effective_target_var:
            effective_target_var = 'price_close'
            logger.info(f"Auto-set target_var='price_close' für zeitbasierte Vorhersage")
        
        job_id = await create_job(
            job_type="TRAIN",
            priority=5,
            train_model_type=request.model_type,
            train_target_var=effective_target_var,
            train_operator=request.operator,
            train_value=request.target_value,
            train_start=request.train_start,
            train_end=request.train_end,
            train_features=request.features,  # JSONB
            train_phases=request.phases,  # JSONB
            train_params=final_params,  # JSONB (enthält jetzt auch zeitbasierte Parameter)
            progress_msg=request.name,  # ⚠️ WICHTIG: Name temporär in progress_msg speichern!
            # Zeitbasierte Vorhersage-Parameter
            train_future_minutes=request.future_minutes if request.use_time_based_prediction else None,
            train_price_change_percent=request.min_percent_change if request.use_time_based_prediction else None,
            train_target_direction=request.direction if request.use_time_based_prediction else None,
            use_flag_features=use_flag_features  # NEU: Flag-Features Parameter
        )
        
        logger.info(f"✅ TRAIN-Job erstellt: {job_id} für Modell '{request.name}'")
        
        return CreateJobResponse(
            job_id=job_id,
            message=f"Job erstellt. Modell '{request.name}' wird trainiert.",
            status="PENDING"
        )
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"❌ Fehler beim Erstellen des TRAIN-Jobs: {e}")
        logger.error(f"❌ Traceback: {error_details}")
        raise HTTPException(status_code=500, detail=f"Trainingsfehler: {str(e)}")

@router.get("/models", response_model=List[ModelResponse])
async def list_models_endpoint(
    status: Optional[str] = None,
    is_deleted: bool = False
):
    """Listet alle Modelle (mit optionalen Filtern)"""
    try:
        try:
            models = await list_models(status=status, is_deleted=is_deleted)
        except Exception as db_error:
            logger.warning(f"⚠️ Datenbank nicht verfügbar für Models: {db_error}")
            logger.info("ℹ️ Rückgabe leerer Model-Liste im eingeschränkten Modus")
            return []
        # Konvertiere JSONB-Felder und extrahiere Confusion Matrix Werte für Legacy-Felder
        result = []
        for model in models:
            model_dict = dict(model)
            # NEU: Extrahiere Confusion Matrix Werte für Legacy-Felder (tp, tn, fp, fn)
            if model_dict.get('confusion_matrix') and isinstance(model_dict['confusion_matrix'], dict):
                cm = model_dict['confusion_matrix']
                model_dict['tp'] = cm.get('tp')
                model_dict['tn'] = cm.get('tn')
                model_dict['fp'] = cm.get('fp')
                model_dict['fn'] = cm.get('fn')
            result.append(ModelResponse(**model_dict))
        return result
    except DatabaseError as e:
        logger.error(f"❌ Datenbank-Fehler beim Auflisten der Modelle: {e.message}")
        raise HTTPException(status_code=500, detail=e.to_dict())
    except Exception as e:
        logger.error(f"❌ Unerwarteter Fehler beim Auflisten der Modelle: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail={"error": "InternalServerError", "message": "Ein unerwarteter Fehler ist aufgetreten"})

@router.get("/models/{model_id}", response_model=ModelResponse)
async def get_model_endpoint(model_id: int):
    """Holt Modell-Details"""
    try:
        model = await get_model(model_id)
        if not model:
            raise ModelNotFoundError(model_id)
        if model.get('is_deleted'):
            raise ModelNotFoundError(model_id)
        
        # NEU: Extrahiere Confusion Matrix Werte für Legacy-Felder (tp, tn, fp, fn)
        if model.get('confusion_matrix') and isinstance(model['confusion_matrix'], dict):
            cm = model['confusion_matrix']
            model['tp'] = cm.get('tp')
            model['tn'] = cm.get('tn')
            model['fp'] = cm.get('fp')
            model['fn'] = cm.get('fn')
        
        return ModelResponse(**dict(model))
    except ModelNotFoundError as e:
        logger.warning(f"⚠️ Modell nicht gefunden: {e.message}")
        raise HTTPException(status_code=404, detail=e.to_dict())
    except DatabaseError as e:
        logger.error(f"❌ Datenbank-Fehler beim Abrufen des Modells: {e.message}")
        raise HTTPException(status_code=500, detail=e.to_dict())
    except Exception as e:
        logger.error(f"❌ Unerwarteter Fehler beim Abrufen des Modells: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail={"error": "InternalServerError", "message": "Ein unerwarteter Fehler ist aufgetreten"})

@router.post("/models/{model_id}/test", response_model=CreateJobResponse, status_code=status.HTTP_201_CREATED)
async def test_model_job(
    model_id: int,
    test_start: str,
    test_end: str
):
    """
    Erstellt einen TEST-Job (Modell wird asynchron getestet)
    """
    try:
        # Prüfe ob Modell existiert
        model = await get_model(model_id)
        if not model or model.get('is_deleted'):
            raise ModelNotFoundError(model_id)
        
        # Konvertiere datetime-Strings
        from datetime import datetime, timezone
        test_start_dt = datetime.fromisoformat(test_start.replace('Z', '+00:00'))
        test_end_dt = datetime.fromisoformat(test_end.replace('Z', '+00:00'))
        if test_start_dt.tzinfo is None:
            test_start_dt = test_start_dt.replace(tzinfo=timezone.utc)
        if test_end_dt.tzinfo is None:
            test_end_dt = test_end_dt.replace(tzinfo=timezone.utc)
        
        # Erstelle TEST-Job
        job_id = await create_job(
            job_type="TEST",
            priority=5,
            test_model_id=model_id,
            test_start=test_start_dt,
            test_end=test_end_dt
        )
        
        logger.info(f"✅ TEST-Job erstellt: {job_id} für Modell {model_id}")
        
        return CreateJobResponse(
            job_id=job_id,
            message=f"Test-Job erstellt für Modell {model_id}",
            status="PENDING"
        )
    except ModelNotFoundError as e:
        logger.warning(f"⚠️ Modell nicht gefunden: {e.message}")
        raise HTTPException(status_code=404, detail=e.to_dict())
    except DatabaseError as e:
        logger.error(f"❌ Datenbank-Fehler beim Erstellen des TEST-Jobs: {e.message}")
        raise HTTPException(status_code=500, detail=e.to_dict())
    except Exception as e:
        logger.error(f"❌ Unerwarteter Fehler beim Erstellen des TEST-Jobs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail={"error": "InternalServerError", "message": "Ein unerwarteter Fehler ist aufgetreten"})

@router.post("/models/compare", response_model=CreateJobResponse, status_code=status.HTTP_201_CREATED)
async def compare_models_job(
    model_ids: str = Query(..., description="Komma-separierte Modell-IDs (2-4 Modelle), z.B. '155,156,157'"),
    test_start: str = Query(..., description="Start des Testzeitraums (ISO-Format, z.B. '2026-01-07T10:00:00Z')"),
    test_end: str = Query(..., description="Ende des Testzeitraums (ISO-Format, z.B. '2026-01-07T18:00:00Z')")
):
    """
    Erstellt einen COMPARE-Job (bis zu 4 Modelle werden asynchron verglichen)
    
    Workflow:
    1. Für jedes Modell wird ein Test-Job gestartet
    2. System wartet auf alle Tests
    3. Ergebnisse werden verglichen
    4. Gewinner wird nach Durchschnitts-Score bestimmt
    """
    try:
        # Parse model_ids
        parsed_model_ids = [int(mid.strip()) for mid in model_ids.split(',') if mid.strip()]
        
        if len(parsed_model_ids) < 2:
            raise HTTPException(status_code=400, detail="Mindestens 2 Modelle erforderlich")
        if len(parsed_model_ids) > 4:
            raise HTTPException(status_code=400, detail="Maximal 4 Modelle erlaubt")
        if len(parsed_model_ids) != len(set(parsed_model_ids)):
            raise HTTPException(status_code=400, detail="Alle Modell-IDs müssen unterschiedlich sein")
        
        # Prüfe ob alle Modelle existieren
        for model_id in parsed_model_ids:
            model = await get_model(model_id)
            if not model or model.get('is_deleted'):
                raise ModelNotFoundError(model_id)
        
        # Parse Zeitstempel
        from datetime import timezone
        test_start_dt = datetime.fromisoformat(test_start.replace('Z', '+00:00'))
        test_end_dt = datetime.fromisoformat(test_end.replace('Z', '+00:00'))
        
        if test_start_dt >= test_end_dt:
            raise HTTPException(status_code=400, detail="test_start muss vor test_end liegen")
        
        # Erstelle COMPARE-Job (mit neuen JSONB-Feldern)
        job_id = await create_job(
            job_type="COMPARE",
            priority=5,
            compare_model_ids=parsed_model_ids,  # NEU: JSONB Array
            compare_model_a_id=parsed_model_ids[0] if len(parsed_model_ids) >= 1 else None,  # Legacy
            compare_model_b_id=parsed_model_ids[1] if len(parsed_model_ids) >= 2 else None,  # Legacy
            compare_start=test_start_dt,
            compare_end=test_end_dt
        )
        
        model_count = len(parsed_model_ids)
        logger.info(f"✅ COMPARE-Job erstellt: {job_id} ({model_count} Modelle: {parsed_model_ids})")
        
        return CreateJobResponse(
            job_id=job_id,
            message=f"Vergleichs-Job erstellt für {model_count} Modelle: {parsed_model_ids}",
            status="PENDING"
        )
    except ModelNotFoundError as e:
        logger.warning(f"⚠️ Modell nicht gefunden: {e.message}")
        raise HTTPException(status_code=404, detail=e.to_dict())
    except DatabaseError as e:
        logger.error(f"❌ Datenbank-Fehler beim Erstellen des COMPARE-Jobs: {e.message}")
        raise HTTPException(status_code=500, detail=e.to_dict())
    except ValueError as e:
        logger.error(f"❌ Ungültige Parameter: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Unerwarteter Fehler beim Erstellen des COMPARE-Jobs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail={"error": "InternalServerError", "message": str(e)})


@router.patch("/models/{model_id}", response_model=ModelResponse)
async def update_model_endpoint(model_id: int, request: UpdateModelRequest):
    """
    Aktualisiert Modell-Name oder Beschreibung
    """
    try:
        model = await get_model(model_id)
        if not model:
            raise HTTPException(status_code=404, detail=f"Modell {model_id} nicht gefunden")
        if model.get('is_deleted'):
            raise HTTPException(status_code=404, detail=f"Modell {model_id} wurde gelöscht")
        
        # Prüfe ob Name bereits existiert (wenn geändert)
        if request.name and request.name != model.get('name'):
            existing = await list_models()
            if any(m.get('name') == request.name and m.get('id') != model_id for m in existing):
                raise HTTPException(status_code=400, detail=f"Modell-Name '{request.name}' existiert bereits")
        
        # Aktualisiere nur gesetzte Felder
        update_data = request.dict(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="Keine Update-Daten bereitgestellt")
        
        await update_model(model_id, name=update_data.get('name'), description=update_data.get('description'))
        logger.info(f"✅ Modell aktualisiert: {model_id} (name={update_data.get('name')}, description={update_data.get('description')})")
        
        # Lade aktualisiertes Modell
        updated_model = await get_model(model_id)
        return ModelResponse(**dict(updated_model))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Fehler beim Aktualisieren des Modells: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/models/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model_endpoint(model_id: int):
    """
    Soft-Delete: Markiert Modell als gelöscht (löscht Datei nicht!)
    """
    try:
        model = await get_model(model_id)
        if not model:
            raise HTTPException(status_code=404, detail=f"Modell {model_id} nicht gefunden")
        
        await delete_model(model_id)
        logger.info(f"✅ Modell gelöscht (soft): {model_id}")
        
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Fehler beim Löschen des Modells: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/{model_id}/download")
async def download_model(model_id: int):
    """
    Download .pkl Datei des Modells
    """
    try:
        model = await get_model(model_id)
        if not model or model.get('is_deleted'):
            raise HTTPException(status_code=404, detail=f"Modell {model_id} nicht gefunden")
        
        model_path = model.get('model_file_path')
        if not model_path or not os.path.exists(model_path):
            raise HTTPException(status_code=404, detail=f"Modell-Datei nicht gefunden: {model_path}")
        
        return FileResponse(
            path=model_path,
            filename=os.path.basename(model_path),
            media_type='application/octet-stream'
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Fehler beim Download des Modells: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# Queue Endpoints
# ============================================================

def convert_jsonb_fields(job_dict: dict) -> dict:
    """Konvertiert JSONB-Strings zu Python-Objekten (refactored: nutze Helper-Funktion)"""
    from app.database.utils import convert_jsonb_fields as convert_jsonb
    
    jsonb_fields = ['train_features', 'train_phases', 'train_params']
    return convert_jsonb(job_dict, jsonb_fields, direction="from")

@router.get("/queue", response_model=List[JobResponse])
async def list_jobs_endpoint(
    status: Optional[str] = None,
    job_type: Optional[str] = None
):
    """Listet alle Jobs (mit optionalen Filtern)"""
    try:
        # Im eingeschränkten Modus (DB nicht verfügbar) leere Liste zurückgeben
        try:
            jobs = await list_jobs(status=status, job_type=job_type)
        except Exception as db_error:
            logger.warning(f"⚠️ Datenbank nicht verfügbar für Jobs: {db_error}")
            logger.info("ℹ️ Rückgabe leerer Job-Liste im eingeschränkten Modus")
            return []
        converted_jobs = []
        for job in jobs:
            job_dict = dict(job)
            converted = convert_jsonb_fields(job_dict)
            
            # Lade Ergebnisse wenn verfügbar (nur für COMPLETED Jobs, um Performance zu sparen)
            result_model = None
            result_test = None
            result_comparison = None
            
            if converted.get('status') == 'COMPLETED':
                if converted.get('result_model_id'):
                    model = await get_model(converted['result_model_id'])
                    if model:
                        result_model = ModelResponse(**dict(model))
                
                if converted.get('result_test_id'):
                    test_result = await get_test_result(converted['result_test_id'])
                    if test_result:
                        result_test = TestResultResponse(**dict(test_result))
                
                if converted.get('result_comparison_id'):
                    comparison = await get_comparison(converted['result_comparison_id'])
                    if comparison:
                        result_comparison = ComparisonResponse(**dict(comparison))
            
            job_response = JobResponse(**converted)
            job_response.result_model = result_model
            job_response.result_test = result_test
            job_response.result_comparison = result_comparison
            converted_jobs.append(job_response)
        
        return converted_jobs
    except Exception as e:
        logger.error(f"❌ Fehler beim Auflisten der Jobs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/queue/{job_id}", response_model=JobResponse)
async def get_job_endpoint(job_id: int):
    """Holt Job-Details mit Ergebnissen"""
    try:
        job = await get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} nicht gefunden")
        converted_job = convert_jsonb_fields(dict(job))
        
        # Lade Ergebnisse wenn verfügbar
        result_model = None
        result_test = None
        result_comparison = None
        
        if converted_job.get('result_model_id'):
            model = await get_model(converted_job['result_model_id'])
            if model:
                result_model = ModelResponse(**dict(model))
        
        if converted_job.get('result_test_id'):
            test_result = await get_test_result(converted_job['result_test_id'])
            if test_result:
                result_test = TestResultResponse(**dict(test_result))
        
        if converted_job.get('result_comparison_id'):
            comparison = await get_comparison(converted_job['result_comparison_id'])
            if comparison:
                result_comparison = ComparisonResponse(**dict(comparison))
        
        # Erstelle Response mit Ergebnissen
        job_response = JobResponse(**converted_job)
        job_response.result_model = result_model
        job_response.result_test = result_test
        job_response.result_comparison = result_comparison
        
        return job_response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Fehler beim Abrufen des Jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# Feature Analysis Endpoints
# ============================================================

@router.get("/features")
async def get_available_features(include_flags: bool = Query(True, description="Flag-Features inkludieren?")):
    """
    Gibt alle verfügbaren Features zurück (strukturiert für n8n Integration)
    
    NEU: Wenn include_flags=True, werden auch Flag-Features zurückgegeben.
    Flag-Features zeigen an, ob ein Engineering-Feature genug Daten hat.
    """
    base_features = [
        'price_open', 'price_high', 'price_low', 'price_close',
        'volume_sol', 'buy_volume_sol', 'sell_volume_sol', 'net_volume_sol',
        'market_cap_close', 'bonding_curve_pct', 'virtual_sol_reserves', 'is_koth',
        'num_buys', 'num_sells', 'unique_wallets', 'num_micro_trades',
        'max_single_buy_sol', 'max_single_sell_sol',
        'whale_buy_volume_sol', 'whale_sell_volume_sol', 'num_whale_buys', 'num_whale_sells',
        'dev_sold_amount', 'volatility_pct', 'avg_trade_size_sol',
        'buy_pressure_ratio', 'unique_signer_ratio', 'phase_id_at_time'
    ]

    engineered_features = [
        # Dev-Sold Features
        'dev_sold_flag', 'dev_sold_cumsum', 'dev_sold_spike_5', 'dev_sold_spike_10', 'dev_sold_spike_15',
        # Buy Pressure Features
        'buy_pressure_ma_5', 'buy_pressure_trend_5', 'buy_pressure_ma_10', 'buy_pressure_trend_10',
        'buy_pressure_ma_15', 'buy_pressure_trend_15',
        # Whale Features
        'whale_net_volume', 'whale_activity_5', 'whale_activity_10', 'whale_activity_15',
        # Volatility Features
        'volatility_ma_5', 'volatility_spike_5', 'volatility_ma_10', 'volatility_spike_10',
        'volatility_ma_15', 'volatility_spike_15',
        # Wash Trading
        'wash_trading_flag_5', 'wash_trading_flag_10', 'wash_trading_flag_15',
        # Volume Patterns
        'net_volume_ma_5', 'volume_flip_5', 'net_volume_ma_10', 'volume_flip_10',
        'net_volume_ma_15', 'volume_flip_15',
        # Price Momentum
        'price_change_5', 'price_roc_5', 'price_change_10', 'price_roc_10',
        'price_change_15', 'price_roc_15',
        # Market Cap Velocity
        'mcap_velocity_5', 'mcap_velocity_10', 'mcap_velocity_15',
        # ATH Features
        'rolling_ath', 'price_vs_ath_pct', 'ath_breakout', 'minutes_since_ath',
        'ath_distance_trend_5', 'ath_approach_5', 'ath_breakout_count_5',
        'ath_distance_trend_10', 'ath_approach_10', 'ath_breakout_count_10',
        'ath_distance_trend_15', 'ath_approach_15', 'ath_breakout_count_15',
        'ath_breakout_volume_ma_5', 'ath_breakout_volume_ma_10', 'ath_breakout_volume_ma_15',
        'ath_age_trend_5', 'ath_age_trend_10', 'ath_age_trend_15',
        # Power Features
        'buy_sell_ratio', 'whale_dominance',
        'price_acceleration_5', 'price_acceleration_10', 'price_acceleration_15',
        'volume_spike_5', 'volume_spike_10', 'volume_spike_15'
    ]

    # NEU: Flag-Features generieren
    flag_features = []
    if include_flags:
        # Verwende die get_flag_feature_names Funktion aus feature_engineering
        from app.training.feature_engineering import get_flag_feature_names
        flag_features = get_flag_feature_names(engineered_features)

    logger.info(f"✅ {len(base_features)} Base + {len(engineered_features)} Engineering + {len(flag_features)} Flag Features")

    return {
        "base": sorted(base_features),
        "engineered": sorted(engineered_features),
        "flag_features": sorted(flag_features) if include_flags else [],  # NEU
        "total": len(base_features) + len(engineered_features) + len(flag_features),
        "base_count": len(base_features),
        "engineered_count": len(engineered_features),
        "flag_count": len(flag_features)  # NEU
    }

# ============================================================
# System Endpoints
# ============================================================

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health Check Endpoint
    Gibt Status, DB-Verbindung, Uptime zurück
    Status Code: 200 wenn healthy, 503 wenn degraded
    """
    try:
        health = await get_health_status()
        health_response = HealthResponse(**health)
        
        # Status Code basierend auf Health
        if health["status"] == "healthy":
            return health_response
        else:
            # Degraded: 503 Service Unavailable
            return JSONResponse(
                content=health_response.dict(),
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE
            )
    except Exception as e:
        logger.error(f"❌ Fehler beim Health Check: {e}")
        health_response = HealthResponse(
            status="degraded",
            db_connected=False,
            uptime_seconds=0,
            start_time=None,
            total_jobs_processed=0,
            last_error=str(e)
        )
        return JSONResponse(
            content=health_response.dict(),
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )

@router.get("/metrics")
async def metrics_endpoint():
    """
    Prometheus Metrics Endpoint
    Gibt Metrics im Prometheus-Format zurück
    """
    try:
        metrics = generate_metrics()
        return Response(
            content=metrics,
            media_type="text/plain; version=0.0.4; charset=utf-8"
        )
    except Exception as e:
        logger.error(f"❌ Fehler beim Generieren der Metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# Configuration Endpoints
# ============================================================

@router.get("/config", response_model=ConfigResponse)
async def get_config():
    """
    Gibt die aktuelle Konfiguration zurück
    """
    try:
        from app.utils.config import get_config_dict
        return ConfigResponse(**get_config_dict())
    except Exception as e:
        logger.error(f"❌ Fehler beim Laden der Konfiguration: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Laden der Konfiguration: {str(e)}"
        )

@router.put("/config", response_model=ConfigUpdateResponse)
async def update_config(request: ConfigUpdateRequest):
    """
    Aktualisiert die Konfiguration zur Laufzeit
    """
    from app.utils.config import update_config_from_dict

    # Filtere None-Werte heraus
    update_data = {k: v for k, v in request.model_dump().items() if v is not None}

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="Keine gültigen Konfigurationswerte zum Aktualisieren angegeben"
        )

    try:
        # Aktualisiere die Config
        update_config_from_dict(update_data)

        logger.info(f"🔧 Konfiguration aktualisiert: {list(update_data.keys())}")

        return ConfigUpdateResponse(
            message="Konfiguration erfolgreich aktualisiert",
            status="success",
            updated_fields=list(update_data.keys())
        )
    except Exception as e:
        logger.error(f"❌ Fehler beim Aktualisieren der Konfiguration: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Aktualisieren der Konfiguration: {str(e)}"
        )

@router.post("/reload-config")
async def reload_config_endpoint():
    """
    Lädt die Konfiguration neu (ohne Neustart)
    Liest .env Datei neu und aktualisiert Config
    """
    try:
        # Lade Config neu aus Environment
        from app.utils.config import reload_config_from_env
        reload_config_from_env()

        logger.info("🔄 Konfiguration wurde neu geladen")

        return {
            "message": "Konfiguration wurde neu geladen",
            "status": "success"
        }
    except Exception as e:
        logger.error(f"❌ Fehler beim Neuladen der Konfiguration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reconnect-db")
async def reconnect_db_endpoint():
    """
    Lädt Konfiguration neu und baut DB-Verbindung mit neuer Konfiguration neu auf
    """
    try:
        from app.database.connection import close_pool, get_pool
        from app.utils.metrics import get_health_status
        from app.utils.config import reload_config_from_env

        # Konfiguration ist bereits durch updateConfig aktualisiert worden
        # Verwende runtime config oder fallback zu env
        from app.utils.config import get_runtime_config, DB_DSN
        current_dsn = get_runtime_config('db_dsn', DB_DSN)
        logger.info(f"🔄 Verwende DB_DSN: {current_dsn}")

        # Temporär die globale Variable überschreiben für diesen Request
        import app.utils.config
        original_dsn = app.utils.config.DB_DSN
        app.utils.config.DB_DSN = current_dsn

        # Schließe bestehende Verbindung
        await close_pool()
        logger.info("🔌 Bestehende DB-Verbindung geschlossen")

        # Setze Pool zurück (damit neue Konfiguration verwendet wird)
        import app.database.connection
        app.database.connection.pool = None

        # Versuche neue Verbindung aufzubauen
        try:
            await get_pool()  # Erstellt automatisch neuen Pool mit neuer Konfiguration
            logger.info("✅ Neue DB-Verbindung erfolgreich aufgebaut")

            # Teste die Verbindung
            health = await get_health_status()

            # Setze DB_AVAILABLE Flag
            import app.main
            app.main.DB_AVAILABLE = health["db_connected"]

            # Stelle originale DSN wieder her (aber behalte die funktionierende Verbindung)
            app.utils.config.DB_DSN = original_dsn

            return {
                "message": "Datenbankverbindung erfolgreich neu aufgebaut",
                "status": "success",
                "db_connected": health["db_connected"],
                "health_status": health["status"]
            }

        except Exception as db_error:
            logger.error(f"❌ Neue DB-Verbindung fehlgeschlagen: {db_error}")

            # Stelle eingeschränkten Modus wieder her
            import app.main
            app.main.DB_AVAILABLE = False

            # Stelle originale DSN wieder her
            app.utils.config.DB_DSN = original_dsn

            return {
                "message": f"DB-Verbindung fehlgeschlagen: {str(db_error)}",
                "status": "error",
                "db_connected": False,
                "health_status": "degraded"
            }

    except Exception as e:
        logger.error(f"❌ Fehler beim DB-Reconnect: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim DB-Reconnect: {str(e)}"
        )

@router.get("/phases")
async def get_phases_endpoint():
    """
    Lade alle Coin-Phasen aus ref_coin_phases mit interval_seconds
    
    Returns:
        Liste von Phasen mit: id, name, interval_seconds, max_age_minutes
    """
    try:
        phases = await get_coin_phases()
        return phases
    except Exception as e:
        logger.error(f"❌ Fehler beim Laden der Phasen: {e}")
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden der Phasen: {str(e)}")

# ============================================================
# Comparison Endpoints
# ============================================================

@router.get("/comparisons", response_model=List[ComparisonResponse])
async def list_comparisons_endpoint(limit: int = 100, offset: int = 0):
    """
    Listet alle Vergleichs-Ergebnisse
    """
    try:
        comparisons = await list_comparisons(limit=limit, offset=offset)
        # Konvertiere zu ComparisonResponse
        result = []
        for comp in comparisons:
            try:
                result.append(ComparisonResponse(**dict(comp)))
            except Exception as e:
                logger.warning(f"⚠️ Fehler beim Konvertieren von Vergleich {comp.get('id')}: {e}")
                continue
        return result
    except Exception as e:
        logger.error(f"❌ Fehler beim Auflisten der Vergleiche: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/comparisons/{comparison_id}", response_model=ComparisonResponse)
async def get_comparison_endpoint(comparison_id: int):
    """
    Holt einen einzelnen Vergleich
    """
    try:
        comparison = await get_comparison(comparison_id)
        if not comparison:
            raise HTTPException(status_code=404, detail=f"Vergleich {comparison_id} nicht gefunden")
        return ComparisonResponse(**dict(comparison))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Fehler beim Abrufen des Vergleichs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/comparisons/{comparison_id}")
async def delete_comparison_endpoint(comparison_id: int):
    """
    Löscht einen Vergleich
    """
    try:
        comparison = await get_comparison(comparison_id)
        if not comparison:
            raise HTTPException(status_code=404, detail=f"Vergleich {comparison_id} nicht gefunden")
        
        deleted = await delete_comparison(comparison_id)
        if deleted:
            logger.info(f"✅ Vergleich gelöscht: {comparison_id}")
            return {"message": f"Vergleich {comparison_id} erfolgreich gelöscht"}
        else:
            raise HTTPException(status_code=500, detail="Fehler beim Löschen des Vergleichs")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Fehler beim Löschen des Vergleichs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# Test Results Endpoints
# ============================================================

@router.get("/test-results", response_model=List[TestResultResponse])
async def list_test_results_endpoint(limit: int = 100, offset: int = 0):
    """
    Listet alle Test-Ergebnisse
    """
    try:
        test_results = await list_all_test_results(limit=limit, offset=offset)
        # Konvertiere zu TestResultResponse
        result = []
        for test in test_results:
            try:
                result.append(TestResultResponse(**dict(test)))
            except Exception as e:
                logger.warning(f"⚠️ Fehler beim Konvertieren von Test-Ergebnis {test.get('id')}: {e}")
                continue
        return result
    except Exception as e:
        logger.error(f"❌ Fehler beim Auflisten der Test-Ergebnisse: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test-results/{test_id}", response_model=TestResultResponse)
async def get_test_result_endpoint(test_id: int):
    """
    Holt ein einzelnes Test-Ergebnis
    """
    try:
        test_result = await get_test_result(test_id)
        if not test_result:
            raise HTTPException(status_code=404, detail=f"Test-Ergebnis {test_id} nicht gefunden")
        return TestResultResponse(**dict(test_result))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Fehler beim Abrufen des Test-Ergebnisses: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/test-results/{test_id}")
async def delete_test_result_endpoint(test_id: int):
    """
    Löscht ein Test-Ergebnis
    """
    try:
        test_result = await get_test_result(test_id)
        if not test_result:
            raise HTTPException(status_code=404, detail=f"Test-Ergebnis {test_id} nicht gefunden")
        
        deleted = await delete_test_result(test_id)
        if deleted:
            logger.info(f"✅ Test-Ergebnis gelöscht: {test_id}")
            return {"message": f"Test-Ergebnis {test_id} erfolgreich gelöscht"}
        else:
            raise HTTPException(status_code=500, detail="Fehler beim Löschen des Test-Ergebnisses")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Fehler beim Löschen des Test-Ergebnisses: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data-availability")
async def get_data_availability(pool = Depends(get_pool)):
    """
    Gibt zurück, wann die ältesten und neuesten Einträge in coin_metrics vorhanden sind.
    
    Returns:
        {
            "min_timestamp": "2025-12-20T10:00:00Z",
            "max_timestamp": "2025-12-23T15:30:00Z"
        }
    """
    try:
        # Einfache Abfrage: Nur Min/Max Timestamps
        query = """
            SELECT 
                MIN(timestamp) as min_ts,
                MAX(timestamp) as max_ts
            FROM coin_metrics
        """
        row = await pool.fetchrow(query)
        
        if not row or not row['min_ts']:
            return {
                "min_timestamp": None,
                "max_timestamp": None
            }
        
        min_ts = row['min_ts']
        max_ts = row['max_ts']
        
        # Konvertiere zu ISO-Format Strings
        # Stelle sicher, dass Zeitzone UTC ist
        from datetime import timezone
        if min_ts.tzinfo is None:
            min_ts = min_ts.replace(tzinfo=timezone.utc)
        if max_ts.tzinfo is None:
            max_ts = max_ts.replace(tzinfo=timezone.utc)
        
        return {
            "min_timestamp": min_ts.isoformat().replace('+00:00', 'Z'),
            "max_timestamp": max_ts.isoformat().replace('+00:00', 'Z')
        }
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Daten-Verfügbarkeit: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Zusätzliche Endpoints für Coolify-Kompatibilität (ohne /api Prefix)
coolify_router = APIRouter()

@coolify_router.get("/health")
async def health_check_coolify():
    """Health Check für Coolify (ohne /api Prefix)"""
    return await health_check()

@coolify_router.get("/metrics")
async def metrics_coolify():
    """Metrics für Coolify (ohne /api Prefix)"""
    return await metrics_endpoint()

@router.get("/phases")
async def get_phases_endpoint():
    """
    Lade alle Coin-Phasen aus ref_coin_phases mit interval_seconds
    
    Returns:
        Liste von Phasen mit: id, name, interval_seconds, max_age_minutes
    """
    try:
        phases = await get_coin_phases()
        return phases
    except Exception as e:
        logger.error(f"❌ Fehler beim Laden der Phasen: {e}")
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden der Phasen: {str(e)}")

# ============================================================
# Comparison Endpoints
# ============================================================

@router.get("/comparisons", response_model=List[ComparisonResponse])
async def list_comparisons_endpoint(limit: int = 100, offset: int = 0):
    """
    Listet alle Vergleichs-Ergebnisse
    """
    try:
        comparisons = await list_comparisons(limit=limit, offset=offset)
        # Konvertiere zu ComparisonResponse
        result = []
        for comp in comparisons:
            try:
                result.append(ComparisonResponse(**dict(comp)))
            except Exception as e:
                logger.warning(f"⚠️ Fehler beim Konvertieren von Vergleich {comp.get('id')}: {e}")
                continue
        return result
    except Exception as e:
        logger.error(f"❌ Fehler beim Auflisten der Vergleiche: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/comparisons/{comparison_id}", response_model=ComparisonResponse)
async def get_comparison_endpoint(comparison_id: int):
    """
    Holt einen einzelnen Vergleich
    """
    try:
        comparison = await get_comparison(comparison_id)
        if not comparison:
            raise HTTPException(status_code=404, detail=f"Vergleich {comparison_id} nicht gefunden")
        return ComparisonResponse(**dict(comparison))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Fehler beim Abrufen des Vergleichs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/comparisons/{comparison_id}")
async def delete_comparison_endpoint(comparison_id: int):
    """
    Löscht einen Vergleich
    """
    try:
        comparison = await get_comparison(comparison_id)
        if not comparison:
            raise HTTPException(status_code=404, detail=f"Vergleich {comparison_id} nicht gefunden")
        
        deleted = await delete_comparison(comparison_id)
        if deleted:
            logger.info(f"✅ Vergleich gelöscht: {comparison_id}")
            return {"message": f"Vergleich {comparison_id} erfolgreich gelöscht"}
        else:
            raise HTTPException(status_code=500, detail="Fehler beim Löschen des Vergleichs")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Fehler beim Löschen des Vergleichs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# Test Results Endpoints
# ============================================================

@router.get("/test-results", response_model=List[TestResultResponse])
async def list_test_results_endpoint(limit: int = 100, offset: int = 0):
    """
    Listet alle Test-Ergebnisse
    """
    try:
        test_results = await list_all_test_results(limit=limit, offset=offset)
        # Konvertiere zu TestResultResponse
        result = []
        for test in test_results:
            try:
                result.append(TestResultResponse(**dict(test)))
            except Exception as e:
                logger.warning(f"⚠️ Fehler beim Konvertieren von Test-Ergebnis {test.get('id')}: {e}")
                continue
        return result
    except Exception as e:
        logger.error(f"❌ Fehler beim Auflisten der Test-Ergebnisse: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test-results/{test_id}", response_model=TestResultResponse)
async def get_test_result_endpoint(test_id: int):
    """
    Holt ein einzelnes Test-Ergebnis
    """
    try:
        test_result = await get_test_result(test_id)
        if not test_result:
            raise HTTPException(status_code=404, detail=f"Test-Ergebnis {test_id} nicht gefunden")
        return TestResultResponse(**dict(test_result))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Fehler beim Abrufen des Test-Ergebnisses: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/test-results/{test_id}")
async def delete_test_result_endpoint(test_id: int):
    """
    Löscht ein Test-Ergebnis
    """
    try:
        test_result = await get_test_result(test_id)
        if not test_result:
            raise HTTPException(status_code=404, detail=f"Test-Ergebnis {test_id} nicht gefunden")
        
        deleted = await delete_test_result(test_id)
        if deleted:
            logger.info(f"✅ Test-Ergebnis gelöscht: {test_id}")
            return {"message": f"Test-Ergebnis {test_id} erfolgreich gelöscht"}
        else:
            raise HTTPException(status_code=500, detail="Fehler beim Löschen des Test-Ergebnisses")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Fehler beim Löschen des Test-Ergebnisses: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data-availability")
async def get_data_availability(pool = Depends(get_pool)):
    """
    Gibt zurück, wann die ältesten und neuesten Einträge in coin_metrics vorhanden sind.
    
    Returns:
        {
            "min_timestamp": "2025-12-20T10:00:00Z",
            "max_timestamp": "2025-12-23T15:30:00Z"
        }
    """
    try:
        # Einfache Abfrage: Nur Min/Max Timestamps
        query = """
            SELECT 
                MIN(timestamp) as min_ts,
                MAX(timestamp) as max_ts
            FROM coin_metrics
        """
        row = await pool.fetchrow(query)
        
        if not row or not row['min_ts']:
            return {
                "min_timestamp": None,
                "max_timestamp": None
            }
        
        min_ts = row['min_ts']
        max_ts = row['max_ts']
        
        # Konvertiere zu ISO-Format Strings
        # Stelle sicher, dass Zeitzone UTC ist
        from datetime import timezone
        if min_ts.tzinfo is None:
            min_ts = min_ts.replace(tzinfo=timezone.utc)
        if max_ts.tzinfo is None:
            max_ts = max_ts.replace(tzinfo=timezone.utc)
        
        return {
            "min_timestamp": min_ts.isoformat().replace('+00:00', 'Z'),
            "max_timestamp": max_ts.isoformat().replace('+00:00', 'Z')
        }
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Daten-Verfügbarkeit: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Zusätzliche Endpoints für Coolify-Kompatibilität (ohne /api Prefix)
coolify_router = APIRouter()

@coolify_router.get("/health")
async def health_check_coolify():
    """Health Check für Coolify (ohne /api Prefix)"""
    return await health_check()

@coolify_router.get("/metrics")
async def metrics_coolify():
    """Metrics für Coolify (ohne /api Prefix)"""
    return await metrics_endpoint()
"""
MCP Tools for Predictions

Provides tools for making predictions and retrieving prediction history.
All tools delegate to existing service functions to avoid code duplication.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.database.models import (
    get_active_models as db_get_active_models,
    get_predictions as db_get_predictions,
    get_latest_prediction as db_get_latest_prediction,
)
from app.database.connection import get_pool
from app.prediction.engine import predict_coin_all_models

logger = logging.getLogger(__name__)


async def predict_coin(
    coin_id: str,
    model_ids: Optional[List[int]] = None,
    timestamp: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Macht eine Vorhersage für einen Coin mit allen oder ausgewählten Modellen.

    Args:
        coin_id: Coin-ID (Mint-Adresse)
        model_ids: Optional - Liste von active_model_ids (wenn None, alle aktiven Modelle)
        timestamp: Optional - Zeitstempel für Vorhersage (wenn None, aktueller Zeitpunkt)

    Returns:
        Dict mit Vorhersage-Ergebnissen
    """
    try:
        # Hole aktive Modelle
        all_models = await db_get_active_models(include_inactive=False)

        if not all_models:
            return {
                "success": False,
                "error": "No active models found",
                "predictions": []
            }

        # Filter nach model_ids wenn angegeben
        if model_ids:
            models = [m for m in all_models if m.get("id") in model_ids]
            if not models:
                return {
                    "success": False,
                    "error": f"No active models found with IDs: {model_ids}",
                    "predictions": []
                }
        else:
            models = all_models

        # Setze Timestamp
        pred_timestamp = timestamp or datetime.utcnow()

        # Hole DB Pool
        pool = await get_pool()

        # Mache Vorhersagen
        results = await predict_coin_all_models(
            coin_id=coin_id,
            timestamp=pred_timestamp,
            active_models=models,
            pool=pool
        )

        # Formatiere Ergebnisse
        predictions = []
        for r in results:
            if r:  # Kann None sein bei Fehlern
                predictions.append({
                    "model_id": r.get("model_id"),
                    "active_model_id": r.get("active_model_id"),
                    "model_name": r.get("model_name"),
                    "prediction": r.get("prediction"),  # 0 oder 1
                    "prediction_label": "POSITIVE (UP)" if r.get("prediction") == 1 else "NEGATIVE (DOWN)",
                    "probability": round(r.get("probability", 0), 4),
                })

        return {
            "success": True,
            "coin_id": coin_id,
            "timestamp": str(pred_timestamp),
            "predictions": predictions,
            "total_models": len(models),
            "successful_predictions": len(predictions),
        }

    except Exception as e:
        logger.error(f"Error predicting coin {coin_id}: {e}")
        return {
            "success": False,
            "error": str(e),
            "predictions": []
        }


async def get_predictions(
    coin_id: Optional[str] = None,
    active_model_id: Optional[int] = None,
    prediction: Optional[int] = None,
    min_probability: Optional[float] = None,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Holt Vorhersagen mit optionalen Filtern.

    Args:
        coin_id: Filter nach Coin-ID (optional)
        active_model_id: Filter nach aktivem Modell (optional)
        prediction: Filter nach Vorhersage: 0 (negative) oder 1 (positive) (optional)
        min_probability: Minimale Wahrscheinlichkeit (0.0-1.0) (optional)
        limit: Maximale Anzahl (default: 50)
        offset: Offset für Pagination (default: 0)

    Returns:
        Dict mit Liste von Vorhersagen
    """
    try:
        predictions = await db_get_predictions(
            coin_id=coin_id,
            active_model_id=active_model_id,
            prediction=prediction,
            min_probability=min_probability,
            limit=limit,
            offset=offset
        )

        # Formatiere Ergebnisse
        formatted = []
        for p in predictions:
            formatted.append({
                "id": p.get("id"),
                "coin_id": p.get("coin_id"),
                "model_id": p.get("model_id"),
                "active_model_id": p.get("active_model_id"),
                "prediction": p.get("prediction"),
                "prediction_label": "POSITIVE" if p.get("prediction") == 1 else "NEGATIVE",
                "probability": round(p.get("probability", 0), 4),
                "data_timestamp": str(p.get("data_timestamp")) if p.get("data_timestamp") else None,
                "created_at": str(p.get("created_at")) if p.get("created_at") else None,
            })

        return {
            "success": True,
            "predictions": formatted,
            "count": len(formatted),
            "limit": limit,
            "offset": offset,
            "filters": {
                "coin_id": coin_id,
                "active_model_id": active_model_id,
                "prediction": prediction,
                "min_probability": min_probability,
            }
        }

    except Exception as e:
        logger.error(f"Error getting predictions: {e}")
        return {
            "success": False,
            "error": str(e),
            "predictions": [],
            "count": 0
        }


async def get_latest_prediction(
    coin_id: str,
    model_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Holt die neueste Vorhersage für einen Coin.

    Args:
        coin_id: Coin-ID (Mint-Adresse)
        model_id: Optional - Filter nach Modell-ID

    Returns:
        Dict mit der neuesten Vorhersage
    """
    try:
        prediction = await db_get_latest_prediction(
            coin_id=coin_id,
            model_id=model_id
        )

        if not prediction:
            return {
                "success": True,
                "found": False,
                "message": f"No prediction found for coin {coin_id}",
                "prediction": None
            }

        return {
            "success": True,
            "found": True,
            "prediction": {
                "id": prediction.get("id"),
                "coin_id": prediction.get("coin_id"),
                "model_id": prediction.get("model_id"),
                "active_model_id": prediction.get("active_model_id"),
                "prediction": prediction.get("prediction"),
                "prediction_label": "POSITIVE" if prediction.get("prediction") == 1 else "NEGATIVE",
                "probability": round(prediction.get("probability", 0), 4),
                "data_timestamp": str(prediction.get("data_timestamp")) if prediction.get("data_timestamp") else None,
                "created_at": str(prediction.get("created_at")) if prediction.get("created_at") else None,
            }
        }

    except Exception as e:
        logger.error(f"Error getting latest prediction for {coin_id}: {e}")
        return {
            "success": False,
            "error": str(e),
            "found": False,
            "prediction": None
        }

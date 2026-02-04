"""
MCP Tools Package

Contains all tool implementations for the MCP server:
- models: Model management tools
- predictions: Prediction tools
- configuration: Configuration tools
- system: System/health tools
"""

from app.mcp.tools.models import (
    list_active_models,
    list_available_models,
    import_model,
    get_model_details,
    activate_model,
    deactivate_model,
)
from app.mcp.tools.predictions import (
    predict_coin,
    get_predictions,
    get_latest_prediction,
)
from app.mcp.tools.configuration import (
    update_alert_config,
    get_model_statistics,
)
from app.mcp.tools.system import (
    health_check,
    get_stats,
)

__all__ = [
    # Models
    "list_active_models",
    "list_available_models",
    "import_model",
    "get_model_details",
    "activate_model",
    "deactivate_model",
    # Predictions
    "predict_coin",
    "get_predictions",
    "get_latest_prediction",
    # Configuration
    "update_alert_config",
    "get_model_statistics",
    # System
    "health_check",
    "get_stats",
]

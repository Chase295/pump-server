"""
MCP Tools Package

Contains all tool implementations for the MCP server:
- models: Model management tools
- predictions: Prediction tools
- configuration: Configuration tools
- alerts: Alert management tools
- system: System/health tools
"""

from app.mcp.tools.models import (
    list_active_models,
    list_available_models,
    import_model,
    get_model_details,
    activate_model,
    deactivate_model,
    rename_model,
    delete_model,
    update_model_metrics,
)
from app.mcp.tools.predictions import (
    predict_coin,
    get_predictions,
    get_latest_prediction,
    get_model_predictions,
    delete_model_predictions,
    reset_model_statistics,
    get_coin_details,
)
from app.mcp.tools.configuration import (
    update_alert_config,
    get_model_statistics,
    get_n8n_status,
    get_ignore_settings,
    update_ignore_settings,
    get_max_log_entries,
    update_max_log_entries,
)
from app.mcp.tools.alerts import (
    get_alerts,
    get_alert_details,
    get_alert_statistics,
    get_all_models_alert_statistics,
    delete_model_alerts,
)
from app.mcp.tools.system import (
    health_check,
    get_stats,
    get_system_config,
    update_configuration,
    get_logs,
    restart_system,
    delete_old_logs,
    migrate_performance_metrics,
    debug_active_models,
    debug_coin_metrics,
)

__all__ = [
    # Models
    "list_active_models",
    "list_available_models",
    "import_model",
    "get_model_details",
    "activate_model",
    "deactivate_model",
    "rename_model",
    "delete_model",
    "update_model_metrics",
    # Predictions
    "predict_coin",
    "get_predictions",
    "get_latest_prediction",
    "get_model_predictions",
    "delete_model_predictions",
    "reset_model_statistics",
    "get_coin_details",
    # Configuration
    "update_alert_config",
    "get_model_statistics",
    "get_n8n_status",
    "get_ignore_settings",
    "update_ignore_settings",
    "get_max_log_entries",
    "update_max_log_entries",
    # Alerts
    "get_alerts",
    "get_alert_details",
    "get_alert_statistics",
    "get_all_models_alert_statistics",
    "delete_model_alerts",
    # System
    "health_check",
    "get_stats",
    "get_system_config",
    "update_configuration",
    "get_logs",
    "restart_system",
    "delete_old_logs",
    "migrate_performance_metrics",
    "debug_active_models",
    "debug_coin_metrics",
]

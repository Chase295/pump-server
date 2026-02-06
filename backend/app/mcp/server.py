"""
MCP Server Implementation for pump-server

Provides a Model Context Protocol server that exposes pump-server
functionality to AI clients like Claude Code.
"""
import json
import logging
from typing import Any, Sequence

from mcp.server import Server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

# Import tool implementations
from app.mcp.tools import (
    # Models
    list_active_models,
    list_available_models,
    import_model,
    get_model_details,
    activate_model,
    deactivate_model,
    rename_model,
    delete_model,
    update_model_metrics,
    # Predictions
    predict_coin,
    get_predictions,
    get_latest_prediction,
    get_model_predictions,
    delete_model_predictions,
    reset_model_statistics,
    get_coin_details,
    # Configuration
    update_alert_config,
    get_model_statistics,
    get_n8n_status,
    get_ignore_settings,
    update_ignore_settings,
    get_max_log_entries,
    update_max_log_entries,
    # Alerts
    get_alerts,
    get_alert_details,
    get_alert_statistics,
    get_all_models_alert_statistics,
    delete_model_alerts,
    # System
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

logger = logging.getLogger(__name__)


def create_mcp_server() -> Server:
    """
    Creates and configures the MCP server instance.

    Returns:
        Configured MCP Server
    """
    server = Server("pump-server-mcp")

    @server.list_tools()
    async def handle_list_tools() -> list[Tool]:
        """Returns the list of available tools."""
        return [
            # === Model Management Tools ===
            Tool(
                name="list_active_models",
                description="Liste aller aktiven ML-Modelle im Pump-Server. Zeigt Name, Typ, Status, Statistiken und Training-Metriken.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "include_inactive": {
                            "type": "boolean",
                            "description": "Wenn true, werden auch pausierte Modelle angezeigt",
                            "default": False
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="list_available_models",
                description="Liste aller verfügbaren Modelle zum Import vom Training-Service. Zeigt nur Modelle die noch nicht importiert wurden.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="import_model",
                description="Importiert ein ML-Modell vom Training-Service in den Pump-Server. Das Modell wird heruntergeladen und aktiviert.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "model_id": {
                            "type": "integer",
                            "description": "ID des Modells im Training-Service (aus list_available_models)"
                        }
                    },
                    "required": ["model_id"]
                }
            ),
            Tool(
                name="get_model_details",
                description="Holt detaillierte Informationen zu einem aktiven Modell inkl. Konfiguration, Features und Statistiken.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "active_model_id": {
                            "type": "integer",
                            "description": "ID des aktiven Modells (aus list_active_models)"
                        }
                    },
                    "required": ["active_model_id"]
                }
            ),
            Tool(
                name="activate_model",
                description="Aktiviert ein pausiertes Modell, sodass es wieder Vorhersagen macht.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "active_model_id": {
                            "type": "integer",
                            "description": "ID des zu aktivierenden Modells"
                        }
                    },
                    "required": ["active_model_id"]
                }
            ),
            Tool(
                name="deactivate_model",
                description="Pausiert ein aktives Modell. Das Modell macht keine Vorhersagen mehr, bleibt aber gespeichert.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "active_model_id": {
                            "type": "integer",
                            "description": "ID des zu pausierenden Modells"
                        }
                    },
                    "required": ["active_model_id"]
                }
            ),
            Tool(
                name="rename_model",
                description="Benennt ein aktives Modell um (setzt custom_name).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "active_model_id": {
                            "type": "integer",
                            "description": "ID des aktiven Modells"
                        },
                        "new_name": {
                            "type": "string",
                            "description": "Neuer Name für das Modell"
                        }
                    },
                    "required": ["active_model_id", "new_name"]
                }
            ),
            Tool(
                name="delete_model",
                description="Löscht ein aktives Modell und ALLE zugehörigen Predictions. ACHTUNG: Nicht rückgängig machbar!",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "active_model_id": {
                            "type": "integer",
                            "description": "ID des zu löschenden Modells"
                        }
                    },
                    "required": ["active_model_id"]
                }
            ),
            Tool(
                name="update_model_metrics",
                description="Aktualisiert die Performance-Metriken eines Modells vom Training-Service (Accuracy, F1, etc.).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "active_model_id": {
                            "type": "integer",
                            "description": "ID des aktiven Modells"
                        },
                        "model_id": {
                            "type": "integer",
                            "description": "ID des Modells im Training-Service"
                        }
                    },
                    "required": ["active_model_id", "model_id"]
                }
            ),

            # === Prediction Tools ===
            Tool(
                name="predict_coin",
                description="Macht eine ML-Vorhersage für einen Cryptocurrency-Coin. Gibt Wahrscheinlichkeit für Kursanstieg/Kursfall zurück.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "coin_id": {
                            "type": "string",
                            "description": "Coin-ID (Mint-Adresse des Tokens)"
                        },
                        "model_ids": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Optional: Liste von active_model_ids. Wenn leer, werden alle aktiven Modelle verwendet."
                        }
                    },
                    "required": ["coin_id"]
                }
            ),
            Tool(
                name="get_predictions",
                description="Holt historische Vorhersagen mit Filtern. Unterstützt Pagination.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "coin_id": {
                            "type": "string",
                            "description": "Filter nach Coin-ID (optional)"
                        },
                        "active_model_id": {
                            "type": "integer",
                            "description": "Filter nach Modell (optional)"
                        },
                        "prediction": {
                            "type": "integer",
                            "enum": [0, 1],
                            "description": "Filter: 0=negativ, 1=positiv (optional)"
                        },
                        "min_probability": {
                            "type": "number",
                            "description": "Minimale Wahrscheinlichkeit 0.0-1.0 (optional)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Max. Anzahl Ergebnisse (default: 50)",
                            "default": 50
                        },
                        "offset": {
                            "type": "integer",
                            "description": "Offset für Pagination (default: 0)",
                            "default": 0
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="get_latest_prediction",
                description="Holt die neueste Vorhersage für einen bestimmten Coin.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "coin_id": {
                            "type": "string",
                            "description": "Coin-ID (Mint-Adresse)"
                        },
                        "model_id": {
                            "type": "integer",
                            "description": "Optional: Filter nach Modell-ID"
                        }
                    },
                    "required": ["coin_id"]
                }
            ),
            Tool(
                name="get_model_predictions",
                description="Holt Model-Predictions (neue Architektur) mit Filtern nach Tag, Status, Coin etc.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "active_model_id": {
                            "type": "integer",
                            "description": "Filter nach aktivem Modell (optional)"
                        },
                        "tag": {
                            "type": "string",
                            "enum": ["negativ", "positiv", "alert"],
                            "description": "Filter nach Tag (optional)"
                        },
                        "status": {
                            "type": "string",
                            "enum": ["aktiv", "inaktiv"],
                            "description": "Filter nach Status (optional)"
                        },
                        "coin_id": {
                            "type": "string",
                            "description": "Filter nach Coin-ID (optional)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Max. Anzahl Ergebnisse (default: 100)",
                            "default": 100
                        },
                        "offset": {
                            "type": "integer",
                            "description": "Offset für Pagination (default: 0)",
                            "default": 0
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="delete_model_predictions",
                description="Löscht ALLE Model-Predictions für ein Modell (aktiv UND inaktiv). ACHTUNG: Nicht rückgängig machbar!",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "active_model_id": {
                            "type": "integer",
                            "description": "ID des aktiven Modells"
                        }
                    },
                    "required": ["active_model_id"]
                }
            ),
            Tool(
                name="reset_model_statistics",
                description="Setzt die Statistiken eines Modells zurück (löscht alle Predictions). ACHTUNG: Nicht rückgängig machbar!",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "active_model_id": {
                            "type": "integer",
                            "description": "ID des aktiven Modells"
                        }
                    },
                    "required": ["active_model_id"]
                }
            ),
            Tool(
                name="get_coin_details",
                description="Holt detaillierte Coin-Informationen für ein Modell (Preishistorie, Predictions, Evaluierungen).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "active_model_id": {
                            "type": "integer",
                            "description": "ID des aktiven Modells"
                        },
                        "coin_id": {
                            "type": "string",
                            "description": "Coin-ID (Mint-Adresse)"
                        },
                        "start_timestamp": {
                            "type": "string",
                            "description": "Start-Zeitstempel ISO-Format (optional, default: 24h zurück)"
                        },
                        "end_timestamp": {
                            "type": "string",
                            "description": "End-Zeitstempel ISO-Format (optional, default: jetzt)"
                        }
                    },
                    "required": ["active_model_id", "coin_id"]
                }
            ),

            # === Configuration Tools ===
            Tool(
                name="update_alert_config",
                description="Aktualisiert die Alert-Konfiguration eines Modells (Webhook, Threshold, Filter).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "active_model_id": {
                            "type": "integer",
                            "description": "ID des aktiven Modells"
                        },
                        "n8n_webhook_url": {
                            "type": "string",
                            "description": "n8n Webhook URL (leer = deaktivieren)"
                        },
                        "n8n_enabled": {
                            "type": "boolean",
                            "description": "Webhook aktivieren/deaktivieren"
                        },
                        "n8n_send_mode": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["all", "alerts_only", "positive_only", "negative_only"]
                            },
                            "description": "Welche Vorhersagen gesendet werden"
                        },
                        "alert_threshold": {
                            "type": "number",
                            "description": "Alert-Schwellenwert 0.0-1.0"
                        },
                        "coin_filter_mode": {
                            "type": "string",
                            "enum": ["all", "whitelist"],
                            "description": "Coin-Filter Modus"
                        }
                    },
                    "required": ["active_model_id"]
                }
            ),
            Tool(
                name="get_model_statistics",
                description="Holt detaillierte Statistiken für ein Modell (Predictions, Alerts, Webhooks, Performance).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "active_model_id": {
                            "type": "integer",
                            "description": "ID des aktiven Modells"
                        }
                    },
                    "required": ["active_model_id"]
                }
            ),
            Tool(
                name="get_n8n_status",
                description="Prüft den n8n Webhook-Status für ein Modell (ok, error, unknown, no_url).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "active_model_id": {
                            "type": "integer",
                            "description": "ID des aktiven Modells"
                        }
                    },
                    "required": ["active_model_id"]
                }
            ),
            Tool(
                name="get_ignore_settings",
                description="Holt die Coin-Ignore-Einstellungen für ein Modell (Sekunden für bad/positive/alert Coins).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "active_model_id": {
                            "type": "integer",
                            "description": "ID des aktiven Modells"
                        }
                    },
                    "required": ["active_model_id"]
                }
            ),
            Tool(
                name="update_ignore_settings",
                description="Aktualisiert die Coin-Ignore-Einstellungen für ein Modell (0-86400 Sekunden).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "active_model_id": {
                            "type": "integer",
                            "description": "ID des aktiven Modells"
                        },
                        "ignore_bad_seconds": {
                            "type": "integer",
                            "description": "Sekunden, die negative Coins ignoriert werden (0-86400)"
                        },
                        "ignore_positive_seconds": {
                            "type": "integer",
                            "description": "Sekunden, die positive Coins ignoriert werden (0-86400)"
                        },
                        "ignore_alert_seconds": {
                            "type": "integer",
                            "description": "Sekunden, die Alert-Coins ignoriert werden (0-86400)"
                        }
                    },
                    "required": ["active_model_id", "ignore_bad_seconds", "ignore_positive_seconds", "ignore_alert_seconds"]
                }
            ),
            Tool(
                name="get_max_log_entries",
                description="Holt die Max-Log-Entries-Einstellungen für ein Modell (max. Einträge pro Coin pro Typ).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "active_model_id": {
                            "type": "integer",
                            "description": "ID des aktiven Modells"
                        }
                    },
                    "required": ["active_model_id"]
                }
            ),
            Tool(
                name="update_max_log_entries",
                description="Aktualisiert die Max-Log-Entries-Einstellungen für ein Modell (0-1000, 0=unbegrenzt).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "active_model_id": {
                            "type": "integer",
                            "description": "ID des aktiven Modells"
                        },
                        "max_log_entries_per_coin_negative": {
                            "type": "integer",
                            "description": "Max negative Einträge pro Coin (0-1000, 0=unbegrenzt)"
                        },
                        "max_log_entries_per_coin_positive": {
                            "type": "integer",
                            "description": "Max positive Einträge pro Coin (0-1000, 0=unbegrenzt)"
                        },
                        "max_log_entries_per_coin_alert": {
                            "type": "integer",
                            "description": "Max Alert-Einträge pro Coin (0-1000, 0=unbegrenzt)"
                        }
                    },
                    "required": ["active_model_id", "max_log_entries_per_coin_negative", "max_log_entries_per_coin_positive", "max_log_entries_per_coin_alert"]
                }
            ),

            # === Alert Tools ===
            Tool(
                name="get_alerts",
                description="Holt Alerts mit optionalen Filtern (Status, Modell, Coin, Datum). Unterstützt Pagination.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "enum": ["pending", "success", "failed", "expired"],
                            "description": "Filter nach Status (optional)"
                        },
                        "model_id": {
                            "type": "integer",
                            "description": "Filter nach active_model_id (optional)"
                        },
                        "coin_id": {
                            "type": "string",
                            "description": "Filter nach Coin-ID (optional)"
                        },
                        "prediction_type": {
                            "type": "string",
                            "enum": ["time_based", "classic"],
                            "description": "Filter nach Prediction-Typ (optional)"
                        },
                        "date_from": {
                            "type": "string",
                            "description": "Filter ab Datum ISO-Format (optional)"
                        },
                        "date_to": {
                            "type": "string",
                            "description": "Filter bis Datum ISO-Format (optional)"
                        },
                        "unique_coins": {
                            "type": "boolean",
                            "description": "Nur ältester Alert pro Coin (default: true)",
                            "default": True
                        },
                        "include_non_alerts": {
                            "type": "boolean",
                            "description": "Auch Predictions unter Alert-Threshold zeigen (default: false)",
                            "default": False
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Max. Anzahl Ergebnisse (default: 100)",
                            "default": 100
                        },
                        "offset": {
                            "type": "integer",
                            "description": "Offset für Pagination (default: 0)",
                            "default": 0
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="get_alert_details",
                description="Holt detaillierte Informationen zu einem bestimmten Alert (Metriken, Preishistorie, Evaluierung).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "alert_id": {
                            "type": "integer",
                            "description": "ID des Alerts"
                        },
                        "chart_before_minutes": {
                            "type": "integer",
                            "description": "Minuten vor Alert für Chart-Daten (default: 10)",
                            "default": 10
                        },
                        "chart_after_minutes": {
                            "type": "integer",
                            "description": "Minuten nach Evaluation für Chart-Daten (default: 10)",
                            "default": 10
                        }
                    },
                    "required": ["alert_id"]
                }
            ),
            Tool(
                name="get_alert_statistics",
                description="Holt Alert-Statistiken, optional gefiltert nach Modell und Zeitraum.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "model_id": {
                            "type": "integer",
                            "description": "Filter nach active_model_id (optional)"
                        },
                        "date_from": {
                            "type": "string",
                            "description": "Filter ab Datum ISO-Format (optional)"
                        },
                        "date_to": {
                            "type": "string",
                            "description": "Filter bis Datum ISO-Format (optional)"
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="get_all_models_alert_statistics",
                description="Holt Alert-Statistiken für alle oder ausgewählte aktive Modelle (optimierte Batch-Abfrage).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "active_model_ids": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Liste von active_model_ids (optional, wenn leer: alle aktiven Modelle)"
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="delete_model_alerts",
                description="Löscht alle Alert-Evaluierungen für ein Modell. ACHTUNG: Nicht rückgängig machbar!",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "active_model_id": {
                            "type": "integer",
                            "description": "ID des aktiven Modells"
                        }
                    },
                    "required": ["active_model_id"]
                }
            ),

            # === System Tools ===
            Tool(
                name="health_check",
                description="Prüft den Health-Status des Pump-Servers (DB-Verbindung, aktive Modelle, Uptime).",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_stats",
                description="Holt umfassende Service-Statistiken (Predictions, Modelle, Webhooks, Alerts).",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_system_config",
                description="Holt die aktuelle persistente Konfiguration (DB-URL, Training-Service-URL, n8n-URL etc.).",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="update_configuration",
                description="Speichert die persistente Konfiguration (database_url, training_service_url, n8n_webhook_url etc.).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "config": {
                            "type": "object",
                            "description": "Konfiguration als Dict mit Schlüsseln: database_url, training_service_url, n8n_webhook_url, api_port, streamlit_port"
                        }
                    },
                    "required": ["config"]
                }
            ),
            Tool(
                name="get_logs",
                description="Holt die letzten Log-Zeilen des Services (Docker-Logs oder Log-Dateien).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "tail": {
                            "type": "integer",
                            "description": "Anzahl der Log-Zeilen (default: 100)",
                            "default": 100
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="restart_system",
                description="Initiiert einen Service-Neustart über SIGTERM. Supervisor startet automatisch neu.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="delete_old_logs",
                description="Löscht ALLE alten Logs (alert_evaluations, predictions, model_predictions) für ein Modell. ACHTUNG: Nicht rückgängig!",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "active_model_id": {
                            "type": "integer",
                            "description": "ID des aktiven Modells"
                        }
                    },
                    "required": ["active_model_id"]
                }
            ),
            Tool(
                name="migrate_performance_metrics",
                description="Führt die DB-Migration für Performance-Metriken aus (fügt Spalten für Accuracy, F1 etc. hinzu).",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="debug_active_models",
                description="Debug: Zeigt alle aktiven Modelle mit vollständigen Details.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="debug_coin_metrics",
                description="Debug: Zeigt coin_metrics Statistiken (Gesamtanzahl, neuester/ältester Eintrag, unique Coins).",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
        ]

    @server.call_tool()
    async def handle_call_tool(
        name: str, arguments: dict | None
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        """
        Handles tool calls by dispatching to the appropriate tool implementation.
        """
        args = arguments or {}

        try:
            # === Model Tools ===
            if name == "list_active_models":
                result = await list_active_models(
                    include_inactive=args.get("include_inactive", False)
                )
            elif name == "list_available_models":
                result = await list_available_models()
            elif name == "import_model":
                result = await import_model(model_id=args["model_id"])
            elif name == "get_model_details":
                result = await get_model_details(active_model_id=args["active_model_id"])
            elif name == "activate_model":
                result = await activate_model(active_model_id=args["active_model_id"])
            elif name == "deactivate_model":
                result = await deactivate_model(active_model_id=args["active_model_id"])
            elif name == "rename_model":
                result = await rename_model(
                    active_model_id=args["active_model_id"],
                    new_name=args["new_name"]
                )
            elif name == "delete_model":
                result = await delete_model(active_model_id=args["active_model_id"])
            elif name == "update_model_metrics":
                result = await update_model_metrics(
                    active_model_id=args["active_model_id"],
                    model_id=args["model_id"]
                )

            # === Prediction Tools ===
            elif name == "predict_coin":
                result = await predict_coin(
                    coin_id=args["coin_id"],
                    model_ids=args.get("model_ids")
                )
            elif name == "get_predictions":
                result = await get_predictions(
                    coin_id=args.get("coin_id"),
                    active_model_id=args.get("active_model_id"),
                    prediction=args.get("prediction"),
                    min_probability=args.get("min_probability"),
                    limit=args.get("limit", 50),
                    offset=args.get("offset", 0)
                )
            elif name == "get_latest_prediction":
                result = await get_latest_prediction(
                    coin_id=args["coin_id"],
                    model_id=args.get("model_id")
                )
            elif name == "get_model_predictions":
                result = await get_model_predictions(
                    active_model_id=args.get("active_model_id"),
                    tag=args.get("tag"),
                    status=args.get("status"),
                    coin_id=args.get("coin_id"),
                    limit=args.get("limit", 100),
                    offset=args.get("offset", 0)
                )
            elif name == "delete_model_predictions":
                result = await delete_model_predictions(
                    active_model_id=args["active_model_id"]
                )
            elif name == "reset_model_statistics":
                result = await reset_model_statistics(
                    active_model_id=args["active_model_id"]
                )
            elif name == "get_coin_details":
                result = await get_coin_details(
                    active_model_id=args["active_model_id"],
                    coin_id=args["coin_id"],
                    start_timestamp=args.get("start_timestamp"),
                    end_timestamp=args.get("end_timestamp")
                )

            # === Configuration Tools ===
            elif name == "update_alert_config":
                result = await update_alert_config(
                    active_model_id=args["active_model_id"],
                    n8n_webhook_url=args.get("n8n_webhook_url"),
                    n8n_enabled=args.get("n8n_enabled"),
                    n8n_send_mode=args.get("n8n_send_mode"),
                    alert_threshold=args.get("alert_threshold"),
                    coin_filter_mode=args.get("coin_filter_mode"),
                    coin_whitelist=args.get("coin_whitelist"),
                    min_scan_interval_seconds=args.get("min_scan_interval_seconds")
                )
            elif name == "get_model_statistics":
                result = await get_model_statistics(active_model_id=args["active_model_id"])
            elif name == "get_n8n_status":
                result = await get_n8n_status(active_model_id=args["active_model_id"])
            elif name == "get_ignore_settings":
                result = await get_ignore_settings(active_model_id=args["active_model_id"])
            elif name == "update_ignore_settings":
                result = await update_ignore_settings(
                    active_model_id=args["active_model_id"],
                    ignore_bad_seconds=args["ignore_bad_seconds"],
                    ignore_positive_seconds=args["ignore_positive_seconds"],
                    ignore_alert_seconds=args["ignore_alert_seconds"]
                )
            elif name == "get_max_log_entries":
                result = await get_max_log_entries(active_model_id=args["active_model_id"])
            elif name == "update_max_log_entries":
                result = await update_max_log_entries(
                    active_model_id=args["active_model_id"],
                    max_log_entries_per_coin_negative=args["max_log_entries_per_coin_negative"],
                    max_log_entries_per_coin_positive=args["max_log_entries_per_coin_positive"],
                    max_log_entries_per_coin_alert=args["max_log_entries_per_coin_alert"]
                )

            # === Alert Tools ===
            elif name == "get_alerts":
                result = await get_alerts(
                    status=args.get("status"),
                    model_id=args.get("model_id"),
                    coin_id=args.get("coin_id"),
                    prediction_type=args.get("prediction_type"),
                    date_from=args.get("date_from"),
                    date_to=args.get("date_to"),
                    unique_coins=args.get("unique_coins", True),
                    include_non_alerts=args.get("include_non_alerts", False),
                    limit=args.get("limit", 100),
                    offset=args.get("offset", 0)
                )
            elif name == "get_alert_details":
                result = await get_alert_details(
                    alert_id=args["alert_id"],
                    chart_before_minutes=args.get("chart_before_minutes", 10),
                    chart_after_minutes=args.get("chart_after_minutes", 10)
                )
            elif name == "get_alert_statistics":
                result = await get_alert_statistics(
                    model_id=args.get("model_id"),
                    date_from=args.get("date_from"),
                    date_to=args.get("date_to")
                )
            elif name == "get_all_models_alert_statistics":
                result = await get_all_models_alert_statistics(
                    active_model_ids=args.get("active_model_ids")
                )
            elif name == "delete_model_alerts":
                result = await delete_model_alerts(
                    active_model_id=args["active_model_id"]
                )

            # === System Tools ===
            elif name == "health_check":
                result = await health_check()
            elif name == "get_stats":
                result = await get_stats()
            elif name == "get_system_config":
                result = await get_system_config()
            elif name == "update_configuration":
                result = await update_configuration(config=args["config"])
            elif name == "get_logs":
                result = await get_logs(tail=args.get("tail", 100))
            elif name == "restart_system":
                result = await restart_system()
            elif name == "delete_old_logs":
                result = await delete_old_logs(active_model_id=args["active_model_id"])
            elif name == "migrate_performance_metrics":
                result = await migrate_performance_metrics()
            elif name == "debug_active_models":
                result = await debug_active_models()
            elif name == "debug_coin_metrics":
                result = await debug_coin_metrics()
            else:
                result = {"error": f"Unknown tool: {name}"}

            # Return result as JSON
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, default=str)
            )]

        except Exception as e:
            logger.error(f"Error calling tool {name}: {e}", exc_info=True)
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": str(e)
                }, indent=2)
            )]

    return server


# Singleton instance
_mcp_server: Server | None = None


def get_mcp_server() -> Server:
    """Returns the singleton MCP server instance."""
    global _mcp_server
    if _mcp_server is None:
        _mcp_server = create_mcp_server()
    return _mcp_server


class PumpServerMCP:
    """
    Wrapper class for the MCP server.
    Provides a cleaner interface for integration with FastAPI.
    """

    def __init__(self):
        self.server = get_mcp_server()

    def get_tool_list(self) -> list[dict]:
        """Returns list of tools with their schemas."""
        return [
            # Models
            {"name": "list_active_models", "description": "Liste aktiver ML-Modelle"},
            {"name": "list_available_models", "description": "Verfügbare Modelle zum Import"},
            {"name": "import_model", "description": "Modell importieren"},
            {"name": "get_model_details", "description": "Modell-Details abrufen"},
            {"name": "activate_model", "description": "Modell aktivieren"},
            {"name": "deactivate_model", "description": "Modell deaktivieren"},
            {"name": "rename_model", "description": "Modell umbenennen"},
            {"name": "delete_model", "description": "Modell löschen"},
            {"name": "update_model_metrics", "description": "Performance-Metriken aktualisieren"},
            # Predictions
            {"name": "predict_coin", "description": "Vorhersage für Coin"},
            {"name": "get_predictions", "description": "Vorhersagen abrufen"},
            {"name": "get_latest_prediction", "description": "Neueste Vorhersage"},
            {"name": "get_model_predictions", "description": "Model-Predictions abrufen"},
            {"name": "delete_model_predictions", "description": "Model-Predictions löschen"},
            {"name": "reset_model_statistics", "description": "Modell-Statistiken zurücksetzen"},
            {"name": "get_coin_details", "description": "Coin-Details abrufen"},
            # Configuration
            {"name": "update_alert_config", "description": "Alert-Konfiguration ändern"},
            {"name": "get_model_statistics", "description": "Modell-Statistiken"},
            {"name": "get_n8n_status", "description": "n8n Webhook-Status prüfen"},
            {"name": "get_ignore_settings", "description": "Ignore-Einstellungen abrufen"},
            {"name": "update_ignore_settings", "description": "Ignore-Einstellungen ändern"},
            {"name": "get_max_log_entries", "description": "Max-Log-Entries abrufen"},
            {"name": "update_max_log_entries", "description": "Max-Log-Entries ändern"},
            # Alerts
            {"name": "get_alerts", "description": "Alerts abrufen"},
            {"name": "get_alert_details", "description": "Alert-Details abrufen"},
            {"name": "get_alert_statistics", "description": "Alert-Statistiken"},
            {"name": "get_all_models_alert_statistics", "description": "Alert-Statistiken aller Modelle"},
            {"name": "delete_model_alerts", "description": "Alert-Evaluierungen löschen"},
            # System
            {"name": "health_check", "description": "Health-Status prüfen"},
            {"name": "get_stats", "description": "Service-Statistiken"},
            {"name": "get_system_config", "description": "Konfiguration abrufen"},
            {"name": "update_configuration", "description": "Konfiguration speichern"},
            {"name": "get_logs", "description": "Logs abrufen"},
            {"name": "restart_system", "description": "System neu starten"},
            {"name": "delete_old_logs", "description": "Alte Logs löschen"},
            {"name": "migrate_performance_metrics", "description": "DB-Migration ausführen"},
            {"name": "debug_active_models", "description": "Debug: Aktive Modelle"},
            {"name": "debug_coin_metrics", "description": "Debug: Coin-Metriken"},
        ]

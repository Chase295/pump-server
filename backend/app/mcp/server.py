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
    # Predictions
    predict_coin,
    get_predictions,
    get_latest_prediction,
    # Configuration
    update_alert_config,
    get_model_statistics,
    # System
    health_check,
    get_stats,
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
            # Dispatch to appropriate tool
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
            elif name == "health_check":
                result = await health_check()
            elif name == "get_stats":
                result = await get_stats()
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
            {
                "name": "list_active_models",
                "description": "Liste aktiver ML-Modelle",
            },
            {
                "name": "list_available_models",
                "description": "Verfügbare Modelle zum Import",
            },
            {
                "name": "import_model",
                "description": "Modell importieren",
            },
            {
                "name": "get_model_details",
                "description": "Modell-Details abrufen",
            },
            {
                "name": "activate_model",
                "description": "Modell aktivieren",
            },
            {
                "name": "deactivate_model",
                "description": "Modell deaktivieren",
            },
            {
                "name": "predict_coin",
                "description": "Vorhersage für Coin",
            },
            {
                "name": "get_predictions",
                "description": "Vorhersagen abrufen",
            },
            {
                "name": "get_latest_prediction",
                "description": "Neueste Vorhersage",
            },
            {
                "name": "update_alert_config",
                "description": "Alert-Konfiguration ändern",
            },
            {
                "name": "get_model_statistics",
                "description": "Modell-Statistiken",
            },
            {
                "name": "health_check",
                "description": "Health-Status prüfen",
            },
            {
                "name": "get_stats",
                "description": "Service-Statistiken",
            },
        ]

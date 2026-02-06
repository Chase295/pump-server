# MCP Server Integration in FastAPI - Anleitung

Diese Anleitung beschreibt, wie ein MCP (Model Context Protocol) Server mit der **offiziellen MCP SDK** in eine bestehende FastAPI-Anwendung integriert wird. Basierend auf der funktionierenden Implementierung im pump-server.

> **Hinweis:** Diese Anleitung zeigt echten, funktionierenden Code. Sie kann direkt als Vorlage fuer andere FastAPI-Projekte verwendet werden.

---

## 1. Voraussetzungen & Dependencies

**`requirements.txt`:**

```txt
# MCP Server (Model Context Protocol)
mcp>=1.0.0

# WICHTIG: FastAPI und Uvicorn muessen aktuell sein wegen anyio>=4.5
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
anyio>=4.5.0
pydantic>=2.5.0

# SSE-Starlette wird von mcp als Dependency mitgebracht,
# aber starlette.routing.Route wird direkt verwendet.
```

**Wichtig:** Die MCP SDK erfordert `anyio>=4.5`, was mit aelteren FastAPI-Versionen (< 0.115) nicht kompatibel ist.

---

## 2. Projektstruktur

```
backend/
├── app/
│   ├── mcp/                      # MCP-Modul
│   │   ├── __init__.py           # Modul-Initialisierung
│   │   ├── server.py             # MCP Server mit offizieller SDK
│   │   ├── routes.py             # SSE Transport + FastAPI Endpoints
│   │   └── tools/                # Tool-Implementierungen
│   │       ├── __init__.py       # Re-Exports aller Tools
│   │       ├── models.py         # Model-Management Tools
│   │       ├── predictions.py    # Prediction Tools
│   │       ├── configuration.py  # Config Tools
│   │       ├── alerts.py         # Alert Tools
│   │       └── system.py         # System Tools
│   ├── main.py                   # FastAPI App (wird erweitert)
│   └── ...
```

---

## 3. Server erstellen (`server.py`)

Die offizielle MCP SDK stellt eine `Server`-Klasse bereit, die mit Decoratorn arbeitet:

```python
"""
MCP Server Implementation
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

# Import Tool-Implementierungen
from app.mcp.tools import (
    list_active_models,
    predict_coin,
    health_check,
    # ... weitere Tools
)

logger = logging.getLogger(__name__)


def create_mcp_server() -> Server:
    """
    Creates and configures the MCP server instance.
    """
    server = Server("dein-service-mcp")

    @server.list_tools()
    async def handle_list_tools() -> list[Tool]:
        """Returns the list of available tools."""
        return [
            Tool(
                name="list_active_models",
                description="Liste aller aktiven ML-Modelle",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "include_inactive": {
                            "type": "boolean",
                            "description": "Auch inaktive Modelle anzeigen",
                            "default": False
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="predict_coin",
                description="Macht eine Vorhersage fuer einen Coin",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "coin_id": {
                            "type": "string",
                            "description": "Coin-ID (Mint-Adresse)"
                        }
                    },
                    "required": ["coin_id"]
                }
            ),
            # ... weitere Tools
        ]

    @server.call_tool()
    async def handle_call_tool(
        name: str, arguments: dict | None
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        """Dispatches tool calls to implementations."""
        args = arguments or {}

        try:
            if name == "list_active_models":
                result = await list_active_models(
                    include_inactive=args.get("include_inactive", False)
                )
            elif name == "predict_coin":
                result = await predict_coin(coin_id=args["coin_id"])
            # ... weitere Tools
            else:
                result = {"error": f"Unknown tool: {name}"}

            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, default=str)
            )]

        except Exception as e:
            logger.error(f"Error calling tool {name}: {e}", exc_info=True)
            return [TextContent(
                type="text",
                text=json.dumps({"success": False, "error": str(e)}, indent=2)
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
    Provides a cleaner interface for info/health endpoints.
    """

    def __init__(self):
        self.server = get_mcp_server()

    def get_tool_list(self) -> list[dict]:
        """Returns list of tools with their schemas."""
        return [
            {"name": "list_active_models", "description": "Liste aktiver ML-Modelle"},
            {"name": "predict_coin", "description": "Vorhersage fuer Coin"},
            # ... alle Tools auflisten
        ]
```

### Kernkonzepte

| Konzept | Beschreibung |
|---------|-------------|
| `Server("name")` | Offizielle MCP Server-Instanz aus `mcp.server` |
| `@server.list_tools()` | Decorator, der die Tool-Liste zurueckgibt |
| `@server.call_tool()` | Decorator, der Tool-Aufrufe dispatched |
| `Tool(name, description, inputSchema)` | Tool-Definition aus `mcp.types` |
| `TextContent(type="text", text=...)` | Response-Format fuer Tool-Ergebnisse |
| Singleton Pattern | Nur eine Server-Instanz pro Prozess |

---

## 4. SSE Transport Routes (`routes.py`)

Die MCP-Kommunikation laeuft ueber SSE (Server-Sent Events). Die offizielle SDK stellt `SseServerTransport` bereit, das **direkt mit ASGI** arbeitet und FastAPIs Response-Handling umgeht.

```python
"""
MCP Routes for FastAPI

Uses the official MCP SDK's SseServerTransport for SSE handling.
"""
import logging
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.routing import Route
from mcp.server.sse import SseServerTransport

from app.mcp.server import get_mcp_server, PumpServerMCP

logger = logging.getLogger(__name__)

# SSE Transport - singleton
_sse_transport: SseServerTransport | None = None


def get_sse_transport() -> SseServerTransport:
    """Returns the singleton SSE transport instance."""
    global _sse_transport
    if _sse_transport is None:
        # Der Pfad ist der POST-Endpoint fuer Messages
        _sse_transport = SseServerTransport("/mcp/messages/")
    return _sse_transport


async def handle_sse(request: Request):
    """
    Handle SSE connections for MCP.
    Main entry point for MCP clients connecting via SSE.
    """
    logger.info("MCP SSE connection established")

    server = get_mcp_server()
    transport = get_sse_transport()

    async with transport.connect_sse(
        request.scope,
        request.receive,
        request._send
    ) as streams:
        await server.run(
            streams[0],  # read stream
            streams[1],  # write stream
            server.create_initialization_options()
        )


async def handle_messages(request: Request):
    """
    Handle POST messages for MCP.
    JSON-RPC messages from clients are sent here.
    """
    logger.debug("MCP message received")

    transport = get_sse_transport()
    await transport.handle_post_message(
        request.scope,
        request.receive,
        request._send
    )


# Regular FastAPI router for /mcp/info and /mcp/health
router = APIRouter(prefix="/mcp", tags=["MCP"])


@router.get("/info")
async def mcp_info() -> dict[str, Any]:
    """Returns MCP server information and tool list."""
    mcp = PumpServerMCP()
    return {
        "name": "dein-service-mcp",
        "version": "1.0.0",
        "description": "MCP Server fuer deinen Service",
        "transport": "sse",
        "sse_endpoint": "/mcp/sse",
        "messages_endpoint": "/mcp/messages/",
        "tools": mcp.get_tool_list(),
        "tools_count": len(mcp.get_tool_list()),
    }


@router.get("/health")
async def mcp_health():
    """Health check endpoint for MCP server."""
    from app.mcp.tools.system import health_check
    result = await health_check()
    return result


def get_sse_routes():
    """
    Returns SSE-specific routes that need direct ASGI handling.

    WICHTIG: Diese Routes umgehen FastAPIs Response-Handling,
    weil SSE direkt auf das ASGI-Send-Interface streamen muss.
    Deshalb werden sie als starlette.routing.Route erstellt,
    nicht als FastAPI-Endpoints.
    """
    return [
        Route("/mcp/sse", endpoint=handle_sse, methods=["GET"]),
        Route("/mcp/messages/", endpoint=handle_messages, methods=["POST"]),
    ]
```

### Warum zwei Arten von Routes?

| Route-Typ | Verwendung | Grund |
|-----------|-----------|-------|
| `APIRouter` (FastAPI) | `/mcp/info`, `/mcp/health` | Normale JSON-Responses, FastAPI-Features (Swagger, Validation) |
| `starlette.routing.Route` | `/mcp/sse`, `/mcp/messages/` | SSE braucht direkten ASGI-Zugriff (`request._send`), FastAPI wuerde den Stream unterbrechen |

---

## 5. FastAPI Integration (`main.py`)

Die Integration in `main.py` erfolgt in zwei Schritten:

```python
from app.mcp.routes import router as mcp_router, get_sse_routes

# 1. Regular FastAPI router for /mcp/info and /mcp/health
app.include_router(mcp_router)

# 2. SSE routes need direct ASGI handling (bypass FastAPI response handling)
for route in get_sse_routes():
    app.routes.append(route)
```

**Wichtig:** Die SSE-Routes werden mit `app.routes.append()` hinzugefuegt, NICHT mit `app.include_router()`. Das ist notwendig, weil `SseServerTransport` direkt auf die ASGI-Schicht zugreift.

### Vollstaendiges Beispiel

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.mcp.routes import router as mcp_router, get_sse_routes

app = FastAPI(title="Dein Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REST API
app.include_router(router)

# MCP Server
app.include_router(mcp_router)      # /mcp/info, /mcp/health
for route in get_sse_routes():       # /mcp/sse, /mcp/messages/
    app.routes.append(route)

@app.on_event("startup")
async def startup():
    logger.info("MCP Server verfuegbar unter /mcp/sse")
```

---

## 6. Tools schreiben

Tools sind async-Funktionen, die bestehende Service-/DB-Funktionen aufrufen und ein Dict zurueckgeben:

```python
"""
MCP Tools fuer Model-Verwaltung
"""
import logging
from typing import Any, Dict

from app.database.models import (
    get_active_models as db_get_active_models,
    import_model as db_import_model,
)

logger = logging.getLogger(__name__)


async def list_active_models(include_inactive: bool = False) -> Dict[str, Any]:
    """Liste aller aktiven ML-Modelle."""
    try:
        models = await db_get_active_models(include_inactive=include_inactive)
        return {
            "success": True,
            "models": models,
            "total": len(models)
        }
    except Exception as e:
        logger.error(f"Fehler: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


async def import_model(model_id: int) -> Dict[str, Any]:
    """Importiert ein Modell."""
    result = await db_import_model(model_id)
    return result
```

### Wichtiges Pattern

- Tools rufen **bestehende Service-Funktionen** auf (kein Code duplizieren!)
- Jedes Tool gibt ein Dict zurueck (wird in `server.py` zu JSON serialisiert)
- Fehlerbehandlung in jedem Tool

---

## 7. Tools exportieren (`tools/__init__.py`)

```python
"""
MCP Tools Package
"""
from app.mcp.tools.models import (
    list_active_models,
    list_available_models,
    import_model,
    # ...
)
from app.mcp.tools.predictions import (
    predict_coin,
    get_predictions,
    # ...
)
from app.mcp.tools.configuration import (
    update_alert_config,
    get_model_statistics,
    # ...
)
from app.mcp.tools.alerts import (
    get_alerts,
    get_alert_details,
    # ...
)
from app.mcp.tools.system import (
    health_check,
    get_stats,
    # ...
)

__all__ = [
    "list_active_models",
    "list_available_models",
    "import_model",
    "predict_coin",
    "get_predictions",
    # ... alle Tool-Funktionen
]
```

---

## 8. Nginx Konfiguration (fuer SSE)

SSE-Verbindungen benoetigen spezielle Nginx-Einstellungen:

```nginx
# MCP-Proxy - alle /mcp/* Anfragen gehen an Backend
location /mcp/ {
    proxy_pass http://backend:8000/mcp/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # SSE-spezifische Einstellungen (WICHTIG!)
    proxy_set_header Connection "";
    proxy_http_version 1.1;
    proxy_buffering off;        # Kein Buffering fuer SSE-Streams!
    proxy_cache off;            # Kein Caching!
    proxy_read_timeout 86400s;  # 24h fuer lange SSE-Verbindungen
}
```

**Kritische Einstellungen:**
- `proxy_buffering off` - Ohne das werden SSE-Events gepuffert und kommen nicht durch
- `proxy_read_timeout 86400s` - Standard-Timeout (60s) wuerde SSE-Verbindung trennen
- `proxy_http_version 1.1` + `Connection ""` - Ermoeglicht Keep-Alive

---

## 9. Client-Konfiguration

### `.mcp.json` im Projektroot (fuer Claude Code)

```json
{
  "mcpServers": {
    "dein-service": {
      "type": "sse",
      "url": "https://dein-service.example.com/mcp/sse"
    }
  }
}
```

### Claude Desktop Konfiguration

Datei: `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)

```json
{
  "mcpServers": {
    "dein-service": {
      "transport": "sse",
      "url": "https://dein-service.example.com/mcp/sse"
    }
  }
}
```

### Cursor IDE

Datei: `~/.cursor/mcp.json`

```json
{
  "mcpServers": {
    "dein-service": {
      "transport": "sse",
      "url": "https://dein-service.example.com/mcp/sse"
    }
  }
}
```

---

## 10. Verifikation

```bash
# 1. MCP Info testen
curl http://localhost:3003/mcp/info
# Erwartete Ausgabe: {"name": "...", "tools_count": 38, ...}

# 2. Health Check
curl http://localhost:3003/mcp/health

# 3. SSE-Verbindung testen
curl -N http://localhost:3003/mcp/sse
# Sollte "event: endpoint" mit der Messages-URL zurueckgeben
# Dann: data: /mcp/messages/?session_id=...
```

---

## 11. Architektur-Diagramm

```
┌──────────────────────────────────────────────────────────────┐
│                   Claude Code / KI-Client                     │
└────────────────────────┬─────────────────────────────────────┘
                         │ SSE + JSON-RPC
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                   Nginx (Port 3003)                           │
│  ┌──────────┐  ┌──────────┐  ┌────────────────────────────┐  │
│  │  /api/*  │  │  /mcp/*  │  │       /* (SPA)             │  │
│  └────┬─────┘  └────┬─────┘  └────────────────────────────┘  │
└───────┼──────────────┼───────────────────────────────────────┘
        │              │
        ▼              ▼
┌──────────────────────────────────────────────────────────────┐
│                 FastAPI Backend (Port 8000)                    │
│                                                               │
│  ┌────────────────┐       ┌────────────────────────────────┐  │
│  │   REST API     │       │         MCP Server             │  │
│  │   /api/...     │       │                                │  │
│  └───────┬────────┘       │  /mcp/info    (FastAPI Router) │  │
│          │                │  /mcp/health  (FastAPI Router)  │  │
│          │                │  /mcp/sse     (ASGI Route)     │  │
│          │                │  /mcp/messages/ (ASGI Route)   │  │
│          │                │                                │  │
│          │                │  ┌──────────────────────────┐   │  │
│          │                │  │  mcp.server.Server       │   │  │
│          │                │  │  + SseServerTransport    │   │  │
│          │                │  └───────────┬──────────────┘   │  │
│          │                │              │                  │  │
│          │                │  ┌───────────▼──────────────┐   │  │
│          │                │  │   tools/                 │   │  │
│          │                │  │   ├── models.py          │   │  │
│          │                │  │   ├── predictions.py     │   │  │
│          │                │  │   ├── configuration.py   │   │  │
│          │                │  │   ├── alerts.py          │   │  │
│          │                │  │   └── system.py          │   │  │
│          │                │  └──────────────────────────┘   │  │
│          │                └────────────────┬────────────────┘  │
│          │                                │                   │
│          ▼                                ▼                   │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                   Service Layer                          │  │
│  │          (Bestehende Business-Logik nutzen!)             │  │
│  └─────────────────────────┬───────────────────────────────┘  │
└────────────────────────────┼──────────────────────────────────┘
                             ▼
                   ┌─────────────────┐
                   │   PostgreSQL    │
                   └─────────────────┘
```

---

## 12. Checkliste fuer neue Projekte

- [ ] Dependencies in `requirements.txt` (`mcp>=1.0.0`, `fastapi>=0.115.0`, `anyio>=4.5.0`)
- [ ] MCP-Modul erstellen (`app/mcp/`)
- [ ] `server.py` mit offizieller SDK (`from mcp.server import Server`)
- [ ] `@server.list_tools()` und `@server.call_tool()` Decorator implementieren
- [ ] `routes.py` mit `SseServerTransport` aus `mcp.server.sse`
- [ ] `get_sse_routes()` gibt `starlette.routing.Route` zurueck
- [ ] Tools in `tools/` - async Funktionen die bestehende Services aufrufen
- [ ] `tools/__init__.py` - Alle Tool-Funktionen re-exportieren
- [ ] `main.py`: `app.include_router(mcp_router)` + `app.routes.append(route)`
- [ ] Nginx-Config: `proxy_buffering off`, `proxy_read_timeout 86400s`
- [ ] `.mcp.json` im Projektroot erstellen
- [ ] Testen: `curl /mcp/info`, `curl /mcp/health`, `curl -N /mcp/sse`

---

## Haeufige Fehler

| Problem | Ursache | Loesung |
|---------|---------|---------|
| SSE-Verbindung bricht sofort ab | FastAPI fängt Response ab | SSE-Routes als `starlette.routing.Route` mit `app.routes.append()` hinzufuegen |
| `anyio` Version Conflict | Alte FastAPI-Version | FastAPI >= 0.115.0 und anyio >= 4.5 verwenden |
| Tools werden nicht erkannt | Client-Config falsch | `.mcp.json` pruefen, Client neu starten |
| SSE-Events kommen nicht an | Nginx buffert | `proxy_buffering off` in Nginx-Config |
| Timeout nach 60s | Nginx Standard-Timeout | `proxy_read_timeout 86400s` setzen |

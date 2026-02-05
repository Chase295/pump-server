# MCP Server Integration in FastAPI

Diese Anleitung beschreibt, wie ein MCP (Model Context Protocol) Server in eine bestehende FastAPI-Anwendung integriert wird. Das MCP-Protokoll von Anthropic ermöglicht KI-Clients wie Claude Code den direkten Zugriff auf Service-Funktionen.

## 1. Projektstruktur

```
backend/
├── app/
│   ├── mcp/                      # Neues MCP-Modul
│   │   ├── __init__.py           # Modul-Initialisierung
│   │   ├── server.py             # MCP Server Hauptlogik
│   │   ├── routes.py             # FastAPI Endpoints
│   │   └── tools/                # Tool-Definitionen
│   │       ├── __init__.py
│   │       ├── models.py         # Model-bezogene Tools
│   │       ├── predictions.py    # Prediction-Tools
│   │       ├── configuration.py  # Config-Tools
│   │       └── system.py         # System-Tools
│   ├── main.py                   # FastAPI App (wird erweitert)
│   └── ...
├── requirements.txt              # Dependencies (wird erweitert)
```

## 2. Dependencies hinzufügen

**Datei: `backend/requirements.txt`**

```txt
# Bestehende Dependencies...

# MCP Server (Model Context Protocol)
mcp>=1.0.0
sse-starlette>=1.6.5

# WICHTIG: FastAPI und uvicorn müssen aktualisiert werden wegen anyio>=4.5
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
anyio>=4.5.0
pydantic>=2.5.0
```

**Hinweis:** MCP erfordert `anyio>=4.5`, was mit älteren FastAPI-Versionen (< 0.115) nicht kompatibel ist.

## 3. MCP-Modul erstellen

### 3.1 `backend/app/mcp/__init__.py`

```python
"""
MCP (Model Context Protocol) Server Module

Ermöglicht KI-Clients wie Claude Code den direkten Zugriff auf Service-Funktionen.
"""

from .server import MCPServer
from .routes import router

__all__ = ["MCPServer", "router"]
```

### 3.2 `backend/app/mcp/server.py`

```python
"""
MCP Server Implementation

Hauptlogik für den MCP Server mit Tool-Registry und Dispatcher.
"""

import json
import uuid
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime

from app.utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class MCPTool:
    """Definition eines MCP Tools"""
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Callable


@dataclass
class MCPServer:
    """MCP Server mit Tool-Registry"""

    name: str = "pump-server"
    version: str = "1.0.0"
    tools: Dict[str, MCPTool] = field(default_factory=dict)
    sessions: Dict[str, Dict] = field(default_factory=dict)

    def register_tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable
    ) -> None:
        """Registriert ein neues Tool"""
        self.tools[name] = MCPTool(
            name=name,
            description=description,
            parameters=parameters,
            handler=handler
        )
        logger.debug(f"Tool registriert: {name}")

    def get_tools_list(self) -> List[Dict[str, Any]]:
        """Gibt Liste aller Tools für MCP zurück"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": {
                    "type": "object",
                    "properties": tool.parameters.get("properties", {}),
                    "required": tool.parameters.get("required", [])
                }
            }
            for tool in self.tools.values()
        ]

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Ruft ein Tool auf und gibt das Ergebnis zurück"""
        if name not in self.tools:
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"Tool nicht gefunden: {name}"}]
            }

        tool = self.tools[name]

        try:
            result = await tool.handler(**arguments)

            # Ergebnis als JSON-Text formatieren
            if isinstance(result, dict) or isinstance(result, list):
                text_content = json.dumps(result, indent=2, default=str, ensure_ascii=False)
            else:
                text_content = str(result)

            return {
                "content": [{"type": "text", "text": text_content}]
            }

        except Exception as e:
            logger.error(f"Tool-Fehler {name}: {e}", exc_info=True)
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"Fehler: {str(e)}"}]
            }

    def create_session(self) -> str:
        """Erstellt eine neue MCP-Session"""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "created_at": datetime.utcnow().isoformat(),
            "initialized": False
        }
        logger.info(f"Neue MCP-Session: {session_id}")
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Holt Session-Daten"""
        return self.sessions.get(session_id)

    def mark_initialized(self, session_id: str) -> None:
        """Markiert Session als initialisiert"""
        if session_id in self.sessions:
            self.sessions[session_id]["initialized"] = True

    async def handle_message(self, session_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Verarbeitet eine JSON-RPC Nachricht"""
        method = message.get("method", "")
        msg_id = message.get("id")
        params = message.get("params", {})

        logger.debug(f"MCP Message: {method} (Session: {session_id[:8]}...)")

        # Initialize
        if method == "initialize":
            self.mark_initialized(session_id)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": self.name,
                        "version": self.version
                    }
                }
            }

        # Notifications (kein Response)
        if method == "notifications/initialized":
            return None

        # Tools auflisten
        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": self.get_tools_list()
                }
            }

        # Tool aufrufen
        if method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})

            result = await self.call_tool(tool_name, arguments)

            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": result
            }

        # Ping
        if method == "ping":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {}
            }

        # Unbekannte Methode
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}"
            }
        }


# Globale MCP Server Instanz
mcp_server = MCPServer()


def get_mcp_server() -> MCPServer:
    """Gibt die globale MCP Server Instanz zurück"""
    return mcp_server
```

### 3.3 `backend/app/mcp/routes.py`

```python
"""
MCP Server FastAPI Routes

Endpoints für SSE-Kommunikation und Server-Info.
"""

import json
import asyncio
from typing import Dict, Any
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

from app.utils.logging_config import get_logger
from .server import get_mcp_server

# Tools importieren und registrieren
from .tools import models, predictions, configuration, system

logger = get_logger(__name__)

router = APIRouter(prefix="/mcp", tags=["MCP"])


def register_all_tools():
    """Registriert alle MCP Tools"""
    server = get_mcp_server()

    # Model-Tools
    models.register_tools(server)

    # Prediction-Tools
    predictions.register_tools(server)

    # Configuration-Tools
    configuration.register_tools(server)

    # System-Tools
    system.register_tools(server)

    logger.info(f"✅ {len(server.tools)} MCP Tools registriert")


# Tools beim Import registrieren
register_all_tools()


@router.get("/info")
async def mcp_info():
    """MCP Server Informationen und Tool-Liste"""
    server = get_mcp_server()

    return {
        "name": server.name,
        "version": server.version,
        "protocol": "MCP",
        "transport": "SSE",
        "tools_count": len(server.tools),
        "tools": [
            {
                "name": tool.name,
                "description": tool.description
            }
            for tool in server.tools.values()
        ]
    }


@router.get("/health")
async def mcp_health():
    """MCP Server Health Check"""
    server = get_mcp_server()

    return {
        "status": "healthy",
        "tools_registered": len(server.tools),
        "active_sessions": len(server.sessions)
    }


@router.get("/sse")
async def mcp_sse(request: Request):
    """SSE Endpoint für MCP Client-Verbindungen"""
    server = get_mcp_server()
    session_id = server.create_session()

    logger.info(f"🔌 Neue MCP SSE-Verbindung: {session_id[:8]}...")

    async def event_generator():
        # Endpoint-URL für POST-Messages senden
        endpoint_url = f"/mcp/sse?session_id={session_id}"
        yield {
            "event": "endpoint",
            "data": endpoint_url
        }

        # Verbindung offen halten
        try:
            while True:
                if await request.is_disconnected():
                    break
                await asyncio.sleep(30)
                # Keepalive
                yield {
                    "event": "ping",
                    "data": "{}"
                }
        except asyncio.CancelledError:
            pass
        finally:
            logger.info(f"🔌 MCP SSE-Verbindung beendet: {session_id[:8]}...")

    return EventSourceResponse(event_generator())


@router.post("/sse")
async def mcp_message(request: Request):
    """Empfängt JSON-RPC Messages vom MCP Client"""
    server = get_mcp_server()

    # Session-ID aus Query-Parameter
    session_id = request.query_params.get("session_id", "")

    if not session_id or not server.get_session(session_id):
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid session"}
        )

    try:
        body = await request.json()
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": f"Invalid JSON: {e}"}
        )

    # Message verarbeiten
    response = await server.handle_message(session_id, body)

    if response is None:
        # Notification - kein Response
        return Response(status_code=202)

    return JSONResponse(content=response)
```

### 3.4 Tools-Modul: `backend/app/mcp/tools/__init__.py`

```python
"""
MCP Tools Module

Enthält alle Tool-Definitionen für den MCP Server.
"""

from . import models
from . import predictions
from . import configuration
from . import system

__all__ = ["models", "predictions", "configuration", "system"]
```

### 3.5 Beispiel Tool-Datei: `backend/app/mcp/tools/models.py`

```python
"""
MCP Tools für Model-Verwaltung
"""

from typing import Optional
from app.database.models import (
    get_active_models,
    get_available_models,
    import_model as db_import_model,
    activate_model as db_activate_model,
    deactivate_model as db_deactivate_model
)


def register_tools(server):
    """Registriert alle Model-Tools"""

    # Tool 1: Aktive Modelle auflisten
    server.register_tool(
        name="list_active_models",
        description="Liste aller aktiven ML-Modelle mit Konfiguration",
        parameters={
            "properties": {},
            "required": []
        },
        handler=list_active_models
    )

    # Tool 2: Verfügbare Modelle auflisten
    server.register_tool(
        name="list_available_models",
        description="Verfügbare Modelle vom Training Service zum Import",
        parameters={
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximale Anzahl (Standard: 20)"
                }
            },
            "required": []
        },
        handler=list_available_models
    )

    # Tool 3: Modell importieren
    server.register_tool(
        name="import_model",
        description="Importiert ein Modell vom Training Service",
        parameters={
            "properties": {
                "model_id": {
                    "type": "integer",
                    "description": "ID des Modells im Training Service"
                }
            },
            "required": ["model_id"]
        },
        handler=import_model
    )

    # Tool 4: Modell-Details abrufen
    server.register_tool(
        name="get_model_details",
        description="Detaillierte Informationen zu einem aktiven Modell",
        parameters={
            "properties": {
                "active_model_id": {
                    "type": "integer",
                    "description": "ID des aktiven Modells"
                }
            },
            "required": ["active_model_id"]
        },
        handler=get_model_details
    )

    # Tool 5: Modell aktivieren
    server.register_tool(
        name="activate_model",
        description="Aktiviert ein pausiertes Modell",
        parameters={
            "properties": {
                "active_model_id": {
                    "type": "integer",
                    "description": "ID des aktiven Modells"
                }
            },
            "required": ["active_model_id"]
        },
        handler=activate_model
    )

    # Tool 6: Modell deaktivieren
    server.register_tool(
        name="deactivate_model",
        description="Deaktiviert ein aktives Modell",
        parameters={
            "properties": {
                "active_model_id": {
                    "type": "integer",
                    "description": "ID des aktiven Modells"
                }
            },
            "required": ["active_model_id"]
        },
        handler=deactivate_model
    )


# Handler-Funktionen (rufen bestehende Service-Funktionen auf)

async def list_active_models():
    """Liste aller aktiven Modelle"""
    models = await get_active_models()
    return {
        "count": len(models),
        "models": models
    }


async def list_available_models(limit: int = 20):
    """Verfügbare Modelle vom Training Service"""
    models = await get_available_models(limit=limit)
    return {
        "count": len(models),
        "models": models
    }


async def import_model(model_id: int):
    """Importiert ein Modell"""
    result = await db_import_model(model_id)
    return result


async def get_model_details(active_model_id: int):
    """Details zu einem Modell"""
    models = await get_active_models()
    model = next((m for m in models if m.get("id") == active_model_id), None)

    if not model:
        return {"error": f"Modell {active_model_id} nicht gefunden"}

    return model


async def activate_model(active_model_id: int):
    """Aktiviert ein Modell"""
    result = await db_activate_model(active_model_id)
    return {"success": True, "message": f"Modell {active_model_id} aktiviert"}


async def deactivate_model(active_model_id: int):
    """Deaktiviert ein Modell"""
    result = await db_deactivate_model(active_model_id)
    return {"success": True, "message": f"Modell {active_model_id} deaktiviert"}
```

### 3.6 System-Tools: `backend/app/mcp/tools/system.py`

```python
"""
MCP Tools für System-Funktionen
"""

from app.utils.metrics import get_health_status
from app.database.models import get_prediction_stats


def register_tools(server):
    """Registriert System-Tools"""

    server.register_tool(
        name="health_check",
        description="Prüft den Health-Status des Services",
        parameters={
            "properties": {},
            "required": []
        },
        handler=health_check
    )

    server.register_tool(
        name="get_stats",
        description="Umfassende Service-Statistiken",
        parameters={
            "properties": {},
            "required": []
        },
        handler=get_stats
    )


async def health_check():
    """Health Status"""
    status = await get_health_status()
    return status


async def get_stats():
    """Service-Statistiken"""
    stats = await get_prediction_stats()
    return stats
```

## 4. FastAPI Integration

**Datei: `backend/app/main.py`** - Erweitere die bestehende Datei:

```python
# Am Anfang der Datei, bei den Imports:
from app.mcp.routes import router as mcp_router

# Nach den anderen Router-Einbindungen:
app.include_router(router)
app.include_router(coolify_router)

# MCP Server Router einbinden
app.include_router(mcp_router)

# Im startup Event (optional, für Logging):
@app.on_event("startup")
async def startup():
    # ... bestehender Code ...

    logger.info("🔌 MCP Server verfügbar unter /mcp/sse")
```

## 5. Nginx Proxy Konfiguration (für SSE)

**Datei: `frontend/Dockerfile`** - Erweitere die Nginx-Config:

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
    proxy_buffering off;
    proxy_cache off;
    proxy_read_timeout 86400s;  # 24 Stunden für lange SSE-Verbindungen
}
```

## 6. Claude Code Konfiguration

**Datei: `~/.claude/mcp_servers.json`** (auf dem Client-Rechner):

```json
{
  "mcpServers": {
    "dein-service-name": {
      "transport": "sse",
      "url": "http://localhost:3003/mcp/sse"
    }
  }
}
```

## 7. Dokumentation erstellen

### 7.1 `docs/api/mcp-server.md`

Erstelle eine ausführliche Dokumentation mit:
- Übersicht und Architektur
- Alle Endpoints (`/mcp/info`, `/mcp/sse`, `/mcp/health`)
- Alle Tools mit Parametern und Beispiel-Responses
- Claude Code Konfiguration
- Troubleshooting

### 7.2 `mcp-config.example.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "_comment": "MCP Server Konfiguration - Kopiere nach ~/.claude/mcp_servers.json",

  "mcpServers": {
    "dein-service": {
      "transport": "sse",
      "url": "http://localhost:3003/mcp/sse",
      "name": "Dein Service Name",
      "description": "Beschreibung des Services"
    }
  }
}
```

## 8. Verifikation

```bash
# 1. Docker bauen
docker-compose build

# 2. Services starten
docker-compose up -d

# 3. MCP Info testen
curl http://localhost:3003/mcp/info

# Erwartete Ausgabe:
# {
#   "name": "pump-server",
#   "version": "1.0.0",
#   "protocol": "MCP",
#   "transport": "SSE",
#   "tools_count": 13,
#   "tools": [...]
# }

# 4. Health Check
curl http://localhost:3003/mcp/health

# 5. SSE-Verbindung testen
curl -N http://localhost:3003/mcp/sse
# Sollte "event: endpoint" zurückgeben
```

## 9. Tool-Schema Referenz

Jedes Tool wird mit folgendem Schema registriert:

```python
server.register_tool(
    name="tool_name",                    # Eindeutiger Name
    description="Was das Tool macht",    # Für KI-Clients
    parameters={
        "properties": {
            "param1": {
                "type": "string",        # string, integer, boolean, array, object
                "description": "Beschreibung"
            },
            "param2": {
                "type": "integer",
                "description": "Beschreibung"
            }
        },
        "required": ["param1"]           # Pflichtparameter
    },
    handler=async_handler_function       # Async-Funktion
)
```

## 10. Architektur-Diagramm

```
┌─────────────────────────────────────────────────────────────┐
│                    Claude Code / KI-Client                   │
└─────────────────────────┬───────────────────────────────────┘
                          │ SSE + JSON-RPC
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Nginx (Port 3003)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   /api/*    │  │   /mcp/*    │  │      /* (SPA)       │  │
│  └──────┬──────┘  └──────┬──────┘  └─────────────────────┘  │
└─────────┼────────────────┼──────────────────────────────────┘
          │                │
          ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI Backend (Port 8000)                 │
│                                                              │
│  ┌─────────────────┐      ┌─────────────────────────────┐   │
│  │   REST API      │      │      MCP Server             │   │
│  │   /api/...      │      │  ┌─────────────────────┐    │   │
│  └────────┬────────┘      │  │  /mcp/info          │    │   │
│           │               │  │  /mcp/sse (GET/POST)│    │   │
│           │               │  │  /mcp/health        │    │   │
│           │               │  └──────────┬──────────┘    │   │
│           │               │             │               │   │
│           │               │  ┌──────────▼──────────┐    │   │
│           │               │  │   Tool Registry     │    │   │
│           │               │  │  - models.py        │    │   │
│           │               │  │  - predictions.py   │    │   │
│           │               │  │  - configuration.py │    │   │
│           │               │  │  - system.py        │    │   │
│           │               │  └──────────┬──────────┘    │   │
│           │               └─────────────┼───────────────┘   │
│           │                             │                   │
│           ▼                             ▼                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  Service Layer                        │   │
│  │         (Bestehende Business-Logik nutzen!)          │   │
│  └──────────────────────────┬───────────────────────────┘   │
└─────────────────────────────┼───────────────────────────────┘
                              ▼
                    ┌─────────────────┐
                    │   PostgreSQL    │
                    └─────────────────┘
```

## Checkliste für neue Projekte

- [ ] Dependencies in `requirements.txt` hinzufügen
- [ ] MCP-Modul erstellen (`backend/app/mcp/`)
- [ ] `server.py` mit Tool-Registry implementieren
- [ ] `routes.py` mit SSE-Endpoints erstellen
- [ ] Tools in `tools/` definieren (bestehende Funktionen aufrufen!)
- [ ] MCP Router in `main.py` einbinden
- [ ] Nginx-Config für SSE erweitern (`proxy_buffering off`!)
- [ ] `mcp-config.example.json` erstellen
- [ ] Dokumentation schreiben
- [ ] Testen mit `curl` und Claude Code

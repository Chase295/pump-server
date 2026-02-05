"""
FastAPI Main App für Pump Server
"""
import asyncio
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from app.api.routes import router, coolify_router
from app.database.connection import get_pool, close_pool
from app.utils.metrics import init_health_status
from app.utils.config import API_PORT
from app.utils.logging_config import setup_logging, get_logger, set_request_id
from app.mcp.routes import router as mcp_router, get_sse_routes

# Strukturiertes Logging konfigurieren
setup_logging()
logger = get_logger(__name__)

# FastAPI App erstellen
app = FastAPI(
    title="Pump Server",
    description="Machine Learning Prediction Service für Coin-Bot",
    version="1.0.0"
)

# Request-ID Middleware (muss vor CORS sein)
class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware für Request-ID Tracking"""
    
    async def dispatch(self, request: Request, call_next):
        # Generiere oder hole Request-ID aus Header
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = set_request_id()
        else:
            set_request_id(request_id)
        
        # Response mit Request-ID Header
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response

app.add_middleware(RequestIDMiddleware)

# CORS (falls nötig)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In Produktion: spezifische Origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router einbinden
app.include_router(router)
app.include_router(coolify_router)

# MCP Server Routes einbinden
# 1. Regular FastAPI router for /mcp/info and /mcp/health
app.include_router(mcp_router)

# 2. SSE routes need direct ASGI handling (bypass FastAPI response handling)
for route in get_sse_routes():
    app.routes.append(route)

@app.on_event("startup")
async def startup():
    """Startup Event: Einfacher Start ohne DB-Initialisierung"""
    logger.info("🚀 Starte Pump Server...")

    # DB-Pool wird lazy geladen (beim ersten API-Call)
    logger.info("ℹ️ Datenbank-Verbindung wird lazy geladen (beim ersten API-Call)")

    # Starte Alert-Evaluator als Background-Task
    try:
        from app.prediction.alert_evaluator import start_alert_evaluator
        await start_alert_evaluator(interval_seconds=30)  # Alle 30 Sekunden auswerten
        logger.info("✅ Alert-Evaluator gestartet")
    except Exception as e:
        logger.error(f"❌ Fehler beim Starten des Alert-Evaluators: {e}", exc_info=True)

    # Event-Handler läuft als separater Supervisor-Prozess
    logger.info("ℹ️ Event-Handler läuft als separater Supervisor-Prozess")

    logger.info("✅ Service ist bereit (Lazy DB Loading)")
    logger.info("🔌 MCP Server verfügbar unter /mcp/sse")

@app.on_event("shutdown")
async def shutdown():
    """Shutdown Event: Cleanup"""
    logger.info("🛑 Stoppe Pump Server...")

    # Hier könnte man den Event-Handler stoppen, falls nötig
    logger.info("✅ Service gestoppt")

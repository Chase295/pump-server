"""
FastAPI Main App für Pump Server
"""
import asyncio
import contextlib
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from app.api.routes import router, coolify_router
from app.database.connection import get_pool, close_pool
from app.utils.metrics import init_health_status
from app.utils.config import API_PORT
from app.utils.logging_config import setup_logging, get_logger, set_request_id
from app.mcp.routes import router as mcp_router, get_streamable_http_routes, get_session_manager

# Strukturiertes Logging konfigurieren
setup_logging()
logger = get_logger(__name__)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown logic."""
    # === STARTUP ===
    logger.info("🚀 Starte Pump Server...")

    # DB-Pool wird lazy geladen (beim ersten API-Call)
    logger.info("ℹ️ Datenbank-Verbindung wird lazy geladen (beim ersten API-Call)")

    # Starte Alert-Evaluator als Background-Task
    try:
        from app.prediction.alert_evaluator import start_alert_evaluator
        await start_alert_evaluator(interval_seconds=30)
        logger.info("✅ Alert-Evaluator gestartet")
    except Exception as e:
        logger.error(f"❌ Fehler beim Starten des Alert-Evaluators: {e}", exc_info=True)

    # Prüfe und stelle fehlende Modell-Dateien wieder her
    try:
        from app.prediction.model_manager import ensure_model_files
        recovery_stats = await ensure_model_files()
        if recovery_stats['missing'] > 0:
            logger.info(
                f"🔄 Modell-Recovery beim Startup: geprüft={recovery_stats['checked']}, "
                f"fehlend={recovery_stats['missing']}, "
                f"wiederhergestellt={recovery_stats['recovered']}, "
                f"fehlgeschlagen={recovery_stats['failed']}"
            )
        else:
            logger.info("✅ Alle Modell-Dateien vorhanden")
    except Exception as e:
        logger.error(f"❌ Fehler bei Modell-Recovery beim Startup: {e}", exc_info=True)

    logger.info("ℹ️ Event-Handler läuft als separater Supervisor-Prozess")

    # Starte MCP Session Manager
    session_manager = get_session_manager()
    async with session_manager.run():
        logger.info("✅ Service ist bereit (Lazy DB Loading)")
        logger.info("🔌 MCP Server verfügbar unter /mcp/ (Streamable HTTP)")
        yield

    # === SHUTDOWN ===
    logger.info("🛑 Stoppe Pump Server...")
    logger.info("✅ Service gestoppt")


# FastAPI App erstellen
app = FastAPI(
    title="Pump Server",
    description="Machine Learning Prediction Service für Coin-Bot",
    version="1.0.0",
    lifespan=lifespan,
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
    expose_headers=["Mcp-Session-Id"],
)

# Router einbinden
app.include_router(router)
app.include_router(coolify_router)

# MCP Server Routes einbinden
# 1. Regular FastAPI router for /mcp/info and /mcp/health
app.include_router(mcp_router)

# 2. Streamable HTTP route needs direct ASGI handling
for route in get_streamable_http_routes():
    app.routes.append(route)


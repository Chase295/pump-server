"""
MCP Routes for FastAPI

Provides HTTP endpoints for MCP server communication using Streamable HTTP transport.
Uses the official MCP SDK's StreamableHTTPSessionManager for session handling.
"""
import logging
from typing import Any

from fastapi import APIRouter, Request
from starlette.routing import Route
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

from app.mcp.server import get_mcp_server, PumpServerMCP

logger = logging.getLogger(__name__)

# Session Manager - singleton (initialized during app lifespan)
_session_manager: StreamableHTTPSessionManager | None = None


def get_session_manager() -> StreamableHTTPSessionManager:
    """Returns the singleton session manager instance."""
    global _session_manager
    if _session_manager is None:
        server = get_mcp_server()
        _session_manager = StreamableHTTPSessionManager(
            app=server,
            json_response=True,
            stateless=True,
        )
    return _session_manager


async def handle_mcp_http(request: Request):
    """
    Handle all MCP Streamable HTTP requests (GET, POST, DELETE).

    This is the single entry point for MCP clients using Streamable HTTP transport.
    """
    logger.debug(f"MCP HTTP request: {request.method}")

    session_manager = get_session_manager()
    await session_manager.handle_request(
        request.scope,
        request.receive,
        request._send,
    )


# Create router for regular FastAPI endpoints (info, health)
router = APIRouter(prefix="/mcp", tags=["MCP"])


@router.get("/info")
async def mcp_info() -> dict[str, Any]:
    """
    Returns information about the MCP server.

    This endpoint can be used to discover MCP server capabilities.
    """
    mcp = PumpServerMCP()
    return {
        "name": "pump-server-mcp",
        "version": "1.0.0",
        "description": "MCP Server for Pump-Server Pump Server",
        "transport": "streamable-http",
        "endpoint": "/mcp/",
        "tools": mcp.get_tool_list(),
        "tools_count": len(mcp.get_tool_list()),
    }


@router.get("/health")
async def mcp_health():
    """
    Health check endpoint for MCP server.
    """
    from app.mcp.tools.system import health_check
    result = await health_check()
    return result


def get_streamable_http_routes():
    """
    Returns Streamable HTTP routes that need direct ASGI handling.

    A single route handles GET, POST, and DELETE for Streamable HTTP transport.
    """
    return [
        Route("/mcp", endpoint=handle_mcp_http, methods=["GET", "POST", "DELETE"]),
        Route("/mcp/", endpoint=handle_mcp_http, methods=["GET", "POST", "DELETE"]),
    ]

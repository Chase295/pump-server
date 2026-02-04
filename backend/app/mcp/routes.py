"""
MCP Routes for FastAPI

Provides HTTP endpoints for MCP server communication using SSE transport.
Uses the official MCP SDK's SseServerTransport for correct SSE handling.
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
        # The path is where POST messages will be sent
        _sse_transport = SseServerTransport("/mcp/messages/")
    return _sse_transport


async def handle_sse(request: Request):
    """
    Handle SSE connections for MCP.

    This is the main entry point for MCP clients connecting via SSE.
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
        "description": "MCP Server for Pump-Server ML Prediction Service",
        "transport": "sse",
        "sse_endpoint": "/mcp/sse",
        "messages_endpoint": "/mcp/messages/",
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


def get_sse_routes():
    """
    Returns SSE-specific routes that need direct ASGI handling.

    These routes bypass FastAPI's response handling because SSE
    requires streaming directly to the ASGI send interface.
    """
    return [
        Route("/mcp/sse", endpoint=handle_sse, methods=["GET"]),
        Route("/mcp/messages/", endpoint=handle_messages, methods=["POST"]),
    ]


def create_mcp_routes() -> APIRouter:
    """
    Factory function for backward compatibility.

    Returns:
        Configured APIRouter for MCP endpoints
    """
    return router

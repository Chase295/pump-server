"""
MCP (Model Context Protocol) Server Module

Provides MCP integration for pump-server, allowing AI clients like Claude Code
to interact with the ML prediction service.
"""

from app.mcp.server import create_mcp_server, PumpServerMCP

__all__ = ["create_mcp_server", "PumpServerMCP"]

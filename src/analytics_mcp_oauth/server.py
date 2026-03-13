"""FastMCP server factory — wires auth and all tools together."""

import os

from fastmcp import FastMCP

from analytics_mcp_oauth.auth import create_auth_provider
from analytics_mcp_oauth.tools.admin import register_admin_tools
from analytics_mcp_oauth.tools.metadata import register_metadata_tools
from analytics_mcp_oauth.tools.realtime import register_realtime_tools
from analytics_mcp_oauth.tools.reporting import register_reporting_tools


def create_server(base_url: str | None = None) -> FastMCP:
    """Creates and configures the FastMCP server with OAuth auth and all GA tools.

    Args:
        base_url: The public URL of this server (e.g. the Cloud Run service URL).
            Used in the OAuth protected resource metadata so MCP clients know
            where to discover auth requirements. Reads MCP_BASE_URL env var
            if not provided.
    """
    if base_url is None:
        base_url = os.environ.get("MCP_BASE_URL", "http://localhost:8080")

    auth = create_auth_provider(base_url=base_url)
    mcp = FastMCP(name="google_analytics_mcp", auth=auth)

    register_admin_tools(mcp)
    register_reporting_tools(mcp)
    register_realtime_tools(mcp)
    register_metadata_tools(mcp)

    return mcp

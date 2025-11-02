"""MCP (Model Context Protocol) client utilities with caching."""
import asyncio
import os

from langchain_core.tools import Tool
from langchain_mcp_adapters.client import MultiServerMCPClient

# Cache for MCP tools to avoid repeated server calls
_mcp_tools_cache: dict[str, list[Tool]] = {}
_cache_lock = asyncio.Lock()


async def get_mcp_tools(mcp_server_uri: str | None = None) -> list[Tool]:
    """Get MCP tools from a configured MCP server with singleton caching."""
    # Get server URI from parameter or environment variable
    if mcp_server_uri is None:
        mcp_server_uri = os.getenv("MCP_SERVER_URI")
    
    # Return empty list if no server configured
    if not mcp_server_uri:
        return []
    
    # Check cache first (with lock to prevent race conditions)
    async with _cache_lock:
        if mcp_server_uri in _mcp_tools_cache:
            print(f"************Using cached MCP tools for {mcp_server_uri}")
            return _mcp_tools_cache[mcp_server_uri]
        
        # Need to fetch - keep lock to prevent concurrent fetches for same server
        # Create the client and fetch tools while holding the lock
        print(f"************Fetching MCP tools from {mcp_server_uri}")
        client = MultiServerMCPClient(
            {
                "langchain-mcp": {
                    "url": mcp_server_uri,
                    "transport": "streamable_http",
                }
            }
        )
        tools = await client.get_tools()
        print(f"************Tools fetched: {tools}")
        
        # Cache the tools
        _mcp_tools_cache[mcp_server_uri] = tools
        return tools


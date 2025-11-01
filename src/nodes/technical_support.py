"""
Technical support node that answers developer questions using the MCP docs tool.
"""
import os
import asyncio
from typing import Literal
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import Tool
from langchain_mcp_adapters.client import MultiServerMCPClient
from src.state import ConversationState
from src.configuration import Configuration
from src.utils.models import load_chat_model

# Cache for MCP tools to avoid repeated server calls
_mcp_tools_cache: dict[str, list[Tool]] = {}
_cache_lock = asyncio.Lock()


async def get_mcp_tools() -> list[Tool]:
    """Search LangChain MCP documentation via an MCP client if configured.
    
    Uses caching to avoid repeated server calls. Cache is keyed by MCP server URI.
    """
    mcp_server = os.getenv("MCP_SERVER_URI")
    
    # Return empty list if no server configured
    if not mcp_server:
        return []
    
    # Check cache first (with lock to prevent race conditions)
    async with _cache_lock:
        if mcp_server in _mcp_tools_cache:
            print(f"************Using cached MCP tools for {mcp_server}")
            return _mcp_tools_cache[mcp_server]
        
        # Need to fetch - keep lock to prevent concurrent fetches for same server
        # Create the client and fetch tools while holding the lock
        print(f"************Fetching MCP tools from {mcp_server}")
        client = MultiServerMCPClient(
            {
                "langchain-mcp": {
                    "url": mcp_server,
                    "transport": "streamable_http",
                }
            }
        )
        tools = await client.get_tools()
        print(f"************Tools fetched: {tools}")
        
        # Cache the tools
        _mcp_tools_cache[mcp_server] = tools
        return tools

async def process_technical_ticket(state: ConversationState, runtime: RunnableConfig[Configuration]) -> dict:
    """Technical support agent that answers developer questions using the MCP docs tool."""
    messages = state.get("messages", [])

    # runtime.context is a Configuration instance, so access attributes directly
    config = runtime.context if runtime.context else Configuration()

    # Create LLM with tools bound
    llm = load_chat_model(config.technical_agent_model, temperature= config.technical_agent_temperature)
    tools = await get_mcp_tools()
    llm_with_tools = llm.bind_tools(tools)

    # Build messages with system prompt
    agent_messages = [SystemMessage(content=config.technical_agent_system_prompt)] + messages

    # Invoke LLM
    response = await llm_with_tools.ainvoke(agent_messages)

    return {"messages": [response]}


def should_continue(state: ConversationState) -> Literal["technical_tools", "assessment"]:
    """Determines whether to route to tools or to assessment."""
    messages = state.get("messages", [])
    if not messages:
        return "assessment"

    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "technical_tools"
    else:
        return "assessment"


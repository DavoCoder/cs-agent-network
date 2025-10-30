"""
Technical support node that answers developer questions using the MCP docs tool.
"""
import os
from typing import Literal
from langchain_core.messages import SystemMessage
from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from src.state import ConversationState
from src.prompts import aload_prompt


async def get_mcp_tools() -> list[Tool]:
    """Search LangChain MCP documentation via an MCP client if configured."""
    mcp_server = os.getenv("MCP_SERVER_URI")
 
    client = MultiServerMCPClient(
        {
            "langchain-mcp": {
                "url": mcp_server,
                "transport": "streamable_http",
            }
        }
    )
    tools = await client.get_tools()
    print(f"************Tools: {tools}")

    return tools

async def process_technical_ticket(state: ConversationState) -> dict:
    """Technical support agent that answers developer questions using the MCP docs tool."""
    messages = state.get("messages", [])

    # Load system prompt for technical agent (non-blocking)
    system_prompt = await aload_prompt("technical_agent_system")

    # Create LLM with tools bound
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
    tools = await get_mcp_tools()
    llm_with_tools = llm.bind_tools(tools)

    # Build messages with system prompt
    agent_messages = [SystemMessage(content=system_prompt)] + messages

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


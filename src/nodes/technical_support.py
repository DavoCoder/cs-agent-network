"""
Technical support node that answers developer questions using the MCP docs tool.
"""
from typing import Literal

from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig

from src.configuration import Configuration
from src.state import ConversationState
from src.tools.mcp_client import get_mcp_tools
from src.utils.models import load_chat_model


async def process_technical_ticket(state: ConversationState, runtime: RunnableConfig[Configuration]) -> dict:
    """Technical support agent that answers developer questions using the MCP docs tool."""
    messages = state.get("messages", [])

    config = runtime.context if runtime.context else Configuration()

    llm = load_chat_model(config.technical_agent_model, temperature= config.technical_agent_temperature)
    tools = await get_mcp_tools()
    llm_with_tools = llm.bind_tools(tools)

    agent_messages = [SystemMessage(content=config.technical_agent_system_prompt)] + messages

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


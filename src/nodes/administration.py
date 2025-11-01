"""
Administration node that uses an external A2A client tool for admin tasks.
"""
from typing import Literal
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from src.state import ConversationState
from src.configuration import Configuration
from src.utils.models import load_chat_model
from src.tools.administration_tools import call_external_admin_a2a_agent


async def process_administration_ticket(state: ConversationState, runtime: RunnableConfig[Configuration]) -> dict:
    """Administration agent that uses an external A2A client tool for admin tasks."""
    messages = state.get("messages", [])

    config = runtime.context if runtime.context else Configuration()

    llm = load_chat_model(config.administration_model, temperature=config.administration_temperature)
    
    tools = [call_external_admin_a2a_agent]
    print("************A2A Tools:", tools)

    llm_with_tools = llm.bind_tools(tools, tool_choice="call_external_admin_a2a_agent")

    agent_messages = [SystemMessage(content=config.administration_system_prompt)] + messages
    response = await llm_with_tools.ainvoke(agent_messages)

    return {"messages": [response]}

def should_continue(state: ConversationState, runtime: RunnableConfig[Configuration] | None = None) -> Literal["admin_tools", "assessment"]:  # noqa: ARG001
    """Determines whether to route to tools or assessment for administration."""
    messages = state.get("messages", [])
    if not messages:
        return "assessment"
    
    last_message = messages[-1]
    
    # Check if there are tool calls to execute
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "admin_tools"
    
    # No tool calls, proceed to assessment
    # (The graph will route admin_tools -> human_review automatically)
    return "assessment"

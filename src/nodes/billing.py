from typing import Literal

from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig

from src.configuration import Configuration
from src.state import ConversationState
from src.tools.billing_tools import search_billing_kb
from src.utils.models import load_chat_model


def process_billing_ticket(
    state: ConversationState, runtime: RunnableConfig[Configuration]
) -> dict:
    """Billing agent that can search the billing knowledge base and generate responses."""
    messages = state.get("messages", [])

    config = runtime.context if runtime.context else Configuration()

    llm = load_chat_model(config.billing_model, temperature=config.billing_temperature)
    llm_with_tools = llm.bind_tools([search_billing_kb])

    agent_messages = [SystemMessage(content=config.billing_system_prompt)] + messages

    response = llm_with_tools.invoke(agent_messages)

    return {"messages": [response]}


def should_continue(state: ConversationState) -> Literal["billing_tools", "assessment"]:
    """Determines whether to route to tools or to assessment."""
    messages = state.get("messages", [])
    if not messages:
        return "assessment"

    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "billing_tools"
    else:
        return "assessment"

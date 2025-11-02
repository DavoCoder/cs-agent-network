"""
Administration node that uses an external A2A client tool for admin tasks.
This node is the central routing hub for all administration-related decisions.
"""
import logging
from typing import Literal

from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig

from src.configuration import Configuration
from src.state import ConversationState
from src.tools.administration_tools import call_external_admin_a2a_agent
from src.utils.message_utils import find_tool_response_and_query
from src.utils.models import load_chat_model

logger = logging.getLogger(__name__)


async def process_administration_ticket(state: ConversationState, runtime: RunnableConfig[Configuration]) -> dict:
    """Administration agent that uses an external A2A client tool for admin tasks."""
    messages = state.get("messages", [])

    config = runtime.context if runtime.context else Configuration()

    llm = load_chat_model(config.administration_model, temperature=config.administration_temperature)
    
    tools = [call_external_admin_a2a_agent]
    
    llm_with_tools = llm.bind_tools(tools)

    agent_messages = [SystemMessage(content=config.administration_system_prompt)] + messages
    response = await llm_with_tools.ainvoke(agent_messages)

    return {"messages": [response]}


def should_continue(
    state: ConversationState,
    runtime: RunnableConfig[Configuration] | None = None  # noqa: ARG001
) -> Literal["admin_tools", "human_review", "assessment"]:
    """Central routing logic for administration agent."""
    messages = state.get("messages", [])
    if not messages:
        return "assessment"
    
    last_message = messages[-1]
    
    # Priority 1: Check if there are tool calls to execute
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        logger.info('Administration: Tool calls detected, routing to admin_tools')
        return "admin_tools"
    
    # Priority 2: Check if there's a tool result that needs confirmation
    # Look for the most recent admin tool response
    admin_tool_response, _ = find_tool_response_and_query(
        messages,
        tool_name="call_external_admin_a2a_agent"
    )
    
    if admin_tool_response:
        # Check if confirmation was already processed
        admin_confirmation_processed = state.get("admin_confirmation_processed", False)
        admin_confirmation_pending = state.get("admin_confirmation_pending", False)
        
        if admin_confirmation_processed:
            # Second tool call completed, route to assessment
            logger.info('Administration: Confirmation processed, second tool call completed, routing to assessment')
            return "assessment"
        elif not admin_confirmation_pending:
            # First tool call completed, needs human confirmation
            logger.info('Administration: Tool result detected, needs human confirmation, routing to human_review')
            return "human_review"
        # If admin_confirmation_pending is True, we're waiting for user response
        # This shouldn't happen here (should be in process_feedback), but route to assessment as fallback
        logger.warning('Administration: Unexpected state - confirmation pending but in should_continue, routing to assessment')
        return "assessment"
    
    # Priority 3: No tool calls or results, proceed to assessment
    logger.info('Administration: No tool calls or results, routing to assessment')
    return "assessment"

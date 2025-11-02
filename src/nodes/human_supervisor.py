"""
Human supervisor node that handles human review and feedback.
"""

import logging

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command, interrupt

from src.configuration import Configuration
from src.state import ConversationState
from src.utils.message_utils import extract_user_message, find_tool_response_and_query

logger = logging.getLogger(__name__)


def human_review_interrupt(
    state: ConversationState, runtime: RunnableConfig[Configuration]
) -> Command:
    """Handle human review interruption, specifically for admin agent tool responses."""
    messages = state.get("messages", [])

    # Get configuration
    config = runtime.context if runtime.context else Configuration()

    # Note: This node should only be called from administration when a tool result
    # needs confirmation. The administration node's admin_should_continue handles
    # the routing logic

    # Find admin tool response and original query
    admin_tool_response, admin_original_query = find_tool_response_and_query(
        messages, tool_name="call_external_admin_a2a_agent"
    )

    # This node should only be called for admin tool responses
    # If no admin tool response is found, log an error and continue without interrupt
    if not admin_tool_response:
        logger.error(
            "human_review_interrupt called but no admin tool response found. "
            "This should only be called after admin_tools execution. "
            "Continuing without human review."
        )
        # Return empty update - edge will route to process_feedback, which will route to assessment
        return Command(update={})

    # Handle admin tool response confirmation (first time only)
    logger.info("Admin tool response detected, requesting human confirmation")

    # Use externalized prompt template
    summary = config.admin_confirmation_message.format(
        admin_original_query=admin_original_query or "Administrative task",
        admin_tool_response=admin_tool_response,
    )

    # Interrupt for user confirmation
    confirmation = interrupt({"question": config.admin_confirmation_question, "details": summary})

    # Store state for processing confirmation
    return Command(
        update={
            "admin_tool_response": admin_tool_response,
            "admin_original_query": admin_original_query or extract_user_message(messages),
            "admin_confirmation_pending": True,
            "human_feedback": confirmation,  # Store confirmation as human_feedback
            "pending_human_review": True,
        }
    )


def process_human_feedback(state: ConversationState) -> Command:
    """Process human feedback, handling admin confirmations specially."""
    human_feedback = state.get("human_feedback")
    admin_confirmation_pending = state.get("admin_confirmation_pending", False)

    if not human_feedback:
        return Command(update={})  # No changes if no feedback

    # Check if this is an admin confirmation
    if admin_confirmation_pending:
        # Check if user confirmed
        feedback_lower = str(human_feedback).lower()
        is_confirmed = any(
            keyword in feedback_lower
            for keyword in ["yes", "confirm", "proceed", "ok", "approved", "go ahead"]
        )
        is_cancelled = any(
            keyword in feedback_lower for keyword in ["no", "cancel", "abort", "stop"]
        )

        if is_cancelled:
            logger.info("Admin action cancelled by user")
            return Command(
                update={
                    "admin_confirmation_pending": False,
                    "admin_confirmation_processed": False,  # Clear confirmation processed flag
                    "admin_tool_response": None,
                    "admin_original_query": None,
                    "human_feedback": None,
                    "pending_human_review": False,
                    "messages": [
                        AIMessage(content="Administrative action cancelled as requested.")
                    ],
                }
                # Routes back to administration (via edge), which will route to assessment
            )

        # Confirmed or additional info - prepare message for second tool call
        logger.info(
            "Admin action confirmed or additional info provided, preparing second tool call"
        )
        original_query = state.get("admin_original_query", "")

        # Create a confirmation message that will trigger the second tool call
        if is_confirmed:
            confirmation_message = f"{original_query}\n\nUser confirmed: {human_feedback}"
        else:
            # Treat as additional info/confirmation
            confirmation_message = f"{original_query}\n\nUser response: {human_feedback}"

        return Command(
            update={
                "messages": [HumanMessage(content=confirmation_message)],
                "admin_confirmation_pending": False,
                "admin_confirmation_processed": True,  # Mark that confirmation was processed
                "pending_human_review": False,
                # Keep admin_tool_response for reference but clear confirmation flag
            }
            # Routes back to administration (via edge) for second tool call
        )

    # Default behavior for other feedback
    system_msg = SystemMessage(content="SYSTEM: Resuming workflow with human feedback")
    feedback_msg = AIMessage(content=human_feedback)

    return Command(
        update={
            "messages": [system_msg, feedback_msg],
            "pending_human_review": False,
            "human_feedback": None,
        }
    )

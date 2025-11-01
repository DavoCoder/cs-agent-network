"""
Human supervisor node that handles human review and feedback.
"""
import logging
from typing import Literal

from langchain_core.messages import AIMessage, SystemMessage, ToolMessage, HumanMessage
from langgraph.types import Command, interrupt

from src.state import ConversationState
from src.utils.message_utils import extract_user_message

logger = logging.getLogger(__name__)


def _extract_a2a_response(tool_message: ToolMessage) -> str:
    """Extract text response from A2A tool message."""
    content = tool_message.content
    # Tool now returns extracted text string directly, no parsing needed
    if isinstance(content, str):
        return content
    return str(content)


def human_review_interrupt(state: ConversationState) -> Command:
    """Handle human review interruption, specifically for admin agent tool responses."""
    messages = state.get("messages", [])
    
    # Check if this is an admin tool response that needs confirmation
    admin_tool_response = None
    admin_original_query = None
    
    # Find the most recent ToolMessage from admin tool
    for msg in reversed(messages[-10:]):  # Check last 10 messages
        if isinstance(msg, ToolMessage):
            tool_name = getattr(msg, "name", "")
            if "call_external_admin_a2a_agent" in tool_name or "a2a" in tool_name.lower():
                admin_tool_response = _extract_a2a_response(msg)
                tool_call_id = getattr(msg, "tool_call_id", None)
                
                # Find the original query - look for tool call with matching ID, then fallback to user message
                for prev_msg in reversed(messages):
                    if prev_msg == msg:
                        continue  # Skip the ToolMessage itself
                    if hasattr(prev_msg, "tool_calls") and prev_msg.tool_calls:
                        for tool_call in prev_msg.tool_calls:
                            if tool_call.get("id") == tool_call_id:
                                admin_original_query = tool_call.get("args", {}).get("query", "")
                                break
                        if admin_original_query:
                            break
                    if isinstance(prev_msg, HumanMessage):
                        admin_original_query = extract_user_message([prev_msg])
                        if admin_original_query:
                            break
                break
    
    # If this is an admin tool response, handle it specially
    if admin_tool_response:
        logger.info('Admin tool response detected, requesting human confirmation')
        
        # Store the response and query in state
        summary = f"""
⚠️ **ADMINISTRATIVE ACTION REQUIRES CONFIRMATION**

**Original Request**: {admin_original_query or 'Administrative task'}

**A2A Agent Response**:
{admin_tool_response}

**Action Required**: Please review the response above and confirm if you want to proceed with this action.

**To confirm**: Reply with "Yes, proceed" or "Confirm" followed by any additional information needed.
**To cancel**: Reply with "No" or "Cancel".
"""
        
        # Interrupt for user confirmation
        confirmation = interrupt({
            "question": "Do you want to proceed with this administrative action?",
            "details": summary
        })
        
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
    
    # Default behavior for other human reviews
    current_ticket = state.get("current_ticket")
    agent_contexts = state.get("agent_contexts", [])
    overall_confidence = state.get("overall_confidence", 0.5)
    risk_assessment = state.get("risk_assessment", "unknown")
    
    summary = f"""
🔍 **HUMAN REVIEW REQUIRED**

**Ticket**: {current_ticket.get('subject') if current_ticket else 'Unknown'}
**Category**: {current_ticket.get('category') if current_ticket else 'Unknown'}
**Confidence Score**: {overall_confidence:.2f}
**Risk Level**: {risk_assessment.upper()}

**Agent Processing History**:
"""
    
    for context in agent_contexts:
        summary += f"- {context['agent_name']}: confidence={context['confidence_score']:.2f}, "
        summary += f"risk={context['risk_level']}, review={context['requires_human_review']}\n"
    
    summary += f"""
**Conversation Summary**:
Last messages: {len(messages)} total messages

**Draft Response**:
{state.get('messages', [])[-1].content if state.get('messages') else 'No response generated'}

**Please review and provide feedback:**
1. Approve the response as-is
2. Edit the response
3. Reject and provide alternative guidance
"""
    
    decision = interrupt({
        "question": "Approve or reject the response?",
        "details": summary
    })

    return Command(
        update={
            "pending_human_review": True,
            "human_feedback": decision,
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
        is_confirmed = any(keyword in feedback_lower for keyword in [
            "yes", "confirm", "proceed", "ok", "approved", "go ahead"
        ])
        is_cancelled = any(keyword in feedback_lower for keyword in [
            "no", "cancel", "abort", "stop"
        ])
        
        if is_cancelled:
            logger.info('Admin action cancelled by user')
            return Command(
                update={
                    "admin_confirmation_pending": False,
                    "admin_tool_response": None,
                    "admin_original_query": None,
                    "human_feedback": None,
                    "pending_human_review": False,
                    "messages": [
                        AIMessage(content="Administrative action cancelled as requested.")
                    ]
                }
                # Route via conditional edges (route_after_feedback) to assessment
            )
        
        # Confirmed or additional info - prepare message for second tool call
        logger.info('Admin action confirmed or additional info provided, preparing second tool call')
        original_query = state.get("admin_original_query", "")
        
        # Create a confirmation message that will trigger the second tool call
        if is_confirmed:
            confirmation_message = f"{original_query}\n\nUser confirmed: {human_feedback}"
        else:
            # Treat as additional info/confirmation
            confirmation_message = f"{original_query}\n\nUser response: {human_feedback}"
        
        return Command(
            update={
                "messages": [
                    HumanMessage(content=confirmation_message)
                ],
                "admin_confirmation_pending": False,
                "pending_human_review": False,
                # Keep admin_tool_response for reference but clear confirmation flag
            }
            # Route via conditional edges (route_after_feedback) to administration
        )
    
    # Default behavior for other feedback
    system_msg = SystemMessage(content="SYSTEM: Resuming workflow with human feedback")
    feedback_msg = AIMessage(content=human_feedback)
    
    return Command(
        update={
            "messages": [system_msg, feedback_msg],
            "pending_human_review": False,
            "human_feedback": None
        }
    )


# Process feedback routes based on context
def route_after_feedback(state: ConversationState) -> Literal["administration", "assessment"]:
    """Route after processing human feedback."""
    # Check if this was an admin confirmation that needs a second tool call
    if state.get("admin_tool_response") and not state.get("admin_confirmation_pending"):
        # Admin confirmation was processed, go back to administration for second tool call
        # (The confirmation message is already in messages from process_human_feedback)
        return "administration"
    # Otherwise go to assessment
    return "assessment"


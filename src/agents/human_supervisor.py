"""
Human Supervisor Agent for handling human-in-the-loop workflows.
"""

from langchain_core.messages import AIMessage, SystemMessage
from langgraph.graph import END
from langgraph.types import Command, interrupt
from src.orchestration.state import ConversationState


def human_review_interrupt(state: ConversationState) -> Command:
    """
    Interrupt the workflow for human review.
    Uses Command pattern to return state updates.
    
    Args:
        state: Current conversation state
    
    Returns:
        Command with state updates
    """
    # Generate summary for human reviewer
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
{state.get('messages', [])[-3:]}  # Last 3 messages

**Draft Response**:
{state.get('messages', [])[-1].content if state.get('messages') else 'No response generated'}

**Please review and provide feedback:**
1. Approve the response as-is
2. Edit the response
3. Reject and provide alternative guidance
"""
    
    # Create interrupt messages
    system_msg = SystemMessage(content="SYSTEM: Workflow paused for human review")
    ai_msg = AIMessage(content=summary)

    decision = interrupt({
        "question": "Approve or reject the response?",
        "details": summary
    })

    goto = "process_feedback" if decision else END

    return Command(
        update={
            "messages": [system_msg, ai_msg],  # Messages reducer will append these
            "pending_human_review": not decision,
            "is_complete": decision,
        }
    )
 

def process_human_feedback(state: ConversationState) -> Command:
    """
    Process human feedback and resume workflow.
    Uses Command pattern to return state updates.
    
    Args:
        state: Current conversation state
    
    Returns:
        Command with state updates
    """
    human_feedback = state.get("human_feedback")
    
    if not human_feedback:
        return Command(update={})  # No changes if no feedback
    
    # Create feedback messages
    system_msg = SystemMessage(content="SYSTEM: Resuming workflow with human feedback")
    feedback_msg = AIMessage(content=human_feedback)
    
    return Command(
        update={
            "messages": [system_msg, feedback_msg],  # Messages reducer will append these
            "pending_human_review": False,
            "human_feedback": None
        }
    )


def should_resume_automatically(state: ConversationState) -> bool:
    """
    Determine if workflow should resume automatically after human review.
    
    Args:
        state: Current conversation state
    
    Returns:
        True if can resume automatically
    """
    human_feedback = state.get("human_feedback", "")
    
    # Resume automatically if human approves
    if human_feedback.lower() in ["approve", "ok", "approved", "yes"]:
        return True
    
    return False


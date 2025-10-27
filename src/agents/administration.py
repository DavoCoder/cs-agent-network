"""
Administration Agent for handling administrative tasks.
"""

from typing import Literal
from langchain_core.messages import AIMessage
from langgraph.graph import END
from langgraph.types import Command
from src.orchestration.state import ConversationState, AgentContext
from src.tools.knowledge_base import search_knowledge_base
from src.utils.confidence import calculate_confidence_score
from src.utils.risk_assessment import assess_risk, is_high_business_impact
from src.utils.routing import determine_routing_decision
from src.tools.compliance_check import check_compliance_risks, requires_human_oversight


def process_administration_ticket(state: ConversationState) -> Command[Literal["human_review", END]]:
    """
    Process an administration support ticket.
    Uses Command pattern to return state updates.
    
    Args:
        state: Current conversation state
    
    Returns:
        Command with state updates
    """
    current_ticket = state.get("current_ticket")
    if not current_ticket:
        return Command(
            update={"error_message": "No ticket information available"}
        )
    
    messages = state.get("messages", [])
    
    # Extract the latest user message
    user_message = ""
    for msg in reversed(messages):
        if hasattr(msg, "content"):
            user_message = msg.content
            break
    
    # Search knowledge base
    kb_result = search_knowledge_base("administration", user_message)
    
    # Generate response
    if kb_result:
        response_content = "I can assist you with administrative tasks.\n\n"
        response_content += f"Topic: {kb_result['topic']}\n\n"
        
        info = kb_result.get("information", {})
        for key, value in info.items():
            response_content += f"{key.replace('_', ' ').title()}: {value}\n"
    else:
        response_content = (
            "I can help you with administrative tasks such as account management, "
            "profile updates, and permissions. What specific administrative task do you need help with?"
        )
    
    # Calculate confidence
    confidence = calculate_confidence_score(response_content, {}, "administration")
    
    # Assess risk
    ticket_info = current_ticket if isinstance(current_ticket, dict) else current_ticket.__dict__
    risk_level = assess_risk(response_content, ticket_info, "administration")
    
    # Administrative changes need human review
    requires_human = any(keyword in user_message.lower() for keyword in 
                        ["delete", "remove", "change", "modify", "update", "permission"])
    
    # Check compliance
    compliance = check_compliance_risks(response_content)
    requires_human = requires_human or requires_human_oversight(compliance)
    
    # Check business impact
    high_impact = is_high_business_impact(response_content, ticket_info)
    
    # Add response message
    new_message = AIMessage(content=response_content)
    
    overall_confidence = min(state.get("overall_confidence", 1.0), confidence)
    
    # Determine if human review is needed
    needs_review = requires_human or high_impact or confidence < 0.65
    
    # Determine where to route next using shared routing logic
    goto = determine_routing_decision(
        state=state,
        needs_review=needs_review,
        overall_confidence=overall_confidence,
        risk_level=risk_level,
        agent_contexts=state.get("agent_contexts", [])
    )
    
    return Command(
        update={
            "messages": [new_message],  # Messages reducer will append this
            "agent_contexts": [AgentContext(
                agent_name="administration",
                confidence_score=confidence,
                reasoning=f"Processed admin request: {user_message[:50]}...",
                requires_human_review=needs_review,
                risk_level=risk_level
            )],  # Agent contexts reducer will append this
            "overall_confidence": overall_confidence,
            "risk_assessment": risk_level,
            "pending_human_review": needs_review
        },
        goto=goto
    )


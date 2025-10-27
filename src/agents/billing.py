"""
Billing Agent for handling billing inquiries.
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


def process_billing_ticket(state: ConversationState) -> Command[Literal["human_review", END]]:
    """
    Process a billing support ticket.
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
    kb_result = search_knowledge_base("billing", user_message)
    
    # Generate response
    if kb_result:
        response_content = "I can help you with that. Here's what I found:\n\n"
        response_content += f"Topic: {kb_result['topic']}\n\n"
        
        info = kb_result.get("information", {})
        if "policy" in info:
            response_content += f"Policy: {info['policy']}\n\n"
        if "conditions" in info:
            response_content += "Conditions:\n"
            for condition in info["conditions"]:
                response_content += f"- {condition}\n"
        if "process" in info:
            response_content += "\nTo proceed:\n"
            for i, step in enumerate(info["process"], 1):
                response_content += f"{i}. {step}\n"
            if "note" in info:
                response_content += f"\nNote: {info['note']}"
    else:
        response_content = (
            "I can help you with billing-related questions. "
            "Could you please specify what you need help with? "
            "For example: refunds, subscriptions, charges, or payment methods."
        )
    
    # Calculate confidence
    confidence = calculate_confidence_score(response_content, {}, "billing")
    
    # Assess risk (billing is inherently higher risk)
    ticket_info = current_ticket if isinstance(current_ticket, dict) else current_ticket.__dict__
    risk_level = assess_risk(response_content, ticket_info, "billing")
    
    # Check compliance
    compliance = check_compliance_risks(response_content)
    requires_human = requires_human_oversight(compliance)
    
    # Check business impact
    high_impact = is_high_business_impact(response_content, ticket_info)
    
    # Billing operations almost always need human review for safety
    requires_human = requires_human or "refund" in response_content.lower() or "charge" in response_content.lower()
    
    # Add response message
    new_message = AIMessage(content=response_content)
    
    overall_confidence = min(state.get("overall_confidence", 1.0), confidence)
    
    # Determine if human review is needed
    needs_review = requires_human or high_impact
    
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
                agent_name="billing",
                confidence_score=confidence,
                reasoning=f"Processed billing inquiry: {user_message[:50]}...",
                requires_human_review=needs_review,
                risk_level=risk_level
            )],  # Agent contexts reducer will append this
            "overall_confidence": overall_confidence,
            "risk_assessment": risk_level,
            "pending_human_review": needs_review
        },
        goto=goto
    )


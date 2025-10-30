from typing import Literal
from langchain_core.messages import AIMessage
from langgraph.graph import END
from langgraph.types import Command
from src.orchestration.state import ConversationState, AgentContext
from src.tools.knowledge_base import search_knowledge_base
from src.utils.confidence import calculate_confidence_score
from src.utils.risk_assessment import assess_risk, is_high_business_impact
from src.utils.routing import determine_routing_decision
from src.utils.message_utils import extract_user_message
from src.tools.compliance_check import check_compliance_risks, requires_human_oversight


def process_technical_ticket(state: ConversationState) -> Command[Literal["human_review", END]]:

    current_ticket = state.get("current_ticket")
    if not current_ticket:
        return Command(
            update={"error_message": "No ticket information available"}
        )
    
    messages = state.get("messages", [])
    
    # Extract the latest user message
    user_message = extract_user_message(messages)
    
    # Search knowledge base
    kb_result = search_knowledge_base("technical", user_message)
    
    # Generate response based on knowledge base or generate a default response
    if kb_result:
        response_content = "Based on your issue, here's what I found:\n\n"
        response_content += f"Topic: {kb_result['topic']}\n\n"
        
        info = kb_result.get("information", {})
        if "steps" in info:
            response_content += "Steps to resolve:\n"
            for i, step in enumerate(info["steps"], 1):
                response_content += f"{i}. {step}\n"
            response_content += f"\nEstimated time: {info.get('estimated_time', 'N/A')}"
    else:
        # Generic technical response
        response_content = (
            "I understand you're experiencing a technical issue. "
            "Let me help you troubleshoot this. "
            "Can you provide more details about the error message or symptoms you're seeing?"
        )
    
    # Calculate confidence
    confidence = calculate_confidence_score(response_content, {}, "technical_support")
    
    # Assess risk
    ticket_info = current_ticket if isinstance(current_ticket, dict) else current_ticket.__dict__
    risk_level = assess_risk(response_content, ticket_info, "technical_support")
    
    # Check compliance risks
    compliance = check_compliance_risks(response_content)
    requires_human = requires_human_oversight(compliance)
    
    # Check business impact
    high_impact = is_high_business_impact(response_content, ticket_info)
    
    # Add response message
    new_message = AIMessage(content=response_content)
    
    # Update overall confidence
    overall_confidence = min(state.get("overall_confidence", 1.0), confidence)
    
    # Determine if human review is needed
    needs_review = requires_human or high_impact or confidence < 0.6
    
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
                agent_name="technical_support",
                confidence_score=confidence,
                reasoning=f"Processed technical ticket about: {user_message[:50]}...",
                requires_human_review=needs_review,
                risk_level=risk_level
            )],  # Agent contexts reducer will append this
            "overall_confidence": overall_confidence,
            "risk_assessment": risk_level,
            "pending_human_review": needs_review
        },
        goto=goto
    )


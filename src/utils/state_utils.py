"""Utility functions for managing conversation state, tickets, and agent contexts."""

from typing import Any, Dict

from src.schemas.classification import TicketClassification
from src.state import AgentContext, ConversationState


def create_fallback_classification() -> TicketClassification:
    """Create a fallback unclassifiable classification for error scenarios."""
    return TicketClassification(
        category="unclassifiable",
        priority="low",
        intent="Unable to classify due to system error",
        keywords=[],
        confidence=0.0,
        needs_human_review=False,
    )


def create_supervisor_agent_context(classification: TicketClassification) -> AgentContext:
    """Create an agent context from a ticket classification."""
    return {
        "agent_name": "supervisor",
        "confidence_score": classification.confidence,
        "reasoning": f"Classified as {classification.category}: {classification.intent}",
        "requires_human_review": classification.needs_human_review,
        "risk_level": "high" if classification.needs_human_review else "low",
    }


def create_unclassifiable_agent_context(classification: TicketClassification) -> AgentContext:
    """Create an agent context for unclassifiable tickets."""
    context = create_supervisor_agent_context(classification)
    # Override with unclassifiable-specific values
    context["reasoning"] = classification.intent
    context["requires_human_review"] = False
    context["risk_level"] = "low"
    return context


def update_ticket_from_classification(
    state: ConversationState, classification: TicketClassification, user_message: str
) -> Dict[str, Any]:
    """Safely update or create a ticket from classification data."""
    current_ticket = state.get("current_ticket", {})

    # Safely handle ticket - ensure it's a dict and make a copy
    if isinstance(current_ticket, dict):
        current_ticket = current_ticket.copy()
    else:
        current_ticket = {}

    # Update ticket with classification data
    current_ticket.update(
        {
            "category": classification.category,
            "priority": classification.priority,
            "subject": classification.intent.strip() if classification.intent else "Unknown intent",
            "initial_description": user_message,
            "keywords": classification.keywords,
        }
    )

    return current_ticket


def create_routing_history_entry(classification: TicketClassification) -> str:
    """Create a formatted routing history entry from classification."""
    if classification.category == "unclassifiable":
        return "supervisor: classified as unclassifiable (not within scope)"

    return (
        f"supervisor: classified as {classification.category} "
        f"(priority: {classification.priority}, "
        f"confidence: {classification.confidence:.2f})"
    )


def build_classification_state_updates(
    classification: TicketClassification,
    current_ticket: Dict[str, Any],
    agent_context: AgentContext,
) -> Dict[str, Any]:
    """Build a complete state update dictionary from classification results."""
    return {
        "current_ticket": current_ticket,
        "routing_history": [create_routing_history_entry(classification)],
        "agent_contexts": [agent_context],
        "pending_human_review": classification.needs_human_review,
        "overall_confidence": classification.confidence,
    }

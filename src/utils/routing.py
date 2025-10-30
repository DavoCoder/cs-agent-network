from langgraph.graph import END


def determine_routing_decision(
    state: dict,
    needs_review: bool,
    overall_confidence: float,
    risk_level: str,
    agent_contexts: list
) -> str:
    """
    Determine where to route next based on review requirements and state.
    
    This implements the same logic as determine_needs_human_review but
    returns the actual routing decision (node name or END).
    
    Args:
        state: Current conversation state
        needs_review: Whether this agent determined review is needed
        overall_confidence: Confidence score for the response
        risk_level: Risk level (low, medium, high)
        agent_contexts: List of agent contexts from state
    
    Returns:
        Either "human_review" or END constant
    """
    # Check if human feedback exists
    if state.get("human_feedback"):
        return END
    
    # Check if this agent determined review is needed
    if needs_review:
        return "human_review"
    
    # Check confidence and risk levels
    if overall_confidence < 0.6 or risk_level == "high":
        return "human_review"
    
    # Check existing agent contexts
    any_requires_review = any(
        context.get("requires_human_review") for context in agent_contexts
    ) if agent_contexts else False
    
    return "human_review" if any_requires_review else END


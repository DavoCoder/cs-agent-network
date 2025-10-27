"""
Confidence scoring utilities for agent responses.
"""

import os
from typing import Dict, Any


def calculate_confidence_score(
    response: str,
    context: Dict[str, Any],  # type: ignore
    agent_name: str
) -> float:
    """
    Calculate confidence score for an agent's response.
    
    Args:
        response: The agent's response
        context: Additional context about the conversation
        agent_name: Name of the agent generating the response
    
    Returns:
        Confidence score between 0.0 and 1.0
    """
    # Base confidence
    confidence = 0.7
    
    # Factor 1: Response length (too short or too long may indicate uncertainty)
    response_length = len(response)
    if 50 <= response_length <= 500:
        confidence += 0.1
    elif response_length > 1000:
        confidence -= 0.2
    
    # Factor 2: Response completeness
    completeness_indicators = [
        "here's", "solution", "steps", "issue", "problem", "resolved",
        "check", "verify", "ensure"
    ]
    if any(indicator in response.lower() for indicator in completeness_indicators):
        confidence += 0.1
    
    # Factor 3: Uncertainty markers
    uncertainty_markers = [
        "not sure", "might", "maybe", "uncertain", "possibly", "perhaps"
    ]
    if any(marker in response.lower() for marker in uncertainty_markers):
        confidence -= 0.2
    
    # Factor 4: Confidence assertions
    if "definitely" in response.lower() or "certainly" in response.lower():
        confidence += 0.1
    
    # Factor 5: Agent-specific adjustments
    if agent_name == "technical_support":
        # Technical issues may be more deterministic
        if "error" in response.lower() or "code" in response.lower():
            confidence += 0.1
    elif agent_name == "billing":
        # Billing requires precision
        if "refund" in response.lower() or "charge" in response.lower():
            confidence -= 0.1  # Financial matters need human review
    elif agent_name == "administration":
        # Admin operations need verification
        if "change" in response.lower() or "modify" in response.lower():
            confidence -= 0.15
    
    # Clamp confidence to [0.0, 1.0]
    confidence = max(0.0, min(1.0, confidence))
    
    return confidence


def should_escalate_to_human(confidence: float, risk_level: str) -> bool:
    """
    Determine if a response should be escalated to human review.
    
    Args:
        confidence: Confidence score (0.0 to 1.0)
        risk_level: Risk level (low, medium, high)
    
    Returns:
        True if escalation is needed
    """
    # Get thresholds from environment
    low_confidence_threshold = float(
        os.getenv("HITL_THRESHOLD_LOW_CONFIDENCE", "0.6")
    )
    
    # Escalate if confidence is below threshold
    if confidence < low_confidence_threshold:
        return True
    
    # Escalate if risk is high
    if risk_level == "high":
        return True
    
    # Escalate if risk is medium AND confidence is borderline
    if risk_level == "medium" and confidence < 0.75:
        return True
    
    return False


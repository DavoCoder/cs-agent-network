from typing import Dict, Any, Literal


def assess_risk(
    response: str,
    ticket_info: Dict[str, Any],
    agent_name: str
) -> Literal["low", "medium", "high"]:
    """
    Assess the risk level of a response or action.
    
    Args:
        response: The proposed response or action
        ticket_info: Information about the current ticket
        agent_name: Name of the agent
    
    Returns:
        Risk level: low, medium, or high
    """
    risk = "low"
    
    # High-risk keywords
    high_risk_keywords = [
        "refund", "reimbursement", "delete", "remove user",
        "cancel account", "terminate", "suspend", "change permissions",
        "access", "password", "credentials", "api key"
    ]
    
    medium_risk_keywords = [
        "modify", "update", "change", "edit", "adjust",
        "escalate", "forward", "transfer"
    ]
    
    # Check for high-risk actions
    if any(keyword in response.lower() for keyword in high_risk_keywords):
        return "high"
    
    # Check for medium-risk actions
    if any(keyword in response.lower() for keyword in medium_risk_keywords):
        risk = "medium"
    
    # Check ticket priority
    if ticket_info.get("priority") in ["high", "urgent"]:
        if risk == "low":
            risk = "medium"
    
    # Check for compliance/policy issues
    compliance_keywords = [
        "compliance", "policy", "legal", "terms", "agreement",
        "gdpr", "privacy", "data protection"
    ]
    
    if any(keyword in response.lower() for keyword in compliance_keywords):
        if risk == "low":
            risk = "medium"
        else:
            risk = "high"
    
    # Agent-specific risk considerations
    if agent_name == "billing":
        # Financial operations are inherently higher risk
        if risk == "low":
            risk = "medium"
        if "refund" in response.lower() or "chargeback" in response.lower():
            risk = "high"
    
    elif agent_name == "administration":
        # Administrative changes need supervision
        if risk == "low":
            risk = "medium"
        if "delete" in response.lower() or "remove" in response.lower():
            risk = "high"
    
    return risk


def is_high_business_impact(
    response: str,
    ticket_info: Dict[str, Any]
) -> bool:
    """
    Determine if a response has high business impact.
    
    Args:
        response: The proposed response
        ticket_info: Information about the current ticket
    
    Returns:
        True if business impact is high
    """
    high_impact_indicators = [
        "revenue", "contract", "enterprise", "vip",
        "refund amount", "large", "significant"
    ]
    
    # Check response content
    if any(indicator in response.lower() for indicator in high_impact_indicators):
        return True
    
    # Check ticket properties
    if ticket_info.get("priority") == "urgent":
        return True
    
    # Check for financial impact keywords
    financial_keywords = ["refund", "credit", "compensation", "rebate"]
    if any(keyword in response.lower() for keyword in financial_keywords):
        # Check for amounts (simple heuristic)
        if any(char.isdigit() for char in response):
            return True
    
    return False


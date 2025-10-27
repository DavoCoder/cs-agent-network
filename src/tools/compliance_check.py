"""
Compliance checking tools for detecting policy and legal risks.
"""

from typing import Dict, Any


COMPLIANCE_KEYWORDS = {
    "high_risk": [
        "personal data", "pii", "gdpr", "data breach",
        "privacy violation", "unauthorized access", "security breach"
    ],
    "financial": [
        "refund", "chargeback", "payment dispute", "billing error",
        "fraud", "unauthorized charge"
    ],
    "legal": [
        "lawsuit", "legal action", "attorney", "legal notice",
        "terms violation", "contract breach"
    ],
    "regulatory": [
        "compliance", "audit", "regulation", "policy violation",
        "regulatory requirement"
    ]
}


def check_compliance_risks(message: str) -> Dict[str, Any]:
    """
    Check if a message contains compliance or policy risks.
    
    Args:
        message: Message to check
    
    Returns:
        Risk assessment dictionary
    """
    message_lower = message.lower()
    risks = []
    risk_level = "low"
    
    # Check for high-risk keywords
    for keyword in COMPLIANCE_KEYWORDS["high_risk"]:
        if keyword in message_lower:
            risks.append({
                "type": "privacy/security",
                "keyword": keyword,
                "severity": "high"
            })
            risk_level = "high"
    
    # Check for financial compliance issues
    for keyword in COMPLIANCE_KEYWORDS["financial"]:
        if keyword in message_lower:
            risks.append({
                "type": "financial",
                "keyword": keyword,
                "severity": "medium"
            })
            if risk_level == "low":
                risk_level = "medium"
    
    # Check for legal issues
    for keyword in COMPLIANCE_KEYWORDS["legal"]:
        if keyword in message_lower:
            risks.append({
                "type": "legal",
                "keyword": keyword,
                "severity": "high"
            })
            risk_level = "high"
    
    # Check for regulatory compliance
    for keyword in COMPLIANCE_KEYWORDS["regulatory"]:
        if keyword in message_lower:
            risks.append({
                "type": "regulatory",
                "keyword": keyword,
                "severity": "medium"
            })
            if risk_level == "low":
                risk_level = "medium"
    
    return {
        "has_risk": len(risks) > 0,
        "risk_level": risk_level,
        "risks": risks
    }


def requires_human_oversight(risk_assessment: Dict[str, Any]) -> bool:
    """
    Determine if risk assessment requires human oversight.
    
    Args:
        risk_assessment: Output from check_compliance_risks
    
    Returns:
        True if human oversight is required
    """
    if not risk_assessment["has_risk"]:
        return False
    
    # Require human oversight for high-risk scenarios
    if risk_assessment["risk_level"] == "high":
        return True
    
    # Require human oversight for financial issues
    financial_risks = [
        r for r in risk_assessment["risks"] 
        if r["type"] == "financial"
    ]
    if financial_risks:
        return True
    
    return False


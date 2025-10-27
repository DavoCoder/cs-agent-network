"""
Knowledge base tools for agents to retrieve information.
"""

from typing import Dict, Any, Optional


# Mock knowledge base for demonstration
KNOWLEDGE_BASE = {
    "technical": {
        "password_reset": {
            "steps": [
                "Visit the login page",
                "Click 'Forgot Password'",
                "Enter your email address",
                "Check your email for reset instructions",
                "Follow the link and set a new password"
            ],
            "estimated_time": "5 minutes"
        },
        "api_connection": {
            "steps": [
                "Verify your API key is valid",
                "Check API endpoint URL",
                "Ensure network connectivity",
                "Review API documentation for correct format"
            ],
            "estimated_time": "15 minutes"
        }
    },
    "billing": {
        "refund_policy": {
            "policy": "Refunds are processed within 5-7 business days",
            "conditions": [
                "Within 30 days of purchase",
                "Product unused or in original condition"
            ]
        },
        "subscription_cancel": {
            "process": [
                "Go to account settings",
                "Select subscription management",
                "Click cancel subscription",
                "Confirm cancellation"
            ],
            "note": "Cancellation takes effect at end of billing period"
        }
    },
    "administration": {
        "account_management": {
            "profile_update": "Update profile through Settings > Personal Information",
            "permissions": "Contact administrator for permission changes"
        }
    }
}


def search_knowledge_base(
    category: str,
    query: str
) -> Optional[Dict[str, Any]]:
    """
    Search the knowledge base for relevant information.
    
    Args:
        category: Category to search (technical, billing, administration)
        query: Search query
    
    Returns:
        Relevant knowledge base entry or None
    """
    category_data = KNOWLEDGE_BASE.get(category.lower(), {})
    
    # Simple keyword matching
    query_lower = query.lower()
    
    for key, value in category_data.items():
        if query_lower in key or any(query_lower in str(v).lower() for v in value.values() if isinstance(v, str)):
            return {
                "category": category,
                "topic": key,
                "information": value
            }
    
    return None


def get_all_knowledge_for_category(category: str) -> Dict[str, Any]:
    """
    Retrieve all knowledge base entries for a category.
    
    Args:
        category: Category name
    
    Returns:
        Dictionary of all knowledge entries
    """
    return KNOWLEDGE_BASE.get(category.lower(), {})


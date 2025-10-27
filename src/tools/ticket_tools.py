"""
Tools for interacting with ticket system.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import uuid


# Mock ticket storage
tickets_db = {}


def create_ticket(
    customer_id: str,
    subject: str,
    description: str,
    category: str,
    priority: str = "medium"
) -> Dict[str, Any]:
    """
    Create a new support ticket.
    
    Args:
        customer_id: Customer identifier
        subject: Ticket subject
        description: Ticket description
        category: Ticket category
        priority: Ticket priority
    
    Returns:
        Created ticket information
    """
    ticket_id = str(uuid.uuid4())
    
    ticket = {
        "ticket_id": ticket_id,
        "customer_id": customer_id,
        "subject": subject,
        "description": description,
        "category": category,
        "priority": priority,
        "status": "new",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "assigned_agent": None,
        "conversation_history": []
    }
    
    tickets_db[ticket_id] = ticket
    
    return ticket


def update_ticket_status(
    ticket_id: str,
    status: str,
    agent_name: Optional[str] = None
) -> bool:
    """
    Update ticket status.
    
    Args:
        ticket_id: Ticket identifier
        status: New status
        agent_name: Agent handling the ticket
    
    Returns:
        True if updated successfully
    """
    if ticket_id not in tickets_db:
        return False
    
    tickets_db[ticket_id]["status"] = status
    tickets_db[ticket_id]["updated_at"] = datetime.now().isoformat()
    
    if agent_name:
        tickets_db[ticket_id]["assigned_agent"] = agent_name
    
    return True


def get_ticket(ticket_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a ticket by ID.
    
    Args:
        ticket_id: Ticket identifier
    
    Returns:
        Ticket information or None
    """
    return tickets_db.get(ticket_id)


def add_message_to_ticket(
    ticket_id: str,
    sender: str,
    message: str
) -> bool:
    """
    Add a message to ticket conversation history.
    
    Args:
        ticket_id: Ticket identifier
        sender: Message sender
        message: Message content
    
    Returns:
        True if added successfully
    """
    if ticket_id not in tickets_db:
        return False
    
    tickets_db[ticket_id]["conversation_history"].append({
        "sender": sender,
        "message": message,
        "timestamp": datetime.now().isoformat()
    })
    
    return True


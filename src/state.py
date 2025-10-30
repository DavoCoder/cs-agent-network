from typing import Optional, List, Literal
from typing_extensions import TypedDict, NotRequired, Annotated
from langgraph.graph import MessagesState

class TicketInfo(TypedDict):
    """Information about a customer support ticket"""
    ticket_id: str
    category: str  # technical, billing, administration
    priority: Literal["low", "medium", "high", "urgent"]
    status: Literal["new", "in_progress", "waiting_human", "resolved", "closed"]
    customer_id: str
    subject: str
    initial_description: str
    assigned_agent: NotRequired[Optional[str]]

class AgentContext(TypedDict):
    """Context for individual agent execution"""
    agent_name: str
    confidence_score: float  # 0.0 to 1.0
    reasoning: str
    requires_human_review: bool
    risk_level: Literal["low", "medium", "high"]

def append_agent_context(left: List[AgentContext], right: List[AgentContext]) -> List[AgentContext]:
    """Reducer for agent_contexts: appends new contexts to the list."""
    return left + right

def append_routing_history(left: List[str], right: List[str]) -> List[str]:
    """Reducer for routing_history: appends new history entries to the list."""
    return left + right


class ConversationState(MessagesState):
    """
    Main state schema for the LangGraph workflow.
    Maintains conversation history and context across all agents.
    """
    # Current ticket information
    current_ticket: NotRequired[Optional[TicketInfo]]
    # Agent context tracking - using reducer to append new contexts
    agent_contexts: NotRequired[Annotated[List[AgentContext], append_agent_context]]
    # Human-in-the-loop state
    pending_human_review: NotRequired[bool]
    human_feedback: NotRequired[Optional[str]]
    # Routing information - using reducer to append new history
    routing_history: NotRequired[Annotated[List[str], append_routing_history]]
    # System flags
    is_complete: NotRequired[bool]
    error_message: NotRequired[Optional[str]]
    # Confidence and risk tracking
    overall_confidence: NotRequired[float]
    risk_assessment: NotRequired[Optional[str]]
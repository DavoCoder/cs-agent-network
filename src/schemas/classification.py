"""Schema for ticket classification."""
from typing import List, Literal
from pydantic import BaseModel, Field


class TicketClassification(BaseModel):
    """Structured output for ticket classification."""
    category: Literal["technical", "billing", "administration", "unclassifiable"] = Field(
        description="The category of the support request"
    )
    priority: Literal["low", "medium", "high", "urgent"] = Field(
        description="The urgency/priority level of the request"
    )
    intent: str = Field(
        description="A brief summary of the customer's intent or what they're trying to accomplish"
    )
    keywords: List[str] = Field(
        description="Key terms or phrases from the message that indicate the issue"
    )
    confidence: float = Field(
        description="Confidence score from 0.0 to 1.0 for the classification"
    )
    needs_human_review: bool = Field(
        description="Whether this request might need human review"
    )


"""
Orchestrator agent that routes tickets to appropriate specialized agents.
Uses an LLM to classify and understand the intent of the customer message.
"""

from typing import List, Literal
from pydantic import BaseModel, Field
from langgraph.graph import END
from langgraph.types import Command
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from src.orchestration.state import ConversationState
from src.prompts import load_prompt


class TicketClassification(BaseModel):
    """Structured output for ticket classification"""
    category: Literal["technical", "billing", "administration"] = Field(
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


def classify_ticket_with_llm(state: ConversationState) -> Command[Literal["technical_support", "billing", "administration"]]:
    """
    Use an LLM to classify the customer's message and determine routing.
    Uses Command pattern to combine state updates with routing.
    
    Args:
        state: Current conversation state
    
    Returns:
        Command with state updates and next node to route to
    """
    # Get the latest user message
    messages = state.get("messages", [])
    
    # Extract the human message
    user_message = ""
    last_message = None
    
    # Try to get the last message
    if messages:
        last_message = messages[-1]
        
        # Check if it's a dict (from Studio UI)
        if isinstance(last_message, dict):
            # LangGraph Studio uses 'type' field: {'type': 'human', 'content': '...'}
            msg_type = last_message.get("type")
            msg_role = last_message.get("role")
            if msg_type == "human" or msg_role == "user" or msg_role == "human":
                user_message = last_message.get("content", "")
        # Check if it's a HumanMessage object
        elif hasattr(last_message, 'content'):
            user_message = last_message.content
    

    print(f"DEBUG: Extracted user message: {user_message[:100] if user_message else 'NONE'}")
    print(f"DEBUG: Messages count: {len(messages)}")
    print(f"DEBUG: Last message type: {type(last_message)}")
    print(f"DEBUG: Last message: {last_message}")
    
    if not user_message:
        # Fallback if no user message found
        return Command(
            update={
                "error_message": "No user message found for classification"
            },
            goto=END  # Default 
        )
    
    # Initialize the LLM for classification
    model = ChatOpenAI(
        model="gpt-4o-mini",  # Use cost-effective model for classification
        temperature=0.0,  # Deterministic classification
    )
    
    # Create structured output parser
    structured_llm = model.with_structured_output(TicketClassification)
    
    # Load system prompt from external file
    system_prompt = load_prompt("ticket_classifier")
    
    # Create classification prompt
    classification_messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Customer message: {user_message}")
    ]
    
    # Get LLM classification
    try:
        classification = structured_llm.invoke(classification_messages)
    except Exception as e:  # noqa: E722
        # Fallback on error
        print(f"Error in LLM classification: {e}")
        return Command(
            update={
                "routing_history": ["orchestrator: fallback to technical_support"]
            },
            goto="technical_support"  # Default fallback
        )
    
    # Determine next agent based on classification
    next_agent = classification.category
    
    # Create or update current ticket with classification
    current_ticket = state.get("current_ticket", {})
    if isinstance(current_ticket, dict):
        current_ticket = current_ticket.copy()
    else:
        current_ticket = {}
    
    current_ticket.update({
        "category": classification.category,
        "priority": classification.priority,
        "subject": classification.intent,
        "initial_description": user_message,
        "keywords": classification.keywords
    })
    
    # Add routing message (handle both dict and AIMessage formats)
    routing_message_content = f"I've analyzed your request and classified it as a {classification.priority} priority {classification.category} issue. " \
                               f"Let me route you to our {classification.category.replace('_', ' ')} team."
    
    if isinstance(messages, list) and messages and isinstance(messages[0], dict):
        # Dict format (from Studio UI) - use 'type' field like Studio expects
        new_message = {"type": "ai", "content": routing_message_content}
    else:
        # AIMessage format
        new_message = AIMessage(content=routing_message_content)
    
    # Return Command with state updates and routing
    return Command(
        update={
            "messages": [new_message],  # Messages reducer will append this
            "current_ticket": current_ticket,
            "routing_history": [
                f"orchestrator: classified as {classification.category} (priority: {classification.priority}, "
                f"confidence: {classification.confidence:.2f})"
            ],
            "agent_contexts": [{
                "agent_name": "orchestrator",
                "confidence_score": classification.confidence,
                "reasoning": f"Classified as {classification.category}: {classification.intent}",
                "requires_human_review": classification.needs_human_review,
                "risk_level": "high" if classification.needs_human_review else "low"
            }],
            "pending_human_review": classification.needs_human_review,
            "overall_confidence": classification.confidence
        },
        goto=next_agent
    )
"""
Supervisor node that classifies the customer's message and determines routing.
"""
from typing import List, Literal
from pydantic import BaseModel, Field
from langgraph.graph import END
from langgraph.types import Command
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from src.utils.models import load_chat_model
from src.state import ConversationState
from src.prompts import load_prompt
from src.utils.message_utils import extract_user_message
from src.configuration import Configuration

class TicketClassification(BaseModel):
    """Structured output for ticket classification"""
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


def _create_ai_message(content: str, messages: list):
    """Helper to create message in correct format based on message history"""
    if isinstance(messages, list) and messages and isinstance(messages[0], dict):
        return {"type": "ai", "content": content}
    return AIMessage(content=content)


def _create_agent_context(classification: TicketClassification) -> dict:
    """Helper to create agent context from classification"""
    return {
        "agent_name": "supervisor",
        "confidence_score": classification.confidence,
        "reasoning": f"Classified as {classification.category}: {classification.intent}",
        "requires_human_review": classification.needs_human_review,
        "risk_level": "high" if classification.needs_human_review else "low"
    }


def classify_ticket_with_llm(state: ConversationState, 
    runtime: RunnableConfig[Configuration]) -> Command[Literal["technical", "billing", "administration", END]]:
    """ Use an LLM to classify the customer's message and determine routing. """
    # Get the latest user message
    messages = state.get("messages", [])
    
    # Extract the human message
    user_message = extract_user_message(messages)
    
    if not user_message:
        # Fallback if no user message found
        return Command(
            update={
                "error_message": "No user message found for classification"
            },
            goto=END  # Default 
        )
    
    config = runtime.context if runtime.context else Configuration()

    model = load_chat_model(
        config.supervisor_model,
        config.supervisor_temperature
    )
    
    structured_llm = model.with_structured_output(TicketClassification)
    
    system_prompt = config.supervisor_system_prompt
    
    # Get recent conversation history (last 5 messages for classification context)
    recent_history = messages[-5:] if len(messages) > 5 else messages
    
    classification_messages = [SystemMessage(content=system_prompt)]
    
    # Add conversation context (skip the current user message as it will be added separately)
    for msg in recent_history:
        if hasattr(msg, "content"):
            msg_content = msg.content if isinstance(msg.content, str) else str(msg.content)
            if msg_content != user_message:
                classification_messages.append(msg)
    
    # Add current user message
    classification_messages.append(HumanMessage(content=f"Customer message: {user_message}"))
    
    try:
        classification = structured_llm.invoke(classification_messages)
    except Exception as e:  # noqa: E722
        # Fallback on error
        print(f"Error in LLM classification: {e}")
        return Command(
            update={
                "routing_history": ["supervisor: fallback to technical"]
            },
            goto="technical"  # Default fallback
        )
    
    # Handle unclassifiable questions
    if classification.category == "unclassifiable":
        response_message = load_prompt("unclassifiable_response")
        new_message = _create_ai_message(response_message, messages)
        
        agent_context = _create_agent_context(classification)
        agent_context["reasoning"] = classification.intent
        agent_context["requires_human_review"] = False
        agent_context["risk_level"] = "low"
        
        return Command(
            update={
                "messages": [new_message],
                "routing_history": [
                    "supervisor: classified as unclassifiable (not within scope)"
                ],
                "agent_contexts": [agent_context],
                "overall_confidence": classification.confidence,
                "pending_human_review": False
            },
            goto=END
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
    
    # Build state updates
    # The specialized agent will provide the actual response to the user
    updates = {
        "current_ticket": current_ticket,
        "routing_history": [
            f"supervisor: classified as {classification.category} (priority: {classification.priority}, "
            f"confidence: {classification.confidence:.2f})"
        ],
        "agent_contexts": [_create_agent_context(classification)],
        "pending_human_review": classification.needs_human_review,
        "overall_confidence": classification.confidence
    }
    
    return Command(
        update=updates,
        goto=next_agent
    )
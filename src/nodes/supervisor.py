"""
Supervisor node that classifies the customer's message and determines routing.
"""
import logging
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END
from langgraph.types import Command

from src.configuration import Configuration
from src.schemas.classification import TicketClassification
from src.state import ConversationState
from src.utils.message_utils import (
    create_ai_message,
    extract_user_message,
    format_conversation_history,
)
from src.utils.models import load_chat_model
from src.utils.state_utils import (
    build_classification_state_updates,
    create_fallback_classification,
    create_supervisor_agent_context,
    create_unclassifiable_agent_context,
    update_ticket_from_classification,
)

logger = logging.getLogger(__name__)


def classify_ticket_with_llm(state: ConversationState, 
    runtime: RunnableConfig[Configuration]) -> Command[Literal["technical", "billing", "administration", END]]:
    """ Use an LLM to classify the customer's message and determine routing. """

    messages = state.get("messages", [])

    user_message = extract_user_message(messages)
    
    config = runtime.context if runtime.context else Configuration()
    
    model = load_chat_model(
        config.supervisor_model,
        config.supervisor_temperature
    )
    
    structured_llm = model.with_structured_output(TicketClassification)
    
    # Include conversation history (up to 10 previous messages) for context
    conversation_history = format_conversation_history(messages, max_messages=10)
    
    # Build the classification message with context
    if conversation_history:
        classification_content = (
            f"Previous conversation history:\n{conversation_history}\n\n"
            f"Current customer message: {user_message}" if user_message else "Current customer message: (empty or unreadable)"
        )
    else:
        classification_content = (
            f"Customer message: {user_message}" if user_message else "Customer message: (empty or unreadable)"
        )
    
    classification_messages = [
        SystemMessage(content=config.supervisor_system_prompt),
        HumanMessage(content=classification_content)
    ]
    
    try:
        classification = structured_llm.invoke(classification_messages)
        
        if classification.confidence < 0.5:
            logger.warning(
                'Low confidence classification: %s (confidence: %.2f). User message: %s',
                classification.category,
                classification.confidence,
                user_message[:100] if len(user_message) > 100 else user_message
            )
            
    except Exception as e:
        logger.error('Error in LLM classification (API/system error): %s', e, exc_info=True)
        
        classification = create_fallback_classification()
        
        logger.info('Using fallback unclassifiable classification due to LLM error')
    
    if classification.category == "unclassifiable":
        response_message = config.unclassifiable_response_ai_prompt
        new_message = create_ai_message(response_message, messages)
        
        state_updates = build_classification_state_updates(
            classification,
            {},  # Empty ticket for unclassifiable
            create_unclassifiable_agent_context(classification)
        )
        # Add messages and ensure pending_human_review is False for unclassifiable
        state_updates["messages"] = [new_message]
        state_updates["pending_human_review"] = False
        
        return Command(
            update=state_updates,
            goto=END
        )

    next_agent = classification.category
    
    updates = build_classification_state_updates(
        classification,
        update_ticket_from_classification(state, classification, user_message),
        create_supervisor_agent_context(classification)
    )
    
    logger.info(
        'Ticket classified: category=%s, priority=%s, confidence=%.2f, intent=%s',
        classification.category,
        classification.priority,
        classification.confidence,
        classification.intent[:50] if len(classification.intent) > 50 else classification.intent
    )
    
    return Command(
        update=updates,
        goto=next_agent
    )
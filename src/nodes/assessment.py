from typing import Literal
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END
from langgraph.types import Command
from src.state import ConversationState, AgentContext
from src.utils.message_utils import extract_user_message
from src.configuration import Configuration
from src.utils.models import load_chat_model
from src.schemas.assessment import Assessment


def process_assessment(state: ConversationState, runtime: RunnableConfig[Configuration]) -> Command[Literal[END]]:
    """ Assess the response and route to END. """
    current_ticket = state.get("current_ticket")
    if not current_ticket:
        return Command(
            update={"error_message": "No ticket information available"}
        )
    
    messages = state.get("messages", [])
    
    # Extract the final response
    final_response = None
    for msg in reversed(messages):
        if isinstance(msg, AIMessage):
            final_response = msg.content if msg.content else ""
            break
    
    if not final_response:
        return Command(
            update={"error_message": "No agent response found"}
        )
    
    # Extract original user message
    user_message = extract_user_message(messages)

    # runtime.context is a Configuration instance, so access attributes directly
    config = runtime.context if runtime.context else Configuration()
    
    llm = load_chat_model(config.assessment_model, temperature=config.assessment_temperature)
    structured_llm = llm.with_structured_output(Assessment)
    
    # Build assessment prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", config.assessment_system_prompt),
        ("human", config.assessment_human_prompt)
    ])
    
    # Invoke LLM for assessment
    messages = prompt.format_messages(
        user_message=user_message,
        ai_response=final_response,
        priority=current_ticket.get("priority", "medium"),
        category=current_ticket.get("category", "unclassified")
    )
    
    assessment = structured_llm.invoke(messages)
    
    # Update agent context
    agent_context = AgentContext(
        agent_name="assessment",
        confidence_score=assessment.confidence_score,
        reasoning=assessment.reasoning,
        requires_human_review=assessment.requires_human_review,
        risk_level=assessment.risk_level
    )
    
    # Update overall confidence
    overall_confidence = min(
        state.get("overall_confidence", 1.0),
        assessment.confidence_score
    )
    
    return Command(
        update={
            "agent_contexts": [agent_context],
            "overall_confidence": overall_confidence,
            "risk_assessment": assessment.risk_level,
            "pending_human_review": assessment.requires_human_review
        },
        goto=END
    )

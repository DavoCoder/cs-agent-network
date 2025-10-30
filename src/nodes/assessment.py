from typing import Literal
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END
from langgraph.types import Command
from pydantic import BaseModel, Field
from src.state import ConversationState, AgentContext
from src.utils.routing import determine_routing_decision
from src.utils.message_utils import extract_user_message
from src.prompts import load_prompt

class Assessment(BaseModel):
    """Structured output for ticket assessment"""
    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence in the quality of the response (0.0 to 1.0)"
    )
    risk_level: Literal["low", "medium", "high"] = Field(
        description="Risk level of the operation"
    )
    compliance_risks: str = Field(
        description="Description of any compliance, legal, or policy risks"
    )
    requires_human_review: bool = Field(
        description="Whether this requires human oversight"
    )
    reasoning: str = Field(
        description="Brief explanation of the assessment"
    )


def process_assessment(state: ConversationState) -> Command[Literal["human_review", END]]:
    """ Assess the response and route to human_review or END. """
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

    # Load prompts
    assessment_prompt = load_prompt("assessment_system")
    human_prompt = load_prompt("assessment_human")
    
    # Create LLM with structured output
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
    structured_llm = llm.with_structured_output(Assessment)
    
    # Build assessment prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", assessment_prompt),
        ("human", human_prompt)
    ])
    
    # Invoke LLM for assessment
    messages = prompt.format_messages(
        user_message=user_message,
        ai_response=final_response,
        priority=current_ticket.get("priority", "medium"),
        category=current_ticket.get("category", "unclassified")
    )
    
    assessment = structured_llm.invoke(messages)
    
    # Determine if human review is needed
    needs_review = assessment.requires_human_review
    
    # Determine where to route next using shared routing logic
    goto = determine_routing_decision(
        state=state,
        needs_review=needs_review,
        overall_confidence=assessment.confidence_score,
        risk_level=assessment.risk_level,
        agent_contexts=state.get("agent_contexts", [])
    )
    
    # Update agent context
    agent_context = AgentContext(
        agent_name="assessment",
        confidence_score=assessment.confidence_score,
        reasoning=assessment.reasoning,
        requires_human_review=needs_review,
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
            "pending_human_review": needs_review
        },
        goto=goto
    )
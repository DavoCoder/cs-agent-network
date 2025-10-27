"""
Billing Agent for handling billing inquiries using RAG with Pinecone and LLM-based assessments.
"""
from typing import Literal
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import END
from langgraph.types import Command
from pydantic import BaseModel, Field
from src.orchestration.state import ConversationState, AgentContext
from src.tools.vector_store import retrieve_and_format_kb_results
from src.utils.routing import determine_routing_decision
from src.prompts import load_prompt


class BillingAssessment(BaseModel):
    """Structured output for billing ticket assessment"""
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


def process_billing_ticket(state: ConversationState) -> Command[Literal["human_review", END]]:
    """
    Process a billing support ticket using RAG with Pinecone and LLM-based assessments.
    Uses Command pattern to return state updates.
    
    Args:
        state: Current conversation state
    
    Returns:
        Command with state updates
    """
    current_ticket = state.get("current_ticket")
    if not current_ticket:
        return Command(
            update={"error_message": "No ticket information available"}
        )
    
    messages = state.get("messages", [])
    
    # Extract the latest user message
    user_message = ""
    for msg in reversed(messages):
        if hasattr(msg, "content"):
            user_message = msg.content
            break
    
    # Step 1: Retrieve relevant knowledge base articles using RAG
    kb_context = retrieve_and_format_kb_results(user_message, "billing")
    
    # Step 2: Generate response using RAG
    response = generate_billing_response(user_message, kb_context, messages)
    
    # Step 3: Assess the response for risks, compliance, and confidence
    assessment = assess_billing_ticket(
        user_message=user_message,
        ai_response=response,
        kb_context=kb_context,
        ticket_info=current_ticket
    )
    
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
    
    # Add response message
    new_message = AIMessage(content=response)
    
    # Update agent context
    agent_context = AgentContext(
        agent_name="billing",
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
            "messages": [new_message],
            "agent_contexts": [agent_context],
            "overall_confidence": overall_confidence,
            "risk_assessment": assessment.risk_level,
            "pending_human_review": needs_review
        },
        goto=goto
    )


def generate_billing_response(
    user_message: str,
    kb_context: str,
    conversation_history: list  # noqa: ARG001
) -> str:
    """
    Generate a billing response using RAG.
    
    Args:
        user_message: Customer's question
        kb_context: Retrieved knowledge base context
        conversation_history: Previous messages in conversation (reserved for future use)
    
    Returns:
        AI response to the customer
    """
    # Load system prompt
    system_prompt = load_prompt("billing_response")
    
    # Create LLM
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3
    )
    
    # Build prompt with RAG context
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", """Customer Question: {user_question}

Context from Knowledge Base:
{kb_context}

Please provide a helpful response to the customer.""")
    ])
    
    # Format context
    formatted_kb = kb_context if kb_context else "No specific knowledge base articles found."
    
    # Invoke LLM
    messages = prompt.format_messages(
        user_question=user_message,
        kb_context=formatted_kb
    )
    
    response = llm.invoke(messages)
    return response.content


def assess_billing_ticket(
    user_message: str,
    ai_response: str,
    kb_context: str,
    ticket_info: dict
) -> BillingAssessment:
    """
    Use LLM to assess the billing ticket for risks, compliance, and confidence.
    
    Args:
        user_message: Customer's question
        ai_response: AI's response
        kb_context: Knowledge base context used
        ticket_info: Ticket information
    
    Returns:
        BillingAssessment with risk and compliance analysis
    """
    # Load assessment prompt
    assessment_prompt = load_prompt("billing_assessment")
    
    # Create LLM with structured output
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.0
    )
    structured_llm = llm.with_structured_output(BillingAssessment)
    
    # Build assessment prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", assessment_prompt),
        ("human", """Analyze this billing interaction:

Customer Question: {user_message}

AI Response: {ai_response}

Knowledge Base Used: {kb_context}

Ticket Priority: {priority}
Ticket Category: {category}

Provide your assessment.""")
    ])
    
    # Invoke LLM for assessment
    messages = prompt.format_messages(
        user_message=user_message,
        ai_response=ai_response,
        kb_context=kb_context if kb_context else "None",
        priority=ticket_info.get("priority", "medium"),
        category=ticket_info.get("category", "billing")
    )
    
    assessment = structured_llm.invoke(messages)
    
    return assessment

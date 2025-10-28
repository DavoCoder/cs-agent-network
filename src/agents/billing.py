"""
Billing Agent for handling billing inquiries using RAG with Pinecone and LLM-based assessments.
"""
from typing import Literal
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import END
from langgraph.types import Command
from pydantic import BaseModel, Field
from src.orchestration.state import ConversationState, AgentContext
from src.utils.routing import determine_routing_decision
from src.utils.message_utils import extract_user_message
from src.prompts import load_prompt
from src.tools.vector_store import retrieve_and_format_kb_results
from langchain_core.tools import tool


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


@tool
def search_billing_kb(query: str) -> str:
    """Search billing knowledge base for relevant information"""
    result = retrieve_and_format_kb_results(query, "billing")
    return result if result else "No specific knowledge base articles found."

def process_billing_ticket(state: ConversationState) -> dict:
    """
    Process a billing ticket as a ReAct agent that can call tools.
    Uses LLM with tools to search knowledge base and generate responses.
    
    Args:
        state: Current conversation state
    
    Returns:
        State updates with agent messages
    """
    messages = state.get("messages", [])
    
    # Load system prompt for billing agent
    system_prompt = load_prompt("billing_response")
    if not system_prompt:
        system_prompt = "You are a billing support agent. Use tools to search knowledge base when needed."
    
    # Create LLM with tools bound
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    llm_with_tools = llm.bind_tools([search_billing_kb])
    
    # Build messages with system prompt
    agent_messages = [SystemMessage(content=system_prompt)] + messages
    
    # Invoke LLM
    response = llm_with_tools.invoke(agent_messages)
    
    return {"messages": [response]}


def should_continue(state: ConversationState) -> Literal["billing_tools", "billing_assessment"]:
    """
    Determines whether to route to tools or to assessment.
    
    Args:
        state: Current conversation state
    
    Returns:
        Next node name
    """
    messages = state.get("messages", [])
    if not messages:
        return "billing_assessment"
    
    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "billing_tools"
    else:
        return "billing_assessment"


def process_billing_assessment(state: ConversationState) -> Command[Literal["human_review", END]]:
    """
    Assess the billing response and route to human_review or END.
    
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
    
    # Assess the response (kb_context now embedded in messages history)
    assessment = assess_billing_ticket(
        user_message=user_message,
        ai_response=final_response,
        kb_context="",  # Context is in message history
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
    conversation_history: list
) -> str:
    """
    Generate a billing response using RAG with conversation context.
    
    Args:
        user_message: Customer's question
        kb_context: Retrieved knowledge base context
        conversation_history: Previous messages in conversation for context
    
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
    
    # Get recent conversation context (last 10 messages for context)
    recent_history = conversation_history[-10:] if len(conversation_history) > 10 else conversation_history
    
    # Build messages with conversation history
    messages = []
    
    # Add system prompt
    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))
    
    # Add recent conversation history
    for msg in recent_history:
        # Skip adding the current user message as it will be added separately
        if hasattr(msg, "content"):
            msg_content = msg.content if isinstance(msg.content, str) else str(msg.content)
            if msg_content != user_message:
                # Pass through existing message objects
                messages.append(msg)
    
    # Add current user question with KB context
    formatted_kb = kb_context if kb_context else "No specific knowledge base articles found."
    full_user_message = f"{user_message}\n\n[Knowledge Base Context: {formatted_kb}]"
    messages.append(HumanMessage(content=full_user_message))
    
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

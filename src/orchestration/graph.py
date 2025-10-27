"""
Main orchestration graph using LangGraph 1.0.
Defines the workflow for the multi-agent customer support system.
"""

from typing import Literal
from langgraph.graph import StateGraph, END, START
from src.orchestration.state import ConversationState
from src.agents.orchestrator import classify_ticket_with_llm
from src.agents.technical_support import process_technical_ticket
from src.agents.billing import process_billing_ticket
from src.agents.administration import process_administration_ticket
from src.agents.human_supervisor import human_review_interrupt, process_human_feedback

def create_agent_network():
    """
    Create the main agent network graph using LangGraph 1.0.
    Uses Command pattern for state updates and routing.
    
    Returns:
        Compiled LangGraph StateGraph
    """
    # Create the graph builder
    builder = StateGraph(ConversationState)
    
    # Add nodes for each agent
    # Orchestrator uses Command with routing - specifies which nodes it can go to
    builder.add_node(
        "orchestrator", 
        classify_ticket_with_llm,
        ends=["technical_support", "billing", "administration"]
    )
    
    # Specialized agents use Command for state updates with routing
    builder.add_node(
        "technical_support", 
        process_technical_ticket,
        ends=["human_review", END]
    )
    builder.add_node(
        "billing", 
        process_billing_ticket,
        ends=["human_review", END]
    )
    builder.add_node(
        "administration", 
        process_administration_ticket,
        ends=["human_review", END]
    )
    
    # Human supervisor nodes use Command for state updates
    builder.add_node("human_review", human_review_interrupt)
    builder.add_node("process_feedback", process_human_feedback)
   
    # Conditional routing function
    def route_after_human_review(state: ConversationState) -> Literal["process_feedback", "end"]:
        """
        Route after human review interruption.
        Checks if there's human feedback to process.
        """
        return "process_feedback" if state.get("human_feedback") else "end"
   
    # Define workflow edges
    builder.add_edge(START, "orchestrator")
    
    # No edges needed from specialized agents - Command pattern handles routing
    
    # Human review routes to feedback processing or end
    builder.add_conditional_edges(
        "human_review",
        route_after_human_review,
        {
            "process_feedback": "process_feedback",
            "end": END
        }
    )
    
    # Process feedback completes the workflow
    builder.add_edge("process_feedback", END)
    
    # Compile the graph
    graph = builder.compile()

    return graph
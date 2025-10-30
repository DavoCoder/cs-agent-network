from typing import Literal
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from src.state import ConversationState
from src.nodes.supervisor import classify_ticket_with_llm
from src.nodes.technical_support import (
    process_technical_ticket,
    should_continue as technical_should_continue,
    get_mcp_tools,
)
from src.nodes.billing import (
    process_billing_ticket,
    should_continue,
    search_billing_kb,
)
from src.nodes.assessment import process_assessment
from src.nodes.administration import process_administration_ticket
from src.nodes.human_supervisor import human_review_interrupt, process_human_feedback

async def create_agent_network():
    """ Create the main agent network graph using LangGraph 1.0. """
    # Conditional routing function after human review
    def route_after_human_review(state: ConversationState) -> Literal["process_feedback", "end"]:
        """ Route after human review interruption. Checks if there's human feedback to process. """
        return "process_feedback" if state.get("human_feedback") else "end"
    
    tools = await get_mcp_tools()
    billing_tools_node = ToolNode([search_billing_kb])
    technical_tools_node = ToolNode(tools)
    
    # Create the graph builder
    builder = StateGraph(ConversationState)
    
    # Add nodes for each agent
    # Supervisor uses Command with routing
    builder.add_node(
        "supervisor", 
        classify_ticket_with_llm,
        ends=["technical", "billing", "administration"]
    )
    
    # Technical support agent
    builder.add_node(
        "technical", 
        process_technical_ticket,
        ends=["human_review", END]
    )
    builder.add_node("technical_tools", technical_tools_node)
    
    # Billing agent with ReAct pattern
    builder.add_node("billing", process_billing_ticket)
    builder.add_node("billing_tools", billing_tools_node)
    builder.add_node(
        "assessment",
        process_assessment,
        ends=["human_review", END]
    )
    
    # Administration agent
    builder.add_node(
        "administration", 
        process_administration_ticket,
        ends=["human_review", END]
    )
    
    # Human supervisor nodes
    builder.add_node("human_review", human_review_interrupt)
    builder.add_node("process_feedback", process_human_feedback)
   
    # Define workflow edges
    builder.add_edge(START, "supervisor")

    # Technical agent ReAct-like routing
    builder.add_conditional_edges(
        "technical",
        technical_should_continue,
        {
            "technical_tools": "technical_tools",
            "assessment": "assessment"
        },
    )
    
    # Billing agent ReAct pattern routing
    builder.add_conditional_edges(
        "billing",
        should_continue,
        {
            "billing_tools": "billing_tools",
            "assessment": "assessment"
        }
    )
    
    # Tools complete, loop back to agent
    builder.add_edge("billing_tools", "billing")
    builder.add_edge("technical_tools", "technical")
    
    # Human review routing
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
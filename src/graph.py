"""
Customer support agent network graph using LangGraph 1.0.
"""
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from src.state import ConversationState
from src.configuration import Configuration
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
from src.nodes.administration import (
    process_administration_ticket,
    should_continue as admin_should_continue,
)
from src.tools.administration_tools import call_external_admin_a2a_agent
from src.nodes.human_supervisor import ( 
    human_review_interrupt, 
    process_human_feedback, 
    route_after_feedback
)

async def create_agent_network(config: RunnableConfig):
    """ Create the main agent network graph using LangGraph 1.0. """

    tech_tools = await get_mcp_tools()
    billing_tools_node = ToolNode([search_billing_kb])
    technical_tools_node = ToolNode(tech_tools)
    admin_tools_node = ToolNode([call_external_admin_a2a_agent])
    
    # Create the graph builder
    builder = StateGraph(ConversationState, context_schema=Configuration)
    
    # Add nodes for each agent
    # Supervisor uses Command with routing
    builder.add_node(
        "supervisor", 
        classify_ticket_with_llm,
        ends=["technical", "billing", "administration"]
    )
    
    builder.add_node("technical", process_technical_ticket)
    builder.add_node("technical_tools", technical_tools_node)
    
    builder.add_node("billing", process_billing_ticket)
    builder.add_node("billing_tools", billing_tools_node)

    builder.add_node("administration",  process_administration_ticket)
    builder.add_node("admin_tools", admin_tools_node)
    
    builder.add_node(
        "assessment",
        process_assessment,
        ends=[END]  # Assessment always routes to END via Command.goto
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

    # Administration agent routing
    builder.add_conditional_edges(
        "administration",
        admin_should_continue,
        {
            "admin_tools": "admin_tools",
            "assessment": "assessment",
        }
    )
    
    # Tools complete, loop back to agent
    builder.add_edge("billing_tools", "billing")
    builder.add_edge("technical_tools", "technical")
    # Admin tools always goes to human_review for confirmation after tool execution
    builder.add_edge("admin_tools", "human_review")
    
    builder.add_edge("human_review", "process_feedback")
    
    builder.add_conditional_edges(
        "process_feedback",
        route_after_feedback,
        {
            "administration": "administration",
            "assessment": "assessment",
        }
    )
    
    # Compile the graph
    graph = builder.compile()

    return graph
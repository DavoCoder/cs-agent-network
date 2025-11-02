"""
Customer support agent network graph using LangGraph 1.0.
"""
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from src.configuration import Configuration
from src.nodes.administration import (
    process_administration_ticket,
)
from src.nodes.administration import should_continue as admin_should_continue
from src.nodes.assessment import process_assessment
from src.nodes.billing import (
    process_billing_ticket,
    search_billing_kb,
    should_continue,
)
from src.nodes.human_supervisor import (
    human_review_interrupt,
    process_human_feedback,
)
from src.nodes.supervisor import classify_ticket_with_llm
from src.nodes.technical_support import (
    get_mcp_tools,
    process_technical_ticket,
)
from src.nodes.technical_support import should_continue as technical_should_continue
from src.state import ConversationState
from src.tools.administration_tools import call_external_admin_a2a_agent, set_runtime_config


async def admin_tools_with_config(state: ConversationState, config: RunnableConfig | None = None):
    """
    Wrapper for admin tools node that sets runtime config before tool invocation.
    This allows tools to access authentication context.
    """
    # Set the runtime config as a dict for tool access
    if config:
        config_dict = {"configurable": dict(config.get("configurable", {}))}
    else:
        config_dict = {"configurable": {}}
    
    set_runtime_config(config_dict)
    
    try:
        # Use standard ToolNode to execute tools
        tools_node = ToolNode([call_external_admin_a2a_agent])
        result = await tools_node.ainvoke(state, config)
        return result
    finally:
        # Always clear config after use
        set_runtime_config(None)


async def create_agent_network(config: RunnableConfig):
    """ Create the main agent network graph using LangGraph 1.0. """

    tech_tools = await get_mcp_tools()
    billing_tools_node = ToolNode([search_billing_kb])
    technical_tools_node = ToolNode(tech_tools)
    
    builder = StateGraph(ConversationState, context_schema=Configuration)
    
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
    builder.add_node("admin_tools", admin_tools_with_config)
    
    builder.add_node(
        "assessment",
        process_assessment,
        ends=[END] 
    )
    
    builder.add_node("human_review", human_review_interrupt)
    builder.add_node("process_feedback", process_human_feedback)
   

    builder.add_edge(START, "supervisor")

    builder.add_conditional_edges(
        "technical",
        technical_should_continue,
        {
            "technical_tools": "technical_tools",
            "assessment": "assessment"
        },
    )
    
    builder.add_conditional_edges(
        "billing",
        should_continue,
        {
            "billing_tools": "billing_tools",
            "assessment": "assessment"
        }
    )

    builder.add_conditional_edges(
        "administration",
        admin_should_continue,
        {
            "admin_tools": "admin_tools",
            "human_review": "human_review",
            "assessment": "assessment",
        }
    )
    
    builder.add_edge("billing_tools", "billing")
    builder.add_edge("technical_tools", "technical")
    builder.add_edge("admin_tools", "administration")
    builder.add_edge("human_review", "process_feedback")
    builder.add_edge("process_feedback", "administration")
    
    graph = builder.compile()

    return graph
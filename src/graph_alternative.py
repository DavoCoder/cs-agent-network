"""Create all subagents using the make_graph pattern from react_agent."""

from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langgraph_supervisor import create_supervisor

from src.configuration import Configuration
from src.schemas.assessment import Assessment
from src.tools.administration_tools import call_external_admin_a2a_agent
from src.tools.billing_tools import search_billing_kb
from src.tools.mcp_client import get_mcp_tools
from src.utils.models import load_chat_model


async def build_supervisor_graph(config: RunnableConfig):
    """Build the supervisor graph."""

    configurable = config.get("configurable", {}) if config else {}
    config = Configuration(**configurable) if configurable else Configuration()

    tech_tools = await get_mcp_tools()

    billing_agent = create_agent(
        model=load_chat_model(config.billing_model, config.billing_temperature),
        tools=[search_billing_kb],
        system_prompt=config.billing_system_prompt,
        context_schema=Configuration,
        name="billing_agent",
    )

    technical_agent = create_agent(
        model=load_chat_model(config.technical_agent_model, config.technical_agent_temperature),
        tools=tech_tools,
        system_prompt=config.technical_agent_system_prompt,
        context_schema=Configuration,
        name="technical_agent",
    )

    administration_agent = create_agent(
        model=load_chat_model(config.administration_model, config.administration_temperature),
        system_prompt=config.administration_system_prompt,
        tools=[call_external_admin_a2a_agent],
        context_schema=Configuration,
        middleware=[
            HumanInTheLoopMiddleware(
                interrupt_on={"a2a_admin_action": True},
                description_prefix="Administrative task pending approval",
            ),
        ],
        name="administration_agent",
    )

    assessment_agent = create_agent(
        model=load_chat_model(config.assessment_model, config.assessment_temperature),
        system_prompt=config.assessment_system_prompt,
        context_schema=Configuration,
        response_format=Assessment,
        name="assessment_agent",
    )

    supervisor_graph = create_supervisor(
        agents=[billing_agent, technical_agent, administration_agent, assessment_agent],
        model=load_chat_model(config.supervisor_model, config.supervisor_temperature),
        prompt=config.supervisor_system_prompt,
        context_schema=Configuration,
        supervisor_name="supervisor",
    )

    checkpointer = InMemorySaver()
    compiled_graph = supervisor_graph.compile(checkpointer=checkpointer)

    return compiled_graph

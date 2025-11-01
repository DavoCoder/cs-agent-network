from typing import Literal
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from src.state import ConversationState
from src.tools.vector_store import retrieve_and_format_kb_results
from src.configuration import Configuration
from src.utils.models import load_chat_model

@tool
def search_billing_kb(query: str) -> str:
    """Search billing knowledge base for relevant information"""
    result = retrieve_and_format_kb_results(query, "billing")
    return result if result else "No specific knowledge base articles found."

def process_billing_ticket(state: ConversationState, runtime: RunnableConfig[Configuration]) -> dict:
    """ Billing agent that can search the billing knowledge base and generate responses. """
    messages = state.get("messages", [])
    
    # runtime.context is a Configuration instance, so access attributes directly
    config = runtime.context if runtime.context else Configuration()
   
    # Create LLM with tools bound
    llm = load_chat_model(config.billing_model, temperature=config.billing_temperature)
    llm_with_tools = llm.bind_tools([search_billing_kb])
    
    # Build messages with system prompt
    agent_messages = [SystemMessage(content=config.billing_system_prompt)] + messages
    
    # Invoke LLM
    response = llm_with_tools.invoke(agent_messages)
    
    return {"messages": [response]}


def should_continue(state: ConversationState) -> Literal["billing_tools", "assessment"]:
    """ Determines whether to route to tools or to assessment. """
    messages = state.get("messages", [])
    if not messages:
        return "assessment"
    
    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "billing_tools"
    else:
        return "assessment"
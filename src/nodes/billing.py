from typing import Literal
from langchain_core.messages import SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from src.state import ConversationState
from src.prompts import load_prompt
from src.tools.vector_store import retrieve_and_format_kb_results

@tool
def search_billing_kb(query: str) -> str:
    """Search billing knowledge base for relevant information"""
    result = retrieve_and_format_kb_results(query, "billing")
    return result if result else "No specific knowledge base articles found."

def process_billing_ticket(state: ConversationState) -> dict:
    """ Billing agent that can search the billing knowledge base and generate responses. """
    messages = state.get("messages", [])
    
    # Load system prompt for billing agent
    system_prompt = load_prompt("billing_agent_system")
   
    # Create LLM with tools bound
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    llm_with_tools = llm.bind_tools([search_billing_kb])
    
    # Build messages with system prompt
    agent_messages = [SystemMessage(content=system_prompt)] + messages
    
    # Invoke LLM
    response = llm_with_tools.invoke(agent_messages)
    
    return {"messages": [response]}


def should_continue(state: ConversationState) -> Literal["billing_tools", "billing_assessment"]:
    """ Determines whether to route to tools or to assessment. """
    messages = state.get("messages", [])
    if not messages:
        return "billing_assessment"
    
    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "billing_tools"
    else:
        return "billing_assessment"
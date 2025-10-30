"""
Administration node that uses an external A2A client tool for admin tasks.
"""
from typing import Literal
import os
from langchain_core.messages import SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
import httpx
from src.state import ConversationState
from src.prompts import aload_prompt
from src.utils.a2a_client import build_a2a_jsonrpc_request, parse_a2a_jsonrpc_response


@tool
async def a2a_admin_action(query: str) -> str:
    """External agent to resolve administrative tasks, 
    including account management like providing user access to a group, 
    adding a user to a team, etc. Use this tool when the user request is 
    about administrative tasks. 

    Args:
        query: The user's request for an administrative task.
    Returns:
        str: A string response from the external agent.
    """
    
    base_url = os.getenv("A2A_BASE_URL")
    endpoint = os.getenv("A2A_ENDPOINT", "/rpc")
    api_key = os.getenv("A2A_API_KEY")
    a2a_method = os.getenv("A2A_METHOD", "message/send")

    print(f"************Query: {query}")
    url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    # JSON-RPC 2.0 request body per A2A 0.3.0
    payload = build_a2a_jsonrpc_request(query=query, method=a2a_method)
    timeout_s = float(os.getenv("A2A_TIMEOUT", "15"))
    async with httpx.AsyncClient(timeout=timeout_s) as client:
        #resp = await client.post(url, json=payload, headers=headers)
        resp = await client.get(url, params=payload, headers=headers)
        resp.raise_for_status()
        return parse_a2a_jsonrpc_response(resp.json())


async def process_administration_ticket(state: ConversationState) -> dict:
    """Administration agent that uses an external A2A client tool for admin tasks."""
    print("************Processing Administration Ticket!!!!!!!!!!!!!")
    messages = state.get("messages", [])

    # Initialize and check tool-call limits for this agent
    agent_key = "administration"
    tool_call_counts = state.get("tool_call_counts", {}) or {}
    tool_call_limits = state.get("tool_call_limits", {}) or {}
    # Default limit from env; falls back to 1 if not set
    default_limit = int(os.getenv("ADMIN_TOOL_CALL_LIMIT", os.getenv("GLOBAL_TOOL_CALL_LIMIT", "1")))
    current_count = int(tool_call_counts.get(agent_key, 0))
    limit = int(tool_call_limits.get(agent_key, default_limit))
    if current_count >= limit:
        # Skip tool usage, proceed directly to assessment by returning no tool calls
        print(f"Admin tool-call limit reached ({current_count}/{limit}); skipping tool binding.")
        return {"messages": []}

    system_prompt = await aload_prompt("administration_agent_system")

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
    tools = [a2a_admin_action]
    print("************A2A Tools:", tools)
    # Force the model to call the A2A tool with arguments
    llm_with_tools = llm.bind_tools(tools, tool_choice="a2a_admin_action")

    agent_messages = [SystemMessage(content=system_prompt)] + messages
    response = await llm_with_tools.ainvoke(agent_messages)

    # Increment tool-call count if a tool call was made
    last = response
    made_tool_call = hasattr(last, "tool_calls") and bool(getattr(last, "tool_calls", None))
    if made_tool_call:
        tool_call_counts[agent_key] = current_count + 1
        return {"messages": [response], "tool_call_counts": tool_call_counts, "tool_call_limits": tool_call_limits}

    return {"messages": [response]}

def should_continue(state: ConversationState) -> Literal["admin_tools", "assessment"]:
    """Determines whether to route to tools or to assessment for administration."""
    messages = state.get("messages", [])
    # Enforce configurable limit
    agent_key = "administration"
    tool_call_counts = state.get("tool_call_counts", {}) or {}
    tool_call_limits = state.get("tool_call_limits", {}) or {}
    default_limit = int(os.getenv("ADMIN_TOOL_CALL_LIMIT", os.getenv("GLOBAL_TOOL_CALL_LIMIT", "1")))
    current_count = int(tool_call_counts.get(agent_key, 0))
    limit = int(tool_call_limits.get(agent_key, default_limit))
    if current_count >= limit:
        return "assessment"
    if not messages:
        return "assessment"
    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "admin_tools"
    return "assessment"

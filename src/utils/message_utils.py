from langchain_core.messages import AIMessage, HumanMessage, ToolMessage


def create_ai_message(content: str, messages: list):
    """Helper to create message in correct format based on message history"""
    if isinstance(messages, list) and messages and isinstance(messages[0], dict):
        return {"type": "ai", "content": content}
    return AIMessage(content=content)


def extract_user_message(messages):
    """
    Extract the latest user message from conversation messages.
    Supports multiple message formats from different sources.

    Args:
        messages: List of message objects from conversation state

    Returns:
        str: The user message content, or empty string if not found

    Note:
        Handles multiple formats:
        - HumanMessage objects from LangChain
        - Dictionary format from Agent Chat UI
        - Content as list of dicts like [{'type': 'text', 'text': '...'}]
    """
    if not messages:
        return ""

    def extract_text_from_content(content):
        """Helper to recursively extract text from various content formats"""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            # Process list of items
            for item in content:
                if isinstance(item, dict):
                    # Check for 'text' key in dict
                    if "text" in item:
                        return item["text"]
                # Recursively check nested content
                result = extract_text_from_content(item)
                if result:
                    return result
        if isinstance(content, dict):
            # Check for 'text' or 'content' in dict
            if "text" in content:
                return content["text"]
            if "content" in content:
                return extract_text_from_content(content["content"])
        return ""

    # Iterate through messages in reverse to get the latest user message
    for msg in reversed(messages):
        extracted = ""

        # Handle HumanMessage objects
        if isinstance(msg, HumanMessage):
            if hasattr(msg, "content"):
                extracted = extract_text_from_content(msg.content)

        # Handle dictionary format (from Agent Chat UI)
        elif isinstance(msg, dict):
            # Check for dict with 'text' key
            if "text" in msg:
                extracted = extract_text_from_content(msg["text"])
            # Check for dict with 'content' key
            elif "content" in msg:
                extracted = extract_text_from_content(msg["content"])

        # Handle any object with content attribute
        elif hasattr(msg, "content"):
            extracted = extract_text_from_content(msg.content)

        if extracted:
            return extracted

    return ""


def find_tool_response_and_query(messages: list, tool_name: str) -> tuple[str | None, str | None]:
    """
    Find the most recent tool response and its original query from message history.

    Args:
        messages: List of messages to search through
        tool_name: Name of the tool to find (checks if tool_name is in the ToolMessage name)

    Returns:
        Tuple of (tool_response, original_query) or (None, None) if not found
    """
    tool_response = None
    original_query = None

    # Find the most recent ToolMessage from the specified tool
    for msg in reversed(messages[-10:]):  # Check last 10 messages
        if isinstance(msg, ToolMessage):
            msg_tool_name = getattr(msg, "name", "")
            if tool_name.lower() in msg_tool_name.lower():
                # Extract text response from tool message (tool returns text directly)
                content = msg.content
                tool_response = content if isinstance(content, str) else str(content)
                tool_call_id = getattr(msg, "tool_call_id", None)

                # Find the original query - look for tool call with matching ID, then
                # fallback to user message
                for prev_msg in reversed(messages):
                    if prev_msg == msg:
                        continue  # Skip the ToolMessage itself
                    if hasattr(prev_msg, "tool_calls") and prev_msg.tool_calls:
                        for tool_call in prev_msg.tool_calls:
                            if tool_call.get("id") == tool_call_id:
                                # Try to extract query from tool call args
                                args = tool_call.get("args", {})
                                original_query = args.get("query", args.get("text", ""))
                                if original_query:
                                    break
                        if original_query:
                            break
                    if isinstance(prev_msg, HumanMessage):
                        original_query = extract_user_message([prev_msg])
                        if original_query:
                            break
                break

    return tool_response, original_query


def count_tool_results(messages: list, tool_name: str) -> int:
    """
    Count how many ToolMessage results exist for a given tool.

    Args:
        messages: List of messages to search through
        tool_name: Name of the tool to count results for

    Returns:
        Number of ToolMessage results found for the specified tool
    """
    return sum(
        1
        for msg in messages
        if isinstance(msg, ToolMessage)
        and hasattr(msg, "name")
        and tool_name.lower() in getattr(msg, "name", "").lower()
    )


def format_conversation_history(messages: list, max_messages: int = 10) -> str:
    """
    Format conversation history for context, excluding the current message.

    Extracts up to max_messages from the conversation history, excluding the last
    message (which is typically the current user message being classified).
    Formats them as a readable conversation history string.

    Args:
        messages: List of all messages in the conversation
        max_messages: Maximum number of previous messages to include (default: 10)

    Returns:
        A formatted string containing the conversation history, or empty string if none
    """
    if not messages or len(messages) < 2:
        # Need at least 2 messages (current + at least one previous)
        return ""

    # Exclude the last message (current user message) and get up to max_messages before it
    previous_messages = (
        messages[-(max_messages + 1) : -1] if len(messages) > max_messages + 1 else messages[:-1]
    )

    if not previous_messages:
        return ""

    history_lines = []

    def extract_content(msg):
        """Extract text content from a message object."""
        if isinstance(msg, dict):
            # Dictionary format
            return msg.get("content", msg.get("text", ""))

        if hasattr(msg, "content"):
            content = msg.content
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                # Extract from list of content parts
                for item in content:
                    if isinstance(item, dict) and "text" in item:
                        return item["text"]
                    if isinstance(item, str):
                        return item
        return ""

    for msg in previous_messages:
        content = extract_content(msg)
        if not content:
            continue

        # Truncate very long messages
        if len(content) > 300:
            content = content[:297] + "..."

        # Format based on message type
        if isinstance(msg, HumanMessage) or (isinstance(msg, dict) and msg.get("type") == "human"):
            history_lines.append(f"User: {content}")
        elif isinstance(msg, AIMessage) or (isinstance(msg, dict) and msg.get("type") == "ai"):
            history_lines.append(f"Assistant: {content}")
        elif isinstance(msg, ToolMessage):
            # Skip tool messages or format them briefly
            continue  # Tool messages are internal details, skip for context
        else:
            # Generic message format
            history_lines.append(f"Message: {content}")

    if not history_lines:
        return ""

    return "\n".join(history_lines)

from langchain_core.messages import HumanMessage


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
        elif isinstance(content, list):
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
        elif isinstance(content, dict):
            # Check for 'text' or 'content' in dict
            if "text" in content:
                return content["text"]
            elif "content" in content:
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


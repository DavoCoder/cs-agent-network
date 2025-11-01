"""Utilities for extracting messages from A2A RequestContext."""
import logging

from a2a.server.agent_execution import RequestContext

logger = logging.getLogger(__name__)


def extract_text_from_message(message) -> str:
    """
    Extract text content from an A2A message object.
    
    Tries multiple strategies to extract text from the message:
    1. Extract from message parts (if parts exist)
    2. Extract from direct text attribute
    3. Extract from content attribute (string or dict)
    4. Fallback to string conversion
    
    Args:
        message: An A2A message object (can be various types)
        
    Returns:
        Extracted text string, or empty string if no text found
    """
    if not message:
        return ""
    
    # Try to get text from message parts
    if hasattr(message, 'parts'):
        for part in message.parts:
            if hasattr(part, 'kind') and getattr(part, 'kind', None) == 'text':
                if hasattr(part, 'text'):
                    return part.text
    
    # Try direct text attribute
    if hasattr(message, 'text'):
        return message.text
    
    # Try content attribute
    if hasattr(message, 'content'):
        content = message.content
        if isinstance(content, str):
            return content
        elif isinstance(content, dict):
            # Try to extract text from dict content
            return content.get('text', str(content))
    
    # Fallback: convert to string
    return str(message)


def extract_user_query_from_context(
    context: RequestContext,
    default_message: str = "I need help with an administrative task"
) -> str:
    """
    Extract user query text from A2A RequestContext.
    
    Tries multiple paths to find the user message:
    1. context.params.message (most common path)
    2. context.message (direct attribute)
    3. context.request.params.message (nested structure)
    
    Args:
        context: The A2A RequestContext containing the request
        default_message: Default message to return if no query found
        
    Returns:
        Extracted user query string, or default_message if not found
    """
    user_query = ""
    
    # Path 1: context.params.message (most common)
    if hasattr(context, 'params') and context.params:
        if hasattr(context.params, 'message'):
            message = context.params.message
            user_query = extract_text_from_message(message)
            if user_query:
                logger.debug('Extracted message from context.params.message')
                return user_query
    
    # Path 2: context.message (direct attribute)
    if not user_query and hasattr(context, 'message'):
        user_query = extract_text_from_message(context.message)
        if user_query:
            logger.debug('Extracted message from context.message')
            return user_query
    
    # Path 3: context.request.params.message (nested structure)
    if not user_query and hasattr(context, 'request'):
        request = context.request
        if hasattr(request, 'params') and request.params:
            if hasattr(request.params, 'message'):
                user_query = extract_text_from_message(request.params.message)
                if user_query:
                    logger.debug('Extracted message from context.request.params.message')
                    return user_query
    
    # No query found, use default
    if not user_query:
        logger.warning('No user query found in context, using default message')
        return default_message
    
    return user_query


__all__ = ['extract_text_from_message', 'extract_user_query_from_context']


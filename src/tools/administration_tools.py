"""Administration-related tools for the agent network."""
import logging
import os
from typing import Any, Optional
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
)
from a2a.utils.constants import (
    AGENT_CARD_WELL_KNOWN_PATH,
    EXTENDED_AGENT_CARD_PATH,
)
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# Global variable to store config for tool access
# This is set by the graph before tool invocation
_current_runtime_config: Optional[dict] = None


def set_runtime_config(config: dict | None):
    """ Set the runtime config for tool access. """
    global _current_runtime_config
    _current_runtime_config = config


def get_a2a_admin_agent_key_from_config() -> str | None:
    """ Get the A2A admin agent key from the runtime config. """
    
    if not _current_runtime_config:
        logger.warning('No runtime config available, falling back to env variable')
        return os.getenv("A2A_ADMIN_AGENT_KEY")
    
    # Access langgraph_auth_user from config
    configurable = _current_runtime_config.get("configurable", {})
    auth_user = configurable.get("langgraph_auth_user", {})
    
    # Get the A2A key from auth user
    a2a_key = auth_user.get("a2a_admin_agent_key")
    
    if a2a_key:
        logger.info('Using A2A admin agent key from auth config')
        return a2a_key
    
    # Fallback to env variable
    logger.warning('No A2A key in auth config, falling back to env variable')
    return os.getenv("A2A_ADMIN_AGENT_KEY")


def _extract_text_from_a2a_response(response_dict: dict[str, Any]) -> str:
    """
    Extract text content from A2A response structure.
    
    The A2A response has the structure:
    {
        "id": "...",
        "jsonrpc": "2.0",
        "result": {
            "kind": "message",
            "messageId": "...",
            "parts": [
                {"kind": "text", "text": "actual response text here"}
            ],
            "role": "agent"
        }
    }
    
    Args:
        response_dict: The A2A response dictionary
        
    Returns:
        Extracted text string from result.parts[0].text, or fallback representation
    """
    try:
        result = response_dict.get("result", {})
        if isinstance(result, dict):
            parts = result.get("parts", [])
            if parts and isinstance(parts[0], dict):
                # Find the first text part
                for part in parts:
                    if part.get("kind") == "text" and "text" in part:
                        text = part.get("text", "")
                        if text:
                            return text
                
                # Fallback: if no text part found, try first part anyway
                if parts[0].get("text"):
                    return parts[0].get("text", "")
        
        # If we can't extract text, return a string representation
        logger.warning('Could not extract text from A2A response, using fallback')
        return str(response_dict)
    except (KeyError, TypeError, AttributeError) as e:
        logger.warning('Error extracting text from A2A response: %s', e)
        return str(response_dict)

@tool
async def call_external_admin_a2a_agent(query: str) -> str:
    """
    **USE THIS TOOL FOR ALL ADMINISTRATIVE QUERIES AND REQUESTS.**
    
    Call the external A2A administration agent to handle administrative tasks.
    This tool MUST be used whenever the user asks about or requests any administrative action.
    
    **Capabilities:**
    - Account Management: Create accounts, delete accounts, close accounts
    - Profile Management: Update email addresses, change names, modify profile information
    - Permissions & Roles: Query role information, manage permissions, view access controls
    - Team Management: Add team members, remove team members, invite users, manage team settings
    - Organization Settings: Manage organization configurations, sub-accounts, enterprise settings
    
    **When to use this tool:**
    - User asks "How to..." questions about administrative tasks (e.g., "How can I create a new account?")
    - User requests administrative actions (e.g., "I want to delete my account", "Update my email")
    - User asks about permissions, roles, or access control
    - User wants to manage team members or organization settings
    - User provides confirmation or additional information for administrative actions
    - ANY administrative query, regardless of whether it's informational or an action request
    
    **Important:** Always use this tool for administrative tasks. The external agent will:
    1. Provide information for informational queries (e.g., "How to create account?")
    2. Request confirmation for action requests (e.g., "Create account" -> asks for details)
    3. Execute actions after confirmation (e.g., "Yes, proceed. Email: user@example.com")
    
    Args:
        query: The user's administrative request, question, or confirmation message
        
    Returns:
        The administration agent's response as a text string containing information,
        instructions, or confirmation of executed actions
    """
    port = int(os.getenv('A2A_SERVER_PORT', '9999'))
    host = os.getenv('A2A_SERVER_HOST', '127.0.0.1')

    base_url = f"http://{host}:{port}"
    
    # Get A2A API key from auth config (user-specific) or fallback to env
    api_key = get_a2a_admin_agent_key_from_config()
    
    if not api_key:
        logger.error('No A2A API key available. Set A2A_ADMIN_AGENT_KEY in auth config or A2A_API_KEY in environment.')
        raise RuntimeError('A2A API key not available. Authentication may not be configured correctly.')
    
    logger.info('Using A2A_BASE_URL: %s', base_url)
    logger.info('Using A2A API key from: %s', 'auth config' if _current_runtime_config else 'environment')

    # Create httpx client with timeout
    timeout = httpx.Timeout(30.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as httpx_client:
        

        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=base_url,
            # agent_card_path uses default, extended_agent_card_path also uses default
        )
       
        final_agent_card_to_use: AgentCard | None = None

        try:
            logger.info(
                'Attempting to fetch public agent card from: %s%s',
                base_url,
                AGENT_CARD_WELL_KNOWN_PATH
            )
            _public_card = (
                await resolver.get_agent_card()
            )  # Fetches from default public path
            logger.info('Successfully fetched public agent card:')
            logger.info(
                _public_card.model_dump_json(indent=2, exclude_none=True)
            )
            final_agent_card_to_use = _public_card
            logger.info(
                '\nUsing PUBLIC agent card for client initialization (default).'
            )

            if _public_card.supports_authenticated_extended_card:
                try:
                    logger.info(
                        '\nPublic card supports authenticated extended card. Attempting to fetch from: %s%s',
                        base_url,
                        EXTENDED_AGENT_CARD_PATH
                    )
                    auth_headers_dict = {
                        'Authorization': f'Bearer {api_key}'
                    }
                    _extended_card = await resolver.get_agent_card(
                        relative_card_path=EXTENDED_AGENT_CARD_PATH,
                        http_kwargs={'headers': auth_headers_dict},
                    )
                    logger.info(
                        'Successfully fetched authenticated extended agent card:'
                    )
                    logger.info(
                        _extended_card.model_dump_json(
                            indent=2, exclude_none=True
                        )
                    )
                    final_agent_card_to_use = (
                        _extended_card  # Update to use the extended card
                    )
                    logger.info(
                        '\nUsing AUTHENTICATED EXTENDED agent card for client initialization.'
                    )
                except Exception as e_extended:
                    logger.warning(
                        'Failed to fetch extended agent card: %s. Will proceed with public card.',
                        e_extended,
                        exc_info=True,
                    )
            elif (
                _public_card
            ):  # supports_authenticated_extended_card is False or None
                logger.info(
                    '\nPublic card does not indicate support for an extended card. Using public card.'
                )

        except Exception as e:
            logger.error(
                'Critical error fetching public agent card: %s', e, exc_info=True
            )
            raise RuntimeError(
                'Failed to fetch the public agent card. Cannot continue.'
            ) from e

        client = A2AClient(
            httpx_client=httpx_client, agent_card=final_agent_card_to_use
        )
        logger.info('A2AClient initialized.')

        send_message_payload: dict[str, Any] = {
            'message': {
                'role': 'user',
                'parts': [
                    {'kind': 'text', 'text': query}
                ],
                'messageId': uuid4().hex,
            },
        }
        request = SendMessageRequest(
            id=str(uuid4()), params=MessageSendParams(**send_message_payload)
        )

        response = await client.send_message(request)
        
        # Convert response to dict for parsing
        response_dict = response.model_dump(mode='json', exclude_none=True)
        
        # Extract text from A2A response structure
        extracted_text = _extract_text_from_a2a_response(response_dict)
        
        logger.info('A2A agent response extracted: %s', extracted_text[:100] if len(extracted_text) > 100 else extracted_text)
        
        # Return the extracted text instead of raw JSON
        return extracted_text


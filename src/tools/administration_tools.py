"""Administration-related tools for the agent network."""
import os
import logging
from typing import Any
from uuid import uuid4
import httpx

from langchain_core.tools import tool

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

logger = logging.getLogger(__name__)


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
    Call the external A2A administration agent to handle administrative tasks.
    
    This tool connects to an A2A-compliant administration agent server and sends
    queries for processing. It handles account management, profile updates,
    permissions, team management, and organization settings.
    
    Args:
        query: The user's administrative request or query
        
    Returns:
        The agent's response as a string or JSON dict
    """
    port = int(os.getenv('A2A_SERVER_PORT', '9999'))
    host = os.getenv('A2A_SERVER_HOST', '127.0.0.1')

    base_url = f"http://{host}:{port}"
    api_key = os.getenv("A2A_API_KEY")
    
    logger.info('Using A2A_BASE_URL: %s', base_url)

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


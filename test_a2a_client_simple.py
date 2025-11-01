"""Simple test script for A2A Administration Agent client - direct function call."""
import asyncio
import os
import logging
from typing import Any
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


async def test_a2a_client(query: str) -> str:
    """Direct implementation of the client function for testing."""
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    base_url = os.getenv("A2A_BASE_URL", "http://localhost:9999")
    api_key = os.getenv("A2A_API_KEY", "")

    async with httpx.AsyncClient() as httpx_client:
        # Initialize A2ACardResolver
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=base_url,
        )

        # Fetch Public Agent Card
        final_agent_card_to_use: AgentCard | None = None

        try:
            logger.info(
                'Attempting to fetch public agent card from: %s%s',
                base_url,
                AGENT_CARD_WELL_KNOWN_PATH
            )
            _public_card = await resolver.get_agent_card()
            logger.info('Successfully fetched public agent card')
            final_agent_card_to_use = _public_card
            logger.info('Using PUBLIC agent card for client initialization')

            if _public_card.supports_authenticated_extended_card and api_key:
                try:
                    logger.info(
                        'Attempting to fetch extended agent card from: %s%s',
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
                    logger.info('Successfully fetched authenticated extended agent card')
                    final_agent_card_to_use = _extended_card
                    logger.info('Using AUTHENTICATED EXTENDED agent card')
                except Exception as e_extended:
                    logger.warning(
                        'Failed to fetch extended agent card: %s. Will proceed with public card.',
                        e_extended,
                    )

        except Exception as e:
            logger.error('Critical error fetching public agent card: %s', e, exc_info=True)
            raise RuntimeError('Failed to fetch the public agent card. Cannot continue.') from e

        # Initialize client
        client = A2AClient(
            httpx_client=httpx_client, agent_card=final_agent_card_to_use
        )
        logger.info('A2AClient initialized.')

        # Send message
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
        return response.model_dump(mode='json', exclude_none=True)


async def main():
    """Run tests."""
    # Set environment variables
    if not os.getenv("A2A_BASE_URL"):
        os.environ["A2A_BASE_URL"] = "http://localhost:9999"
    
    print("=" * 60)
    print("Testing A2A Administration Agent Client")
    print("=" * 60)
    print(f"A2A_BASE_URL: {os.getenv('A2A_BASE_URL')}")
    print("=" * 60)
    print()
    
    # Test queries
    test_queries = [
        "I need to delete my account",
        "What permissions does the Developer role have?",
        "How do I add team members?",
        "I want to change my email address",
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'=' * 60}")
        print(f"Test {i}: {query}")
        print(f"{'=' * 60}")
        
        try:
            result = await test_a2a_client(query)
            
            print("\n✅ Response received:")
            print("-" * 60)
            # Extract the actual response text if it's nested
            if isinstance(result, dict):
                # Try to extract text from response
                if 'result' in result:
                    result_data = result['result']
                    # Check for parts array in message
                    if isinstance(result_data, dict):
                        if 'parts' in result_data:
                            for part in result_data['parts']:
                                if part.get('kind') == 'text' and 'text' in part:
                                    print(f"📝 Agent Response:\n{part['text']}")
                                    break
                        elif 'artifacts' in result_data:
                            artifacts = result_data['artifacts']
                            for artifact in artifacts:
                                if 'parts' in artifact:
                                    for part in artifact['parts']:
                                        if part.get('kind') == 'text' and 'text' in part:
                                            print(f"📝 Agent Response:\n{part['text']}")
                                            break
                
                # Also print full JSON for debugging
                import json
                print(f"\n📋 Full Response JSON:")
                print(json.dumps(result, indent=2))
            else:
                print(result)
            print("-" * 60)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        print()


if __name__ == "__main__":
    asyncio.run(main())


"""A2A Mock Server for Administration Agent."""
import os
import logging
import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
)
from a2a_server.admin_agent_executor import (
    AdministrationAgentExecutor,  # type: ignore[import-untyped]
)
from a2a_server.admin_agent_skills import (
    get_public_skills,
    get_extended_skills,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


if __name__ == '__main__':

    # Get port from environment or default to 9999
    port = int(os.getenv('A2A_SERVER_PORT', '9999'))
    host = os.getenv('A2A_SERVER_HOST', '127.0.0.1')

    # Get skills from externalized module
    public_skills = get_public_skills()
    extended_skills = get_extended_skills()

    # Public-facing agent card with basic skills
    public_agent_card = AgentCard(
        name='Administration Agent',
        description=(
            'Administrative support agent that handles account management, '
            'profile updates, permissions, and team management tasks'
        ),
        url=f"http://{host}:{port}/",
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        skills=public_skills,
        supports_authenticated_extended_card=True,
    )

    # Extended agent card with additional skills for authenticated users
    extended_agent_card = public_agent_card.model_copy(
        update={
            'name': 'Administration Agent - Extended Edition',
            'description': (
                'Full-featured administration agent for authenticated users '
                'with access to organization management and advanced permissions'
            ),
            'version': '1.0.1',
            'skills': extended_skills,
        }
    )

    # Initialize request handler with administration agent executor
    request_handler = DefaultRequestHandler(
        agent_executor=AdministrationAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    # Create A2A server application
    server = A2AStarletteApplication(
        agent_card=public_agent_card,
        http_handler=request_handler,
        extended_agent_card=extended_agent_card,
    )

    logger.info('Starting A2A Administration Agent Server on %s:%s', host, port)
    logger.info('Public agent card URL: %s', public_agent_card.url)
    logger.info('Agent supports %d public skills and %d extended skills',
                len(public_agent_card.skills), len(extended_agent_card.skills))
    
    uvicorn.run(server.build(), host=host, port=port)
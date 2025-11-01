"""Administration Agent Executor for A2A mock server."""
import logging

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message

from a2a_server.admin_agent import (
    AdministrationAgent,
)
from a2a_server.context_utils import (
    extract_user_query_from_context,
)

logger = logging.getLogger(__name__)


class AdministrationAgentExecutor(AgentExecutor):
    """Administration Agent Executor for handling admin tasks via A2A."""

    def __init__(self):
        self.agent = AdministrationAgent()

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute the administration agent request."""
        try:
            # Extract user message from context using utility function
            user_query = extract_user_query_from_context(context)
            
            logger.info('Processing admin request: %s', user_query)
            
            # Process the request
            result = await self.agent.process_admin_request(user_query)
            
            # Send response via event queue
            await event_queue.enqueue_event(new_agent_text_message(result))
            logger.info('Admin request processed successfully')
            
        except Exception as e:
            error_msg = f"Error processing administrative request: {str(e)}"
            logger.error('Error in admin executor: %s', e, exc_info=True)
            await event_queue.enqueue_event(new_agent_text_message(error_msg))
            raise

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        """Cancel the current execution (not supported for admin tasks)."""
        logger.info('Cancel requested (context ID: %s), but admin tasks are not cancellable',
                    getattr(context, 'id', 'unknown'))
        await event_queue.enqueue_event(
            new_agent_text_message("Administrative tasks cannot be cancelled once initiated.")
        )
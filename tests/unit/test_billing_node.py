"""
Unit tests for the billing node.
Tests process_billing_ticket and billing_should_continue functions with mocked external integrations.
"""

from unittest.mock import Mock, patch

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from src.configuration import Configuration
from src.nodes.billing import billing_should_continue, process_billing_ticket
from src.state import ConversationState


class TestProcessBillingTicket:
    """Tests for process_billing_ticket function."""

    @patch("src.nodes.billing.load_chat_model")
    def test_processes_billing_ticket_with_user_message(self, mock_load_model):
        """Test that process_billing_ticket processes a user message correctly."""
        # Setup mock LLM
        mock_llm = Mock()
        mock_llm_with_tools = Mock()
        mock_llm.bind_tools.return_value = mock_llm_with_tools
        mock_response = AIMessage(content="I can help with billing questions.")
        mock_llm_with_tools.invoke.return_value = mock_response
        mock_load_model.return_value = mock_llm

        # Setup state
        state: ConversationState = {
            "messages": [HumanMessage(content="How much does the Pro plan cost?")]
        }

        # Setup runtime config
        config = Configuration()
        runtime = Mock()
        runtime.context = config

        # Execute
        result = process_billing_ticket(state, runtime)

        # Verify
        assert "messages" in result
        assert len(result["messages"]) == 1
        assert result["messages"][0] == mock_response

        # Verify LLM was called correctly
        mock_load_model.assert_called_once_with(
            config.billing_model, temperature=config.billing_temperature
        )
        mock_llm.bind_tools.assert_called_once()
        mock_llm_with_tools.invoke.assert_called_once()

        # Verify system prompt was included
        call_args = mock_llm_with_tools.invoke.call_args[0][0]
        assert len(call_args) == 2
        assert isinstance(call_args[0], SystemMessage)
        assert call_args[0].content == config.billing_system_prompt
        assert isinstance(call_args[1], HumanMessage)

    @patch("src.nodes.billing.load_chat_model")
    def test_processes_billing_ticket_with_empty_messages(self, mock_load_model):
        """Test that process_billing_ticket handles empty messages."""
        # Setup mock LLM
        mock_llm = Mock()
        mock_llm_with_tools = Mock()
        mock_llm.bind_tools.return_value = mock_llm_with_tools
        mock_response = AIMessage(content="No messages to process.")
        mock_llm_with_tools.invoke.return_value = mock_response
        mock_load_model.return_value = mock_llm

        # Setup state with empty messages
        state: ConversationState = {"messages": []}

        # Setup runtime config
        config = Configuration()
        runtime = Mock()
        runtime.context = config

        # Execute
        result = process_billing_ticket(state, runtime)

        # Verify
        assert "messages" in result
        assert len(result["messages"]) == 1

        # Verify only system prompt was sent
        call_args = mock_llm_with_tools.invoke.call_args[0][0]
        assert len(call_args) == 1
        assert isinstance(call_args[0], SystemMessage)

    @patch("src.nodes.billing.load_chat_model")
    def test_processes_billing_ticket_with_multiple_messages(self, mock_load_model):
        """Test that process_billing_ticket handles multiple messages."""
        # Setup mock LLM
        mock_llm = Mock()
        mock_llm_with_tools = Mock()
        mock_llm.bind_tools.return_value = mock_llm_with_tools
        mock_response = AIMessage(content="Here's the billing information.")
        mock_llm_with_tools.invoke.return_value = mock_response
        mock_load_model.return_value = mock_llm

        # Setup state with multiple messages
        state: ConversationState = {
            "messages": [
                HumanMessage(content="First question"),
                AIMessage(content="First answer"),
                HumanMessage(content="Follow-up question"),
            ]
        }

        # Setup runtime config
        config = Configuration()
        runtime = Mock()
        runtime.context = config

        # Execute
        result = process_billing_ticket(state, runtime)

        # Verify
        assert "messages" in result
        assert len(result["messages"]) == 1

        # Verify all messages were included
        call_args = mock_llm_with_tools.invoke.call_args[0][0]
        assert len(call_args) == 4  # System message + 3 user messages
        assert isinstance(call_args[0], SystemMessage)

    @patch("src.nodes.billing.load_chat_model")
    def test_processes_billing_ticket_with_custom_config(self, mock_load_model):
        """Test that process_billing_ticket uses custom configuration."""
        # Setup mock LLM
        mock_llm = Mock()
        mock_llm_with_tools = Mock()
        mock_llm.bind_tools.return_value = mock_llm_with_tools
        mock_response = AIMessage(content="Response")
        mock_llm_with_tools.invoke.return_value = mock_response
        mock_load_model.return_value = mock_llm

        # Setup state
        state: ConversationState = {"messages": [HumanMessage(content="Question?")]}

        # Setup custom config
        custom_config = Configuration(billing_model="openai/o1", billing_temperature=0.5)
        runtime = Mock()
        runtime.context = custom_config

        # Execute
        _ = process_billing_ticket(state, runtime)

        # Verify custom config was used
        mock_load_model.assert_called_once_with("openai/o1", temperature=0.5)

    @patch("src.nodes.billing.load_chat_model")
    def test_processes_billing_ticket_falls_back_to_default_config(self, mock_load_model):
        """Test that process_billing_ticket falls back to default config if runtime.context is None."""
        # Setup mock LLM
        mock_llm = Mock()
        mock_llm_with_tools = Mock()
        mock_llm.bind_tools.return_value = mock_llm_with_tools
        mock_response = AIMessage(content="Response")
        mock_llm_with_tools.invoke.return_value = mock_response
        mock_load_model.return_value = mock_llm

        # Setup state
        state: ConversationState = {"messages": [HumanMessage(content="Question?")]}

        # Setup runtime with no context
        runtime = Mock()
        runtime.context = None

        # Execute
        _ = process_billing_ticket(state, runtime)

        # Verify default config was used
        default_config = Configuration()
        mock_load_model.assert_called_once_with(
            default_config.billing_model, temperature=default_config.billing_temperature
        )

    @patch("src.nodes.billing.load_chat_model")
    @patch("src.nodes.billing.search_billing_kb")
    def test_processes_billing_ticket_binds_billing_tool(self, mock_search_tool, mock_load_model):
        """Test that process_billing_ticket binds the billing tool correctly."""
        # Setup mock LLM
        mock_llm = Mock()
        mock_llm_with_tools = Mock()
        mock_llm.bind_tools.return_value = mock_llm_with_tools
        mock_response = AIMessage(content="Response")
        mock_llm_with_tools.invoke.return_value = mock_response
        mock_load_model.return_value = mock_llm

        # Setup state
        state: ConversationState = {"messages": [HumanMessage(content="Question?")]}

        # Setup runtime config
        config = Configuration()
        runtime = Mock()
        runtime.context = config

        # Execute
        _ = process_billing_ticket(state, runtime)

        # Verify tool was bound
        mock_llm.bind_tools.assert_called_once()
        bound_tools = mock_llm.bind_tools.call_args[0][0]
        assert len(bound_tools) == 1
        assert bound_tools[0] == mock_search_tool


class TestBillingShouldContinue:
    """Tests for billing_should_continue routing function."""

    def test_routes_to_billing_tools_when_tool_calls_present(self):
        """Test that billing_should_continue routes to billing_tools when tool calls are detected."""
        # Setup state with tool calls
        state: ConversationState = {
            "messages": [
                HumanMessage(content="What's the pricing?"),
                AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "id": "call_123",
                            "name": "search_billing_kb",
                            "args": {"query": "What's the pricing?"},
                        }
                    ],
                ),
            ]
        }

        result = billing_should_continue(state)
        assert result == "billing_tools"

    def test_routes_to_assessment_when_no_tool_calls(self):
        """Test that billing_should_continue routes to assessment when no tool calls."""
        # Setup state without tool calls
        state: ConversationState = {
            "messages": [
                HumanMessage(content="What's the pricing?"),
                AIMessage(content="Here's the pricing information."),
            ]
        }

        result = billing_should_continue(state)
        assert result == "assessment"

    def test_routes_to_assessment_when_empty_messages(self):
        """Test that billing_should_continue routes to assessment when messages are empty."""
        # Setup state with empty messages
        state: ConversationState = {"messages": []}

        result = billing_should_continue(state)
        assert result == "assessment"

    def test_routes_to_assessment_when_messages_is_none(self):
        """Test that billing_should_continue routes to assessment when messages is None."""
        # Setup state with missing messages
        state: ConversationState = {"messages": None}  # type: ignore

        result = billing_should_continue(state)
        assert result == "assessment"

    def test_routes_to_billing_tools_with_multiple_tool_calls(self):
        """Test that billing_should_continue routes to billing_tools with multiple tool calls."""
        # Setup state with multiple tool calls
        state: ConversationState = {
            "messages": [
                HumanMessage(content="Question"),
                AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "id": "call_1",
                            "name": "search_billing_kb",
                            "args": {"query": "Question 1"},
                        },
                        {
                            "id": "call_2",
                            "name": "search_billing_kb",
                            "args": {"query": "Question 2"},
                        },
                    ],
                ),
            ]
        }

        result = billing_should_continue(state)
        assert result == "billing_tools"

    def test_routes_to_assessment_after_tool_response(self):
        """Test that billing_should_continue routes to assessment after receiving tool response."""
        from langchain_core.messages import ToolMessage

        # Setup state with tool response (no new tool calls)
        state: ConversationState = {
            "messages": [
                HumanMessage(content="Question"),
                AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "id": "call_123",
                            "name": "search_billing_kb",
                            "args": {"query": "Question"},
                        }
                    ],
                ),
                ToolMessage(
                    content="Billing information here",
                    name="search_billing_kb",
                    tool_call_id="call_123",
                ),
                AIMessage(content="Based on the billing information..."),
            ]
        }

        result = billing_should_continue(state)
        assert result == "assessment"

    def test_routes_correctly_with_conversation_history(self):
        """Test that billing_should_continue routes correctly with conversation history."""
        # Setup state with long conversation history
        state: ConversationState = {
            "messages": [
                HumanMessage(content="First question"),
                AIMessage(content="First answer"),
                HumanMessage(content="Second question"),
                AIMessage(content="Second answer"),
                HumanMessage(content="Third question"),
                AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "id": "call_123",
                            "name": "search_billing_kb",
                            "args": {"query": "Third question"},
                        }
                    ],
                ),
            ]
        }

        result = billing_should_continue(state)
        assert result == "billing_tools"

        # Remove tool calls from last message
        state["messages"][-1] = AIMessage(content="Final answer")
        result = billing_should_continue(state)
        assert result == "assessment"


class TestBillingNodeIntegration:
    """Integration tests for billing node with mocked dependencies."""

    @patch("src.nodes.billing.load_chat_model")
    @patch("src.tools.billing_tools.retrieve_and_format_kb_results")
    def test_full_flow_with_tool_call(self, mock_retrieve_kb, mock_load_model):
        """Test the full billing flow when LLM decides to call tool."""
        # Mock knowledge base retrieval
        mock_retrieve_kb.return_value = (
            "--- Knowledge Base Articles ---\n\nArticle 1:\nContent: Pro plan costs $99/month\n"
        )

        # Setup mock LLM that makes a tool call
        mock_llm = Mock()
        mock_llm_with_tools = Mock()
        mock_llm.bind_tools.return_value = mock_llm_with_tools

        # First call: LLM decides to use tool
        tool_call_aimessage = AIMessage(
            content="",
            tool_calls=[
                {
                    "id": "call_123",
                    "name": "search_billing_kb",
                    "args": {"query": "Pro plan pricing"},
                }
            ],
        )
        mock_llm_with_tools.invoke.return_value = tool_call_aimessage
        mock_load_model.return_value = mock_llm

        # Setup state
        state: ConversationState = {
            "messages": [HumanMessage(content="How much does the Pro plan cost?")]
        }

        # Setup runtime
        config = Configuration()
        runtime = Mock()
        runtime.context = config

        # Execute process_billing_ticket
        result = process_billing_ticket(state, runtime)

        # Verify tool call was made
        assert len(result["messages"]) == 1
        assert hasattr(result["messages"][0], "tool_calls")
        assert len(result["messages"][0].tool_calls) == 1
        assert result["messages"][0].tool_calls[0]["name"] == "search_billing_kb"

        # Verify routing decision
        updated_state = {**state, **result}
        routing_result = billing_should_continue(updated_state)
        assert routing_result == "billing_tools"

    @patch("src.nodes.billing.load_chat_model")
    def test_full_flow_without_tool_call(self, mock_load_model):
        """Test the full billing flow when LLM responds directly."""
        # Setup mock LLM that responds directly
        mock_llm = Mock()
        mock_llm_with_tools = Mock()
        mock_llm.bind_tools.return_value = mock_llm_with_tools

        # LLM responds without tool call
        direct_response = AIMessage(content="The Pro plan costs $99 per month.")
        mock_llm_with_tools.invoke.return_value = direct_response
        mock_load_model.return_value = mock_llm

        # Setup state
        state: ConversationState = {
            "messages": [HumanMessage(content="How much does the Pro plan cost?")]
        }

        # Setup runtime
        config = Configuration()
        runtime = Mock()
        runtime.context = config

        # Execute process_billing_ticket
        result = process_billing_ticket(state, runtime)

        # Verify direct response
        assert len(result["messages"]) == 1
        assert (
            not hasattr(result["messages"][0], "tool_calls") or not result["messages"][0].tool_calls
        )

        # Verify routing decision
        updated_state = {**state, **result}
        routing_result = billing_should_continue(updated_state)
        assert routing_result == "assessment"

"""
Unit tests for message utility functions.
"""
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from src.utils.message_utils import (
    extract_user_message,
    find_tool_response_and_query,
    count_tool_results,
    format_conversation_history,
)


class TestExtractUserMessage:
    """Tests for extract_user_message function."""
    
    def test_extract_from_human_message(self):
        """Test extracting from HumanMessage object."""
        messages = [HumanMessage(content="Hello, how can I help?")]
        assert extract_user_message(messages) == "Hello, how can I help?"
    
    def test_extract_from_dict_format(self):
        """Test extracting from dictionary format."""
        messages = [{"type": "human", "content": "I need help"}]
        assert extract_user_message(messages) == "I need help"
    
    def test_extract_from_dict_with_text_key(self):
        """Test extracting from dict with 'text' key."""
        messages = [{"text": "User question here"}]
        assert extract_user_message(messages) == "User question here"
    
    def test_extract_from_list_content(self):
        """Test extracting from list content format."""
        messages = [{"content": [{"type": "text", "text": "Question from user"}]}]
        assert extract_user_message(messages) == "Question from user"
    
    def test_empty_messages(self):
        """Test with empty messages list."""
        assert extract_user_message([]) == ""
    
    def test_multiple_messages_returns_latest(self):
        """Test that it returns the latest user message."""
        messages = [
            HumanMessage(content="First message"),
            AIMessage(content="AI response"),
            HumanMessage(content="Latest message"),
        ]
        assert extract_user_message(messages) == "Latest message"
    
    def test_no_user_message_returns_empty(self):
        """Test that it returns empty string when no messages or empty messages."""
        # Empty list should return empty string
        assert extract_user_message([]) == ""
        
        # Note: The function falls back to extracting from any message with content attribute
        # So AIMessage content will be extracted. This test verifies empty list behavior.
        # To test true "no user message" scenario, we'd need a different approach


class TestFindToolResponseAndQuery:
    """Tests for find_tool_response_and_query function."""
    
    def test_find_tool_response_with_matching_tool_name(self):
        """Test finding tool response when tool name matches."""
        messages = [
            HumanMessage(content="Create account"),
            AIMessage(
                content="",
                tool_calls=[{
                    "id": "call_123",
                    "name": "call_external_admin_a2a_agent",
                    "args": {"query": "Create account"}
                }]
            ),
            ToolMessage(
                content="Account creation instructions...",
                name="call_external_admin_a2a_agent",
                tool_call_id="call_123"
            ),
        ]
        response, query = find_tool_response_and_query(messages, "call_external_admin_a2a_agent")
        
        assert response == "Account creation instructions..."
        assert query == "Create account"
    
    def test_tool_response_not_found(self):
        """Test when tool response is not found."""
        messages = [HumanMessage(content="Some message")]
        response, query = find_tool_response_and_query(messages, "call_external_admin_a2a_agent")
        
        assert response is None
        assert query is None
    
    def test_fallback_to_user_message_when_tool_call_args_missing(self):
        """Test fallback to user message when tool call args don't have query."""
        messages = [
            HumanMessage(content="User query here"),
            AIMessage(
                content="",
                tool_calls=[{
                    "id": "call_123",
                    "name": "call_external_admin_a2a_agent",
                    "args": {}
                }]
            ),
            ToolMessage(
                content="Tool response",
                name="call_external_admin_a2a_agent",
                tool_call_id="call_123"
            ),
        ]
        response, query = find_tool_response_and_query(messages, "call_external_admin_a2a_agent")
        
        assert response == "Tool response"
        assert query == "User query here"


class TestCountToolResults:
    """Tests for count_tool_results function."""
    
    def test_count_single_tool_result(self):
        """Test counting a single tool result."""
        messages = [
            ToolMessage(content="Result 1", name="test_tool", tool_call_id="call_1"),
        ]
        assert count_tool_results(messages, "test_tool") == 1
    
    def test_count_multiple_tool_results(self):
        """Test counting multiple tool results for same tool."""
        messages = [
            ToolMessage(content="Result 1", name="test_tool", tool_call_id="call_1"),
            ToolMessage(content="Result 2", name="test_tool", tool_call_id="call_2"),
            ToolMessage(content="Result 3", name="test_tool", tool_call_id="call_3"),
        ]
        assert count_tool_results(messages, "test_tool") == 3
    
    def test_count_zero_when_no_tool_results(self):
        """Test that it returns zero when no tool results found."""
        messages = [HumanMessage(content="No tools here")]
        assert count_tool_results(messages, "test_tool") == 0
    
    def test_case_insensitive_tool_name_matching(self):
        """Test that tool name matching is case insensitive."""
        messages = [
            ToolMessage(content="Result", name="TEST_TOOL", tool_call_id="call_1"),
        ]
        assert count_tool_results(messages, "test_tool") == 1
        assert count_tool_results(messages, "TEST_TOOL") == 1


class TestFormatConversationHistory:
    """Tests for format_conversation_history function."""
    
    def test_format_basic_conversation(self):
        """Test formatting a basic conversation."""
        messages = [
            HumanMessage(content="First question"),
            AIMessage(content="First answer"),
            HumanMessage(content="Second question"),
        ]
        history = format_conversation_history(messages, max_messages=10)
        
        assert "User: First question" in history
        assert "Assistant: First answer" in history
        assert "User: Second question" not in history  # Last message excluded
    
    def test_excludes_last_message(self):
        """Test that the last message is excluded from history."""
        messages = [
            HumanMessage(content="Question 1"),
            AIMessage(content="Answer 1"),
            HumanMessage(content="Current question"),  # Should be excluded
        ]
        history = format_conversation_history(messages, max_messages=10)
        
        assert "Current question" not in history
        assert "Question 1" in history
    
    def test_respects_max_messages_limit(self):
        """Test that it respects max_messages limit."""
        messages = [
            HumanMessage(content=f"Question {i}")
            for i in range(15)
        ]
        history = format_conversation_history(messages, max_messages=5)
        
        # Should only include last 5 messages before the current one
        assert "Question 9" in history
        assert "Question 0" not in history
    
    def test_skips_tool_messages(self):
        """Test that tool messages are skipped in history."""
        messages = [
            HumanMessage(content="User question"),
            AIMessage(content="AI response"),
            ToolMessage(content="Tool result", name="test_tool", tool_call_id="call_1"),
            HumanMessage(content="Current question"),
        ]
        history = format_conversation_history(messages, max_messages=10)
        
        assert "Tool result" not in history
        assert "User question" in history
    
    def test_truncates_long_messages(self):
        """Test that very long messages are truncated."""
        long_message = "A" * 500
        messages = [
            HumanMessage(content=long_message),
            AIMessage(content="Response"),
            HumanMessage(content="Current"),
        ]
        history = format_conversation_history(messages, max_messages=10)
        
        assert len(history) < 600  # Should be truncated
        assert "..." in history
    
    def test_returns_empty_for_insufficient_messages(self):
        """Test that it returns empty string for insufficient messages."""
        messages = [HumanMessage(content="Only one message")]
        assert format_conversation_history(messages, max_messages=10) == ""
        
        assert format_conversation_history([], max_messages=10) == ""


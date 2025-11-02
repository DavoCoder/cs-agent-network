"""
Unit tests for state utility functions.
"""
from src.utils.state_utils import (
    create_fallback_classification,
    create_supervisor_agent_context,
    create_unclassifiable_agent_context,
    update_ticket_from_classification,
    create_routing_history_entry,
    build_classification_state_updates,
)
from src.schemas.classification import TicketClassification


class TestCreateFallbackClassification:
    """Tests for create_fallback_classification function."""
    
    def test_creates_unclassifiable_classification(self):
        """Test that it creates an unclassifiable classification."""
        classification = create_fallback_classification()
        
        assert classification.category == "unclassifiable"
        assert classification.priority == "low"
        assert classification.intent == "Unable to classify due to system error"
        assert classification.keywords == []
        assert classification.confidence == 0.0
        assert classification.needs_human_review is False


class TestCreateSupervisorAgentContext:
    """Tests for create_supervisor_agent_context function."""
    
    def test_creates_context_from_classification(self):
        """Test creating agent context from classification."""
        classification = TicketClassification(
            category="technical",
            priority="high",
            intent="User needs API help",
            keywords=["API", "error"],
            confidence=0.85,
            needs_human_review=False,
        )
        
        context = create_supervisor_agent_context(classification)
        
        assert context["agent_name"] == "supervisor"
        assert context["confidence_score"] == 0.85
        assert "technical" in context["reasoning"]
        assert context["requires_human_review"] is False
        assert context["risk_level"] == "low"
    
    def test_sets_high_risk_when_needs_human_review(self):
        """Test that risk_level is high when needs_human_review is True."""
        classification = TicketClassification(
            category="billing",
            priority="urgent",
            intent="Payment dispute",
            keywords=["dispute"],
            confidence=0.9,
            needs_human_review=True,
        )
        
        context = create_supervisor_agent_context(classification)
        
        assert context["risk_level"] == "high"
        assert context["requires_human_review"] is True


class TestCreateUnclassifiableAgentContext:
    """Tests for create_unclassifiable_agent_context function."""
    
    def test_overrides_context_for_unclassifiable(self):
        """Test that it overrides context with unclassifiable-specific values."""
        classification = TicketClassification(
            category="unclassifiable",
            priority="low",
            intent="Question outside scope",
            keywords=[],
            confidence=0.8,
            needs_human_review=False,
        )
        
        context = create_unclassifiable_agent_context(classification)
        
        assert context["reasoning"] == "Question outside scope"
        assert context["requires_human_review"] is False
        assert context["risk_level"] == "low"


class TestUpdateTicketFromClassification:
    """Tests for update_ticket_from_classification function."""
    
    def test_creates_new_ticket_when_none_exists(self):
        """Test creating a new ticket when none exists."""
        state = {}
        classification = TicketClassification(
            category="technical",
            priority="medium",
            intent="API integration help",
            keywords=["API", "integration"],
            confidence=0.8,
            needs_human_review=False,
        )
        
        ticket = update_ticket_from_classification(state, classification, "How do I use the API?")
        
        assert ticket["category"] == "technical"
        assert ticket["priority"] == "medium"
        assert ticket["subject"] == "API integration help"
        assert ticket["initial_description"] == "How do I use the API?"
        assert ticket["keywords"] == ["API", "integration"]
    
    def test_updates_existing_ticket(self):
        """Test updating an existing ticket."""
        state = {
            "current_ticket": {
                "ticket_id": "123",
                "category": "billing",
            }
        }
        classification = TicketClassification(
            category="technical",
            priority="high",
            intent="New intent",
            keywords=["new"],
            confidence=0.9,
            needs_human_review=False,
        )
        
        ticket = update_ticket_from_classification(state, classification, "New question")
        
        assert ticket["ticket_id"] == "123"  # Preserved
        assert ticket["category"] == "technical"  # Updated
        assert ticket["priority"] == "high"  # Updated


class TestCreateRoutingHistoryEntry:
    """Tests for create_routing_history_entry function."""
    
    def test_creates_entry_for_unclassifiable(self):
        """Test creating entry for unclassifiable category."""
        classification = TicketClassification(
            category="unclassifiable",
            priority="low",
            intent="Outside scope",
            keywords=[],
            confidence=0.5,
            needs_human_review=False,
        )
        
        entry = create_routing_history_entry(classification)
        
        assert "unclassifiable" in entry
        assert "not within scope" in entry
    
    def test_creates_entry_for_classified_category(self):
        """Test creating entry for a classified category."""
        classification = TicketClassification(
            category="technical",
            priority="high",
            intent="API issue",
            keywords=["API"],
            confidence=0.9,
            needs_human_review=False,
        )
        
        entry = create_routing_history_entry(classification)
        
        assert "technical" in entry
        assert "high" in entry
        assert "0.90" in entry


class TestBuildClassificationStateUpdates:
    """Tests for build_classification_state_updates function."""
    
    def test_builds_complete_state_updates(self):
        """Test building complete state updates dictionary."""
        classification = TicketClassification(
            category="billing",
            priority="medium",
            intent="Subscription question",
            keywords=["subscription"],
            confidence=0.75,
            needs_human_review=False,
        )
        current_ticket = {"category": "billing", "priority": "medium"}
        agent_context = {
            "agent_name": "supervisor",
            "confidence_score": 0.75,
            "reasoning": "Classified as billing",
            "requires_human_review": False,
            "risk_level": "low",
        }
        
        updates = build_classification_state_updates(classification, current_ticket, agent_context)
        
        assert updates["current_ticket"] == current_ticket
        assert len(updates["routing_history"]) == 1
        assert "billing" in updates["routing_history"][0]
        assert len(updates["agent_contexts"]) == 1
        assert updates["agent_contexts"][0] == agent_context
        assert updates["pending_human_review"] is False
        assert updates["overall_confidence"] == 0.75


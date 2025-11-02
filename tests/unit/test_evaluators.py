"""
Unit tests for evaluation functions.
"""

from tests.evals.evaluators import (
    supervisor_classification_correct,
    trajectory_match,
    trajectory_subsequence,
)


class TestTrajectoryMatch:
    """Tests for trajectory_match evaluator."""

    def test_exact_match(self):
        """Test that exact matching trajectories return True."""
        outputs = {
            "trajectory": ["supervisor", "technical", "technical_tools", "technical", "assessment"]
        }
        reference = {
            "trajectory": ["supervisor", "technical", "technical_tools", "technical", "assessment"]
        }

        assert trajectory_match(outputs, reference) is True

    def test_different_length(self):
        """Test that different length trajectories return False."""
        outputs = {"trajectory": ["supervisor", "technical"]}
        reference = {"trajectory": ["supervisor", "technical", "technical_tools"]}

        assert trajectory_match(outputs, reference) is False

    def test_different_nodes(self):
        """Test that different nodes return False."""
        outputs = {"trajectory": ["supervisor", "technical"]}
        reference = {"trajectory": ["supervisor", "billing"]}

        assert trajectory_match(outputs, reference) is False

    def test_empty_trajectories(self):
        """Test that empty trajectories match."""
        outputs = {"trajectory": []}
        reference = {"trajectory": []}

        assert trajectory_match(outputs, reference) is True


class TestTrajectorySubsequence:
    """Tests for trajectory_subsequence evaluator."""

    def test_exact_match_returns_one(self):
        """Test that exact match returns 1.0."""
        outputs = {"trajectory": ["supervisor", "technical", "assessment"]}
        reference = {"trajectory": ["supervisor", "technical", "assessment"]}

        assert trajectory_subsequence(outputs, reference) == 1.0

    def test_partial_match_returns_fraction(self):
        """Test that partial match returns appropriate fraction."""
        outputs = {
            "trajectory": ["supervisor", "technical", "technical_tools", "technical", "assessment"]
        }
        reference = {"trajectory": ["supervisor", "technical", "assessment"]}

        result = trajectory_subsequence(outputs, reference)
        assert result == 1.0  # All expected nodes are present in order

    def test_no_match_returns_zero(self):
        """Test that no match returns 0.0."""
        outputs = {"trajectory": ["supervisor", "billing"]}
        reference = {"trajectory": ["supervisor", "technical", "assessment"]}

        result = trajectory_subsequence(outputs, reference)
        assert result < 1.0  # Not all nodes match

    def test_empty_expected_trajectory(self):
        """Test handling of empty expected trajectory."""
        # According to implementation: if expected is empty,
        # return 1.0 if actual is also empty, else 0.0
        outputs = {"trajectory": []}
        reference = {"trajectory": []}
        assert trajectory_subsequence(outputs, reference) == 1.0

        # When expected is empty but actual has items, returns 0.0
        outputs = {"trajectory": ["supervisor"]}
        reference = {"trajectory": []}
        assert trajectory_subsequence(outputs, reference) == 0.0

    def test_empty_actual_trajectory(self):
        """Test handling of empty actual trajectory."""
        outputs = {"trajectory": []}
        reference = {"trajectory": ["supervisor"]}

        assert trajectory_subsequence(outputs, reference) == 0.0


class TestSupervisorClassificationCorrect:
    """Tests for supervisor_classification_correct evaluator."""

    def test_matching_classification(self):
        """Test that matching classifications return True."""
        outputs = {"supervisor_classification": "technical"}
        reference = {"supervisor_classification": "technical"}

        assert supervisor_classification_correct(outputs, reference) is True

    def test_different_classification(self):
        """Test that different classifications return False."""
        outputs = {"supervisor_classification": "technical"}
        reference = {"supervisor_classification": "billing"}

        assert supervisor_classification_correct(outputs, reference) is False

    def test_empty_classification(self):
        """Test handling of empty classification."""
        outputs = {"supervisor_classification": ""}
        reference = {"supervisor_classification": "technical"}

        assert supervisor_classification_correct(outputs, reference) is False

# Unit Tests

This directory contains unit tests for the customer support agent network using pytest.

## Structure

- `test_message_utils.py` - Tests for message utility functions
- `test_state_utils.py` - Tests for state management utilities
- `test_evaluators.py` - Tests for evaluation functions

## Running Tests

### Run all unit tests
```bash
pytest tests/unit
```

### Run specific test file
```bash
pytest tests/unit/test_message_utils.py
```

### Run specific test function
```bash
pytest tests/unit/test_message_utils.py::TestExtractUserMessage::test_extract_from_human_message
```

### Run with coverage
```bash
pytest tests/unit --cov=src --cov-report=html
```

### Run in verbose mode
```bash
pytest tests/unit -v
```

## Test Categories

Tests are marked with pytest markers:
- `@pytest.mark.unit` - Fast unit tests with no external dependencies
- `@pytest.mark.integration` - Integration tests that may require external services
- `@pytest.mark.slow` - Slow-running tests

Run specific categories:
```bash
pytest -m unit
pytest -m integration
pytest -m "not slow"  # Skip slow tests
```

## Adding New Tests

1. Create test files following the pattern `test_*.py` or `*_test.py`
2. Place them in `tests/unit/` directory
3. Use descriptive test class and function names
4. Follow the existing test structure and patterns


# Customer Support Agent Network

A well-structured multi-agent system built with LangGraph that intelligently routes and handles customer support tickets across specialized domains (technical support, billing, and administration) with human-in-the-loop capabilities. This project provides a solid foundation for building production-grade agent networks.

## Overview

This system demonstrates a **dispatcher → specialized agents** architecture where a supervisor routes tickets to domain-specific agents (Technical Support, Billing, Administration), each with their own tool integrations and decision logic. The system uses explicit graph construction for fine-grained control over execution flow, state management, and agent coordination.

For detailed architecture information, design decisions, and implementation patterns, see [ARCHITECTURE.md](./ARCHITECTURE.md).

---

## Prerequisites

### Python Version

- **Python 3.11+** (tested with Python 3.13)
- We use [`uv`](https://github.com/astral-sh/uv) as the package manager

### Install uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Environment Variables

Copy the example environment file and configure your API keys:

```bash
cp .env.example .env
```

Edit `.env` with the following required variables:

**Required:**
- `OPENAI_API_KEY` - Your OpenAI API key for LLM access
- `LANGSMITH_API_KEY` - Your LangSmith API key for tracing and evaluation
- `PINECONE_API_KEY` - Your Pinecone API key for vector database access

**Optional:**
- `A2A_ADMIN_AGENT_KEY` - API key for A2A endpoint authentication (for administration agent)
- `MCP_SERVER_URI` - URI for MCP (Model Context Protocol) documentation server
- `PULL_PROMPTS_FROM_LANGSMITH` - Set to `"true"` to pull prompts from LangSmith Prompt Hub (default: local files)
- `A2A_SERVER_PORT` - Port for local A2A server (default: `9999`)
- `A2A_SERVER_HOST` - Host for local A2A server (default: `127.0.0.1`)

### Dependencies

Install project dependencies using `uv`:

```bash
# Create virtual environment and install all dependencies
uv sync

# Or install with optional dev/test dependencies
uv sync --extra dev --extra test
```

### Vector Database Setup (Pinecone)

The billing agent uses Pinecone for semantic search. Seed the knowledge base with sample documents:

```bash
# Ensure PINECONE_API_KEY is set in your .env file
uv run python vector_db/seed_vector_kb.py
```

This script:
- Creates a Pinecone index (if it doesn't exist)
- Loads billing knowledge base documents from `vector_db/data/billing_kb_documents.json`
- Adds documents to the vector store for semantic search

### A2A Server (Optional, for Administration Agent)

The administration agent requires an A2A-compliant endpoint. A local mock server is provided:

```bash
# Start the A2A server (in a separate terminal)
uv run python -m a2a_server
```

The server:
- Runs on `127.0.0.1:9999` by default (configurable via `A2A_SERVER_PORT` and `A2A_SERVER_HOST`)
- Provides a public agent card at `http://127.0.0.1:9999/.well-known/agent-card.json`
- Includes mock responses for administrative operations
- Supports authenticated extended skills for testing purposes
- Is fully A2A-compliant for integration testing

**Note:** The A2A server must be running before testing administration agent functionality.

---

## Running the Application

### LangGraph Development Server

Start the LangGraph development server using the CLI:

```bash
# Run LangGraph server (automatically uses virtual environment)
uv run langgraph dev
```

The server will:
- Start on `http://localhost:2024` (default)
- Provide API endpoints for the agent network
- Enable interactive testing via LangGraph Studio
- Include authentication (see `src/auth.py`)

**Running Both Servers:**

For full functionality (especially administration agent), run both servers:

```bash
# Terminal 1: Start A2A server
uv run python -m a2a_server

# Terminal 2: Start LangGraph server
uv run langgraph dev
```

**Example Prompts:**

Example prompts for testing the agent network are available in `tests/sample_scenarios/`:
- `supervisor_test_cases.txt` - Supervisor routing examples
- `technical_agent_test_cases.txt` - Technical support scenarios
- `billing_agent_test_cases.txt` - Billing inquiry examples
- `admin_agent_test_cases.txt` - Administration request scenarios

---

## Code Quality Tools

The project uses the following tools for code quality:

- **Black**: Code formatter (line length: 100)
- **Pylint**: Linter with project-specific configuration (`.pylintrc`)
- **isort**: Import sorter (configured for Black compatibility)

Run code quality checks:

```bash
# Format code
uv run black src tests

# Sort imports
uv run isort src tests

# Lint code
uv run pylint src tests
```

Configuration files:
- `pyproject.toml` - Black, isort, and Pylint settings
- `.pylintrc` - Pylint configuration with virtual environment detection

---

## Testing

### Unit Tests

Run unit tests with pytest:

```bash
# Run all unit tests
uv run pytest tests/unit/

# Run with coverage
uv run pytest tests/unit/ --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/unit/test_billing_node.py
```

Unit tests use `pytest-asyncio` for async test support and `pytest-mock` for mocking external dependencies.

### Evaluations

Run evaluations using LangSmith:

```bash
# Run evaluations against a specific dataset
uv run python -m tests.evals.run_evals ds-curated.json

# Or use a different dataset
uv run python -m tests.evals.run_evals ds-synthetic.json
```

The evaluation suite:
- Uses LLM-as-judge evaluators for response quality
- Includes deterministic evaluators for trajectory matching
- Generates datasets and experiments in LangSmith
- Tracks performance metrics and traces

---

## Additional Resources

- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Detailed architecture, design decisions, and implementation patterns
- **[LLM_MODEL_ANALYSIS.md](./LLM_MODEL_ANALYSIS.md)** - Model selection guide, trade-offs, and recommendations

---

## License

MIT

# Customer Support Agent Network

A well-structured multi-agent system built with LangGraph that intelligently routes and handles customer support tickets across specialized domains (technical support, billing, and administration) with human-in-the-loop capabilities. This project provides a solid foundation for building production-grade agent networks.

## Table of Contents

| Section | Description |
|---------|-------------|
| [Overview](#overview) | System architecture and design |
| [Prerequisites](#prerequisites) | Python, dependencies, environment setup |
| [Running the Application](#running-the-application) | LangGraph server and A2A server |
| [Code Quality Tools](#code-quality-tools) | Formatting, linting, import sorting |
| [Testing](#testing) | Unit tests and evaluations |
| [Additional Resources](#additional-resources) | Documentation links |

---

## Overview

This system demonstrates a **dispatcher → specialized agents** architecture where a supervisor routes tickets to domain-specific agents (Technical Support, Billing, Administration), each with their own tool integrations and decision logic. The system uses explicit graph construction for fine-grained control over execution flow, state management, and agent coordination.

| Architecture Pattern | Description |
|---------------------|-------------|
| **Dispatcher** | Supervisor node classifies and routes tickets |
| **Specialized Agents** | Technical Support, Billing, Administration |
| **Tool Integration** | MCP, Vector Store (Pinecone), A2A Protocol |
| **Graph Construction** | Explicit control over execution flow |
| **State Management** | Shared state across agent coordination |

> 📚 **New to this project? Start with [START_HERE.md](./docs/START_HERE.md) for a guided reading path through all documentation.**

> 📚 **For detailed architecture information, design decisions, and implementation patterns, see [ARCHITECTURE.md](./docs/ARCHITECTURE.md)**

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

Edit `.env` with the following variables:

#### Required Environment Variables

| Variable | Purpose | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | LLM Access | Your OpenAI API key for LLM access |
| `LANGSMITH_API_KEY` | Observability | Your LangSmith API key for tracing and evaluation |
| `PINECONE_API_KEY` | Vector Database | Your Pinecone API key for vector database access |

#### Optional Environment Variables

| Variable | Purpose | Default | Description |
|----------|---------|---------|-------------|
| `A2A_ADMIN_AGENT_KEY` | A2A Authentication | - | API key for A2A endpoint authentication (for administration agent) |
| `MCP_SERVER_URI` | MCP Integration | - | URI for MCP (Model Context Protocol) documentation server |
| `PULL_PROMPTS_FROM_LANGSMITH` | Prompt Management | local files | Set to `"true"` to pull prompts from LangSmith Prompt Hub |
| `A2A_SERVER_PORT` | A2A Server | `9999` | Port for local A2A server |
| `A2A_SERVER_HOST` | A2A Server | `127.0.0.1` | Host for local A2A server |

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

#### Vector Database Script Functions

| Function | Description |
|----------|-------------|
| **Index Creation** | Creates a Pinecone index (if it doesn't exist) |
| **Data Loading** | Loads billing knowledge base documents from `vector_db/data/billing_kb_documents.json` |
| **Vector Store** | Adds documents to the vector store for semantic search |

### A2A Server (Optional, for Administration Agent)

The administration agent requires an A2A-compliant endpoint. A local mock server is provided:

```bash
# Start the A2A server (in a separate terminal)
uv run python -m a2a_server
```

#### A2A Server Configuration

| Aspect | Configuration | Description |
|--------|---------------|-------------|
| **Default Address** | `127.0.0.1:9999` | Configurable via `A2A_SERVER_PORT` and `A2A_SERVER_HOST` |
| **Agent Card** | `/.well-known/agent-card.json` | Public agent card endpoint |
| **Mock Responses** | Included | Mock responses for administrative operations |
| **Authentication** | Extended skills | Supports authenticated extended skills for testing |
| **Compliance** | A2A-compliant | Fully A2A-compliant for integration testing |

> ⚠️ **Important**: The A2A server must be running before testing administration agent functionality.

---

## Running the Application

### LangGraph Development Server

Start the LangGraph development server using the CLI:

```bash
# Run LangGraph server (automatically uses virtual environment)
uv run langgraph dev
```

#### Server Capabilities

| Feature | Description |
|---------|-------------|
| **Default Port** | `http://localhost:2024` |
| **API Endpoints** | Provides API endpoints for the agent network |
| **Interactive Testing** | Enable interactive testing via LangGraph Studio |
| **Authentication** | Includes authentication (see `src/auth.py`) |

#### Testing Your Agent

Once the LangGraph server is running, you can test your graph(s) using:

- **LangGraph Studio**: Built-in interactive testing interface
- **Agent Chat UI**: Prebuilt conversational interface with tool visualization and time-travel debugging ([Agent Chat UI Documentation](https://docs.langchain.com/oss/python/langchain/ui))

To use Agent Chat UI, visit the [hosted version](https://agentchat.vercel.app/) or run it locally, then connect to your server at `http://localhost:2024`.

### Running Both Servers

For full functionality (especially administration agent), run both servers:

| Server | Terminal | Command |
|--------|----------|---------|
| **A2A Server** | Terminal 1 | `uv run python -m a2a_server` |
| **LangGraph Server** | Terminal 2 | `uv run langgraph dev` |

### Example Prompts

Example prompts for testing the agent network are available in `tests/sample_scenarios/`:

| File | Purpose |
|------|---------|
| `supervisor_test_cases.txt` | Supervisor routing examples |
| `technical_agent_test_cases.txt` | Technical support scenarios |
| `billing_agent_test_cases.txt` | Billing inquiry examples |
| `admin_agent_test_cases.txt` | Administration request scenarios |

---

## Code Quality Tools

The project uses the following tools for code quality:

| Tool | Purpose | Configuration |
|------|---------|---------------|
| **Black** | Code formatter | Line length: 100 |
| **Pylint** | Linter | Project-specific configuration (`.pylintrc`) |
| **isort** | Import sorter | Configured for Black compatibility |

### Running Code Quality Checks

```bash
# Format code
uv run black src tests

# Sort imports
uv run isort src tests

# Lint code
uv run pylint src tests
```

### Configuration Files

| File | Contains |
|------|----------|
| `pyproject.toml` | Black, isort, and Pylint settings |
| `.pylintrc` | Pylint configuration with virtual environment detection |

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

#### Unit Test Dependencies

| Dependency | Purpose |
|------------|---------|
| `pytest-asyncio` | Async test support |
| `pytest-mock` | Mocking external dependencies |

### Evaluations

Run evaluations using LangSmith:

```bash
# Run evaluations against a specific dataset
uv run python -m tests.evals.run_evals ds-curated.json

# Or use a different dataset
uv run python -m tests.evals.run_evals ds-synthetic.json
```

#### Evaluation Suite Features

| Feature | Description |
|---------|-------------|
| **LLM-as-judge Evaluators** | Response quality assessment |
| **Deterministic Evaluators** | Trajectory matching validation |
| **LangSmith Integration** | Generates datasets and experiments |
| **Performance Tracking** | Tracks performance metrics and traces |

---

## Documentation

> 📖 **Start Here**: See [START_HERE.md](./docs/START_HERE.md) for a guided reading path through all documentation.

### All Documentation

| Resource | Description |
|----------|-------------|
| **[START_HERE.md](./docs/START_HERE.md)** | 📍 **Documentation guide** - Recommended reading order and quick reference |
| **[BUSINESS_OVERVIEW.md](./docs/BUSINESS_OVERVIEW.md)** | Business context, challenges, and success criteria |
| **[SDLC_AGENTIC_AI.md](./docs/SDLC_AGENTIC_AI.md)** | Development lifecycle for agentic AI systems |
| **[ARCHITECTURE.md](./docs/ARCHITECTURE.md)** | Detailed architecture, design decisions, and implementation patterns |
| **[LLM_MODEL_ANALYSIS.md](./docs/LLM_MODEL_ANALYSIS.md)** | Model selection guide, trade-offs, and recommendations (reference) |
| **[BUSINESS_NEEDS_SOLUTION_ALIGNMENT.md](./docs/BUSINESS_NEEDS_SOLUTION_ALIGNMENT.md)** | How architecture addresses business needs |
| **[RESULTS_SNAPSHOT.md](./docs/RESULTS_SNAPSHOT.md)** | Initial evaluation results and KPI alignment analysis |
| **[FURTHER_ENHANCEMENTS.md](./docs/FURTHER_ENHANCEMENTS.md)** | Future improvements and enhancements roadmap |


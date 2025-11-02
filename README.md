# Customer Support Agent Network

A multi-agent system built with LangChain and LangGraph that automates customer support ticket handling with human-in-the-loop capabilities.

## Features

- **Multi-Agent Architecture**: Specialized agents for technical support, billing, and administration
- **Smart Orchestration**: Intelligent routing and task distribution between agents
- **Human-in-the-Loop**: Automatic escalation for low confidence, high-risk, or high-impact decisions
- **Custom Authentication**: JWT-based authentication system
- **Stateful Conversations**: Maintains context across multiple agents and interactions

## Architecture

### Agents

1. **Orchestrator Agent**: Routes tickets to appropriate specialized agents
2. **Technical Support Agent**: Handles technical issues and troubleshooting
3. **Billing Agent**: Manages billing inquiries, refunds, and payment issues
4. **Administration Agent**: Handles account management and administrative tasks
5. **Human Supervisor**: Intervenes when human oversight is required

### Human-in-the-Loop Triggers

The system automatically pauses for human review when:
- Agent confidence is below threshold (configurable)
- Issue involves compliance or policy risks
- Decision has high business impact
- User explicitly requests human assistance

## Installation

### Using uv (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package manager. Install it first:

```bash
# Install uv (macOS/Linux)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or using pip
pip install uv
```

Then set up the project:

```bash
# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies (requires Python 3.11+)
uv pip install -e .

# Install dev dependencies (optional)
uv pip install -e ".[dev,test]"

# Copy environment variables
cp .env.example .env

# Edit .env with your API keys
```

### Using pip (Legacy)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (requires Python 3.11+)
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env

# Edit .env with your API keys
```

### Requirements

- Python 3.11 or higher
- LangGraph 1.0+
- LangChain 1.0+

## Usage

### Running the LangGraph Server

**Important:** The LangGraph server must use the Python interpreter from your virtual environment where dependencies are installed.

**Option 1: Using `uv run` (Recommended - always works):**

```bash
# Ensure project is installed in editable mode
uv pip install -e .

# Run LangGraph server using uv (automatically uses .venv Python)
uv run langgraph dev
```

**Option 2: With venv activated (ensure venv is activated first):**

```bash
# IMPORTANT: Activate virtual environment FIRST
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Verify you're using the venv langgraph
which langgraph  # Should show: .../.venv/bin/langgraph

# Install project dependencies (if not already installed)
uv pip install -e .  # or: pip install -e .

# Run LangGraph development server
langgraph dev
```

**Option 3: Use venv langgraph directly (no activation needed):**

```bash
# Run directly from venv (bypasses PATH issues)
.venv/bin/langgraph dev
```

**Troubleshooting:**

If you see `ModuleNotFoundError: No module named 'a2a'`, it means the LangGraph server is using the wrong Python interpreter:

1. **Verify which langgraph is being used:**
   ```bash
   which langgraph
   # Should show: .../.venv/bin/langgraph
   # If it shows: /usr/local/bin/langgraph, activate venv or use Option 1/3
   ```

2. **Check `langgraph.json`:** Ensure `python_version` matches your venv Python version (e.g., "3.13")

3. **Verify installation:**
   ```bash
   .venv/bin/python -c "import a2a; print('OK')"
   uv pip list | grep a2a-sdk
   ```

4. **Reinstall if needed:**
   ```bash
   uv pip install -e .
   uv pip install langgraph-cli  # Ensure CLI is in venv
   ```

### Running the A2A Administration Server (Optional)

The A2A (Agent-to-Agent) server provides a mock administration agent that can be used for testing administration tools. This server is required if you're testing administration agent functionality.

**Start the A2A server:**

```bash
# Option 1: Using uv run (recommended)
uv run python -m a2a_server

# Option 2: Using venv Python directly
.venv/bin/python -m a2a_server

# Option 3: With venv activated
source .venv/bin/activate
python -m a2a_server
```

**Configuration:**

The server runs on `127.0.0.1:9999` by default. You can customize the host and port using environment variables:

```bash
# Custom port
A2A_SERVER_PORT=8080 uv run python -m a2a_server

# Custom host and port
A2A_SERVER_HOST=0.0.0.0 A2A_SERVER_PORT=8080 uv run python -m a2a_server
```

**Verify the server is running:**

Once started, you should see:
```
INFO - Starting A2A Administration Agent Server on 127.0.0.1:9999
INFO - Public agent card URL: http://127.0.0.1:9999/
```

You can access the agent card at `http://127.0.0.1:9999/` in your browser or via API calls.

**Important:** The A2A server **MUST be running** before using administration agent functionality in the LangGraph network. If you see errors like:

```
RuntimeError: Failed to fetch the public agent card. Cannot continue.
```

This means the A2A server is not running or not accessible. To fix:
1. Start the A2A server in a separate terminal: `uv run python -m a2a_server`
2. Verify it's accessible: `curl http://127.0.0.1:9999/.well-known/agent-card.json`
3. Make sure the port matches (default is 9999) or set `A2A_SERVER_PORT` environment variable

**Run both servers:**
```bash
# Terminal 1: Start A2A server
uv run python -m a2a_server

# Terminal 2: Start LangGraph server
uv run langgraph dev
```

### Running Examples

```bash
# Run the example
python examples/basic_usage.py
```

## Project Structure

```
.
├── src/
│   ├── __init__.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── orchestrator.py
│   │   ├── technical_support.py
│   │   ├── billing.py
│   │   ├── administration.py
│   │   └── human_supervisor.py
│   ├── orchestration/
│   │   ├── __init__.py
│   │   ├── graph.py
│   │   └── state.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── knowledge_base.py
│   │   ├── ticket_tools.py
│   │   └── compliance_check.py
│   └── utils/
│       ├── __init__.py
│       ├── confidence.py
│       └── risk_assessment.py
├── requirements.txt
└── README.md
```

## Configuration

Configure human-in-the-loop thresholds in `.env`:
- `HITL_THRESHOLD_LOW_CONFIDENCE`: Confidence level below which human review is triggered
- `HITL_THRESHOLD_HIGH_IMPACT`: Business impact threshold requiring human approval

## License

MIT


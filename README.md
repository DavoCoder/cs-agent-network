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

Make sure to activate your virtual environment first:

```bash
# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install project dependencies (if not already installed)
uv pip install -e .  # or: pip install -e .

# Run LangGraph development server
langgraph dev

# Or use uv to run (ensures venv is used)
uv run langgraph dev
```

**Important:** Always activate the virtual environment before running `langgraph` to ensure it uses the correct Python with all dependencies installed.

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


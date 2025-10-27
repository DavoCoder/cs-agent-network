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

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (requires Python 3.8+)
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env

# Edit .env with your API keys
```

### Requirements

- Python 3.8 or higher
- LangGraph 1.0+
- LangChain 0.3+

## Usage

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


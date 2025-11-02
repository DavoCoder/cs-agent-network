# Architecture

## Goal & Purpose

This agent network is a **multi-agent customer support system** designed to intelligently route and handle customer service tickets across specialized domains. The system provides a **solid foundation and proven patterns** for building complex, multi-step agent workflows that require:

- **Intelligent routing** to domain-specific specialists
- **Structured coordination** between multiple specialized agents
- **Human-in-the-loop** oversight for sensitive operations
- **Tool integration** with external systems (documentation, knowledge bases, administrative APIs)
- **Quality assessment** and confidence scoring for responses

The system demonstrates how to build **flexible, maintainable agent networks** using LangGraph with explicit graph construction for maximum control and customization.

---

## Design Choices

### Dispatcher → Specialized Agents Model

The system follows a **central dispatcher pattern** where a **Supervisor** node classifies incoming tickets and routes them to specialized agent nodes:

- **Technical Support Agent**: Handles developer questions using MCP (Model Context Protocol) tools for documentation access
- **Billing Agent**: Answers billing questions using vector store knowledge base search
- **Administration Agent**: Manages administrative requests via A2A (Agent-to-Agent) protocol with mandatory human review

This design provides several benefits:
- **Domain specialization**: Each agent is optimized for its specific task domain
- **Separation of concerns**: Clear boundaries between routing, execution, and assessment
- **Scalability**: New specialized agents can be added without modifying existing ones
- **Quality control**: Centralized assessment and human review at appropriate points

### Low-Level Explicit Graph Building

Unlike prebuilt LangChain ReAct agents or high-level abstractions, this system **explicitly constructs the graph** using LangGraph's StateGraph API. This approach provides:

- **Fine-grained control**: Precise control over node execution, edge conditions, and state transitions
- **Custom patterns**: Ability to implement specialized patterns (ReAct loops, classifier chains, human-in-the-loop interrupts)
- **Flexibility**: Easy modification of graph structure, routing logic, and tool integration
- **Transparency**: Clear visibility into execution flow for debugging and optimization

The graph is built node-by-node with explicit edges and conditional routing, allowing for complex multi-agent workflows that wouldn't be easily achievable with standard agent templates.

### Node Types & Patterns

Different nodes in the system serve distinct architectural roles:

**Classifier/Router Nodes**:
- **Supervisor**: Classifies tickets into categories using structured LLM output (Pydantic schemas)
- **Assessment**: Evaluates response quality, confidence, and risk using structured output schemas

**ReAct Agent Nodes**:
- **Technical Support**: Implements ReAct loop (Reasoning → Action → Observation) with MCP tool integration
- **Billing**: Implements ReAct loop with vector store knowledge base search
- **Administration**: Implements ReAct loop with A2A agent delegation

**Control Flow Nodes**:
- **Human Review**: Implements interrupt pattern for human-in-the-loop approval
- **Process Feedback**: Handles resumption after human feedback

**Tool Execution Nodes**:
- Tool nodes execute tool calls and return results to their respective agent nodes
- Separate tool nodes per agent domain for isolation and clarity

---

## Architecture Components

### Graph Structure

The graph follows this execution flow:

```
START → Supervisor (classification)
    ├─→ Technical → Technical Tools → Technical (ReAct loop)
    ├─→ Billing → Billing Tools → Billing (ReAct loop)
    └─→ Administration → Admin Tools → Administration → Human Review → Process Feedback → Administration
                                                    ↓
                                            Assessment → END
```

**Key Characteristics**:
- **Single entry point**: All requests start at Supervisor
- **Parallel agent branches**: Three specialized agent paths
- **ReAct loops**: Technical and Billing agents can iterate with tools
- **Human-in-the-loop**: Administration path includes mandatory interrupt for review
- **Quality gate**: Assessment node evaluates all paths before completion

### State Management: ConversationState

The system uses a shared **ConversationState** that extends LangGraph's `MessagesState`:

**Core Components**:
- **Messages**: Conversation history (built-in from MessagesState)
- **Agent Contexts**: Per-agent execution metadata (confidence, reasoning, risk levels)
- **Routing History**: Track of node execution path for debugging and evaluation
- **Human-in-the-loop State**: Flags and feedback for human review workflow
- **Quality Metrics**: Overall confidence, risk assessment, tool call tracking

**State Reducers**:
- **Agent Contexts**: Append-only list tracking each agent's execution context
- **Routing History**: Append-only list of nodes visited during execution

This shared state enables:
- **Context preservation** across agent transitions
- **Quality tracking** throughout the conversation
- **Audit trail** for debugging and evaluation
- **Human review** workflow state management

### Structured Output Schemas

The system uses **Pydantic models** for structured LLM outputs:

- **TicketClassification**: Supervisor's routing decision (category, priority, intent, confidence)
- **Assessment**: Quality evaluation (confidence score, risk level, compliance risks, human review flag)

Benefits:
- **Type safety**: Compile-time validation of LLM outputs
- **Consistency**: Guaranteed output format across executions
- **Integration**: Easy integration with downstream systems and databases

### Configuration System: RunnableConfig with Configuration Schema

The graph uses LangGraph's **RunnableConfig** pattern with a custom **Configuration** Pydantic schema that allows **runtime parameter overrides**:

**Configurable Parameters**:
- **Per-node model selection**: Different LLM models per agent (e.g., GPT-4o-mini, GPT-5, Claude Sonnet)
- **Temperature settings**: Customizable creativity/determinism per node
- **System prompts**: Overridable prompts for each agent
- **Tool call limits**: Configurable iteration limits per agent
- **Human review messages**: Customizable confirmation prompts

**Runtime Override Mechanism**:
- Configuration is passed via `RunnableConfig` with `context_schema=Configuration`
- LangGraph Assistants API allows runtime overrides through configuration payload
- Each node accesses configuration via `runtime.context` from its `RunnableConfig` parameter
- Default values are provided for all parameters, with overrides applied at runtime

This design enables:
- **A/B testing** of models and prompts
- **Multi-tenant customization** (different configurations per customer)
- **Gradual rollout** of new models/prompts
- **Fine-tuning** of individual agent behavior

### Integrations

**MCP (Model Context Protocol)**:
- Technical Support agent uses MCP tools to access documentation servers
- Provides dynamic tool discovery and execution
- Enables integration with external documentation systems without hardcoding

**A2A (Agent-to-Agent Protocol)**:
- Administration agent delegates to external A2A-compliant administrative agents
- Demonstrates agent-to-agent communication patterns
- API key authentication propagated from runtime configuration

**Vector Store (Pinecone)**:
- Billing agent searches knowledge base using semantic vector search
- Uses OpenAI embeddings for query encoding
- Enables scalable, accurate retrieval of billing information

**LangSmith Integration**:
- Traces all LLM calls, tool invocations, and graph execution
- Enables debugging, performance monitoring, and cost tracking
- Used for evaluation dataset management and experiment tracking

### Authentication & Security

**Custom Authentication Mechanism**:
- Implements LangGraph SDK's `Auth` interface for request authentication
- Validates LangSmith API keys from request headers
- Extracts user identity and retrieves user-specific A2A admin agent keys
- Demonstrates **auth data propagation** through the graph execution

**Auth Data Propagation**:
- Authentication context is stored in `RunnableConfig` (`configurable` field)
- Tools access auth data via runtime configuration injection
- Administration tools use API key from config for A2A endpoint authentication
- Custom wrapper (`admin_tools_with_config`) sets runtime config before tool execution

This pattern shows how to:
- Securely pass authentication tokens through agent workflows
- Access user-specific credentials within tool executions
- Implement multi-tenant authentication for agent networks

### Memory Management: Short-Term Memory with History Cropping

The system implements **short-term memory management** to balance context preservation with token efficiency:

**Conversation History Formatting**:
- Supervisor node includes up to 10 previous messages for classification context
- History excludes tool messages (internal implementation details)
- Long messages are truncated to 300 characters to prevent token bloat
- Format preserves user/assistant dialogue for better context understanding

**Rationale**:
- **Token efficiency**: Prevents context window overflow in long conversations
- **Relevance**: Recent messages are more important for classification and responses
- **Clarity**: Tool messages are excluded from user-facing context to reduce noise
- **Performance**: Truncation prevents slow processing of very long messages

This approach demonstrates:
- Practical memory management in production agent systems
- Balancing context richness with cost and performance
- Selective history inclusion based on node needs

### Prompt Management: LangSmith Prompt Hub with Local Fallback

The system loads prompts from **LangSmith Prompt Hub** with automatic fallback to local text files:

**Loading Strategy**:
- Environment variable `PULL_PROMPTS_FROM_LANGSMITH` controls source preference
- Primary: Pull from LangSmith Prompt Hub (for production, A/B testing)
- Fallback: Load from local `.txt` files in `src/prompts/` directory
- Caching: Prompts are cached after first load to avoid repeated API calls

**Benefits**:
- **Centralized management**: Prompts can be updated in LangSmith without code changes
- **Version control**: LangSmith tracks prompt versions and changes
- **Offline capability**: Local fallback ensures system works without LangSmith connectivity
- **Development workflow**: Developers can edit local files for testing

**Prompt Organization**:
- System prompts for each agent node
- Human prompts for assessment and human review
- Grader prompts for LLM-as-judge evaluators
- All prompts are externalized, not hardcoded in Python

### Model Selection & LLM Configuration

The system supports multiple LLM providers and models per node:

**Current Models**:
- Default: GPT-4o-mini (cost-effective, good for most tasks)
- Options: GPT-4o, GPT-5, Claude Sonnet 4.5, Claude Haiku 4.5, o1/o1-mini

**Model Selection Strategy**:
Each node can be configured with different models based on:
- **Task complexity**: Simple classification vs. complex reasoning
- **Tool usage requirements**: Some models (o1) don't support tools
- **Cost constraints**: High-volume nodes use cheaper models
- **Quality requirements**: Security-critical nodes use premium models

**Comprehensive Analysis**:
See [LLM_MODEL_ANALYSIS.md](./LLM_MODEL_ANALYSIS.md) for:
- Detailed model capabilities comparison
- Node-by-node recommendations
- Cost-efficiency trade-offs
- Provider strategy (OpenAI vs. Anthropic)
- Hardening roadmap and implementation priorities

**Key Insights**:
- **Selective upgrades**: Not all nodes benefit from premium models
- **Administration is critical**: Security-sensitive operations warrant premium models (Claude Sonnet 4.5 or GPT-5)
- **Technical benefits from Claude**: Claude Sonnet 4.5 excels at coding/technical tasks
- **Hybrid strategy**: Using both OpenAI and Anthropic optimizes for task-specific strengths

---

## Evaluation System

### Evaluation Architecture

The system includes a comprehensive evaluation suite that generates datasets and experiments in LangSmith:

**Evaluation Types**:

1. **LLM-as-Judge Evaluators**:
   - **Final Response Correctness**: Uses LLM to compare actual vs. expected responses
   - **HITL Preparation Quality**: Evaluates how well human-in-the-loop outputs prepare humans for decisions
   - **Grader Models**: Configured with structured output (Pydantic schemas) for consistent scoring

2. **Deterministic Evaluators**:
   - **Trajectory Match**: Exact node sequence matching
   - **Trajectory Subsequence**: Partial sequence matching for flexible evaluation
   - **Supervisor Classification**: Exact category match validation

**Evaluation Workflow**:
- Datasets are defined in JSON files with inputs, expected outputs, and reference trajectories
- Evaluators run against datasets to generate experiment results in LangSmith
- Results include scores, traces, and metadata for analysis
- Experiments track performance over time and across model/prompt changes

**Dataset Management**:
- Datasets stored in LangSmith for version control and collaboration
- Multiple datasets supported (curated, synthetic, development)
- Command-line interface for running evaluations against different datasets
- Results automatically uploaded to LangSmith for visualization

**Integration with LangSmith**:
- All evaluations create LangSmith experiments with traces
- Traces include full graph execution paths for debugging
- Score aggregation and comparison across experiments
- Enables systematic testing of model upgrades, prompt changes, and architecture modifications

**Evaluation Patterns Demonstrated**:
- **Hybrid evaluation**: Combining LLM judges with deterministic checks
- **Trajectory evaluation**: Validating execution paths, not just outputs
- **Domain-specific evaluation**: HITL quality evaluation only for administration cases
- **Cost-aware evaluation**: Different evaluators for CI/CD vs. production validation

This evaluation system demonstrates:
- How to systematically test multi-agent workflows
- Best practices for LLM evaluation (judges, structured outputs, context-aware scoring)
- Integration with LangSmith for experiment management
- Continuous improvement workflow for agent networks

---

## Summary

This architecture provides a **solid foundation** for building complex, multi-agent systems with:

- **Flexible routing** through specialized agents
- **Explicit control** over execution flow
- **Structured coordination** via shared state and schemas
- **Runtime configurability** for models, prompts, and behavior
- **Comprehensive evaluation** for continuous improvement

The system demonstrates how to balance **flexibility and control** with **practical constraints** (cost, performance, token limits) in real-world agent deployment scenarios.


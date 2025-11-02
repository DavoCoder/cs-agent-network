# Evaluation Suite for Customer Support Agent Network

This directory contains evaluation tests for the customer support agent network, based on the [LangSmith evaluation guide for complex agents](https://docs.langchain.com/langsmith/evaluate-complex-agent#evaluations).

## Structure

- **`examples.py`**: Contains 10 test examples with inputs and expected outputs (trajectories, classifications, responses)
- **`evaluators.py`**: Contains evaluator functions including:
  - LLM-as-judge evaluator for final response correctness
  - Deterministic trajectory matching evaluator
  - Trajectory subsequence evaluator (partial match scoring)
  - Supervisor classification accuracy evaluator
- **`run_evals.py`**: Main script to run all evaluations using LangSmith Client

## Evaluation Types

### 1. Final Response Correctness (LLM-as-judge)
Uses GPT-4o-mini as a judge to evaluate if the agent's final response is factually correct and helpful compared to the expected response.

### 2. Trajectory Matching (Exact)
Deterministically checks if the agent took the exact expected path through graph nodes.

### 3. Trajectory Subsequence
Checks how many of the expected steps the agent took, returning a score between 0.0 and 1.0.

### 4. Supervisor Classification
Deterministically checks if the supervisor correctly classified the ticket into the right category (technical, billing, administration, or unclassifiable).

## Running Evaluations

### Prerequisites

1. Set environment variables:
```bash
export LANGSMITH_API_KEY="your-api-key"
export OPENAI_API_KEY="your-openai-key"
```

2. Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### Run All Evaluations

```bash
python -m tests.evals.run_evals
```

This will:
1. Create a dataset in LangSmith (if it doesn't exist)
2. Run all 4 evaluation types
3. Display results in pandas DataFrames

### View Results in LangSmith

After running, you can view detailed results in the LangSmith UI:
- Navigate to your LangSmith project
- Look for experiments prefixed with:
  - `customer-support-final-response`
  - `customer-support-trajectory-exact`
  - `customer-support-trajectory-subsequence`
  - `customer-support-classification`

## Test Examples

The suite includes 10 examples covering different scenarios:

1. **Technical Query**: API authentication question → routes to technical agent
2. **Billing Query**: Pricing question → routes to billing agent
3. **Administration Query**: Account creation → routes to admin agent (with human review flow)
4. **Technical Error**: API error troubleshooting → routes to technical agent
5. **Billing Refund**: Refund request → routes to billing agent
6. **Administration Team**: Team member addition → routes to admin agent (with human review)
7. **Technical Setup**: Webhook setup → routes to technical agent
8. **Billing Plans**: Plan comparison → routes to billing agent
9. **Administration Profile**: Email update → routes to admin agent (with human review)
10. **Unclassifiable**: Gratitude message → routes to unclassifiable handler

## Adding New Examples

To add new test examples, edit `examples.json`:

```json
{
  "inputs": {
    "messages": [
      {
        "role": "user",
        "content": "Your test question"
      }
    ]
  },
  "outputs": {
    "trajectory": ["supervisor", "agent_name", "tools", "agent_name", "assessment"],
    "supervisor_classification": "agent_category",
    "response": "Expected response description with domain-specific details"
  }
}
```

The JSON format allows for better readability and easier version control.

## Customizing Evaluators

You can modify evaluators in `evaluators.py`:

- **`GRADER_INSTRUCTIONS`**: Modify LLM-as-judge grading criteria
- **`trajectory_match`**: Change exact matching logic
- **`trajectory_subsequence`**: Adjust partial matching algorithm
- **`supervisor_classification_correct`**: Modify classification validation

## References

- [LangSmith Evaluation Documentation](https://docs.langchain.com/langsmith/evaluate-complex-agent#evaluations)
- [LangGraph Streaming Documentation](https://langchain-ai.github.io/langgraph/how-tos/streaming-subgraphs/)


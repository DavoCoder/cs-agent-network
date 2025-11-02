"""
Run evaluations for the customer support agent network.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain.messages import AIMessage, ToolMessage
from langsmith import Client

from src.graph import create_agent_network
from tests.evals.evaluators import (
    final_response_correct,
    supervisor_classification_correct,
    trajectory_match,
    trajectory_subsequence,
)

logger = logging.getLogger(__name__)

# Load environment variables from .env file
# Look for .env file in the project root
project_root = Path(__file__).parent.parent.parent
env_file = project_root / ".env"
if env_file.exists():
    load_dotenv(env_file, override=True)
    print(f"✅ Loaded environment variables from {env_file}")
else:
    # Try to load from current directory as fallback
    load_dotenv(override=True)


langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
if not langsmith_api_key:
    raise ValueError(
        "LANGSMITH_API_KEY environment variable is required. "
        "Set it in your .env file or environment."
    )

client = Client()

# Dataset name
DATASET_NAME = "ds-cs-agent-network-e2e"


async def extract_final_response(state: dict) -> str:
    """Extract the final response from the state."""
    messages = state.get("messages", [])
    if not messages:
        print("No messages found in the state")
        return ""

    for msg in reversed(messages):
        # Skip tool messages
        if isinstance(msg, ToolMessage) or (isinstance(msg, dict) and msg.get("type") == "tool"):
            print("Skipping tool message")
            continue

        # Extract AI message content
        if isinstance(msg, AIMessage):
            if msg.content:
                print("Found final response in AIMessage format")
                return str(msg.content)
        if isinstance(msg, dict):
            if msg.get("type") == "ai" and msg.get("content"):
                print("Found final response in dict format messages")
                return str(msg["content"])
            if msg.get("content") and msg.get("type") != "tool":
                print("Found final response in content of messages")
                return str(msg["content"])

    return ""


async def extract_trajectory(_state: dict, trajectory: list) -> list:
    """Extract trajectory from state."""
    return trajectory


async def extract_supervisor_classification(state: dict) -> str:
    """Extract supervisor classification from state."""
    # pylint: disable=too-many-return-statements,too-many-branches
    # Primary source: current_ticket.category from State
    current_ticket = state.get("current_ticket", {})
    if isinstance(current_ticket, dict):
        print(f"Supervisor classification will search in CURRENT_TICKET: {current_ticket}")
        category = current_ticket.get("category", "")
        if category:
            print(f"Supervisor classification found in CATEGORY: {category}")
            return category

    # Secondary source: routing_history
    routing_history = state.get("routing_history", [])
    if routing_history:
        # Extract classification from first routing history entry
        first_entry = routing_history[0]
        if isinstance(first_entry, str):
            print(f"Supervisor classification will search in ROUTING_HISTORY: {first_entry}")
            if "classified as" in first_entry:
                if "technical" in first_entry:
                    return "technical"
                if "billing" in first_entry:
                    return "billing"
                if "administration" in first_entry:
                    return "administration"
                if "unclassifiable" in first_entry:
                    return "unclassifiable"

    # Tertiary source: agent_contexts (supervisor context)
    agent_contexts = state.get("agent_contexts", [])
    if agent_contexts:
        # Look for supervisor context
        for context in agent_contexts:
            if isinstance(context, dict):
                agent_name = context.get("agent_name", "")
                print(f"Supervisor classification will search in AGENT_CONTEXTS: {agent_name}")
                if agent_name == "supervisor":
                    # Try to infer from reasoning
                    reasoning = context.get("reasoning", "")
                    if "technical" in reasoning.lower():
                        return "technical"
                    if "billing" in reasoning.lower():
                        return "billing"
                    if "administration" in reasoning.lower():
                        return "administration"

    return ""


async def run_graph(inputs: dict, graph, config: dict = None) -> dict:
    """Run graph and extract trajectory, response, and classification.

    For evaluation purposes, trajectories that hit human_review stop there.
    We don't simulate the continuation after interrupt.
    """
    trajectory = []

    # Build initial state
    state_input = {"messages": inputs.get("messages", [])}

    # Valid node names to track
    valid_nodes = {
        "supervisor",
        "technical",
        "billing",
        "administration",
        "technical_tools",
        "billing_tools",
        "admin_tools",
        "assessment",
        "human_review",
        "process_feedback",
    }

    # Track trajectory using astream in debug mode
    try:
        async for namespace, chunk in graph.astream(
            state_input,
            config=config or {},
            stream_mode="debug",
        ):
            # In debug mode, namespace is the node name or state key
            node_name = None

            # First, check if namespace itself is a valid node
            if namespace in valid_nodes:
                node_name = namespace
            # Otherwise, try to extract from chunk
            elif isinstance(chunk, dict):
                # Check various possible formats in chunk
                if "task" in chunk:
                    task_info = chunk.get("task", {})
                    node_name = task_info.get("name") or task_info.get("payload", {}).get("name")
                elif "node" in chunk:
                    node_name = chunk.get("node")
                elif "name" in chunk:
                    node_name = chunk.get("name")
                # Check if chunk keys include a valid node name
                elif any(key in valid_nodes for key in chunk.keys()):
                    for key in chunk.keys():
                        if key in valid_nodes:
                            node_name = key
                            break

            # Track valid nodes (allow duplicates for cycles like technical -> tools -> technical)
            if node_name and node_name in valid_nodes:
                trajectory.append(node_name)

    except Exception:
        # Fallback: try astream_events if astream fails
        try:
            async for event in graph.astream_events(
                state_input,
                config=config or {},
                version="v2",
            ):
                if event.get("event") == "on_chain_start":
                    name = event.get("name")
                    if name and name in valid_nodes:
                        trajectory.append(name)
        except Exception:
            pass

    # Get final state
    try:
        final_state = await graph.ainvoke(state_input, config=config or {})
    except Exception:
        logger.warning("Graph invocation failed - using state_input as fallback")
        final_state = state_input

    # Extract results
    response = await extract_final_response(final_state)
    actual_trajectory = await extract_trajectory(final_state, trajectory)
    classification = await extract_supervisor_classification(final_state)

    # Include state in outputs for evaluators to access State fields
    return {
        "response": response,
        "trajectory": actual_trajectory,
        "supervisor_classification": classification,
        "state": final_state,
    }


async def setup_dataset(examples_filename: str):
    """Setup the evaluation dataset."""

    # Load examples from externalized JSON file
    examples_file = Path(__file__).parent / examples_filename
    if not examples_file.exists():
        raise FileNotFoundError(f"Examples file not found: {examples_file}")

    with open(examples_file, "r", encoding="utf-8") as f:
        examples = json.load(f)

    # Derive dataset name from filename (remove .json extension)
    # e.g., "ds-curated.json" -> "ds-cs-agent-network-e2e-ds-curated"
    filename_base = Path(examples_filename).stem

    if not client.has_dataset(dataset_name=filename_base):
        dataset = client.create_dataset(dataset_name=filename_base)
        client.create_examples(dataset_id=dataset.id, examples=examples)
        print(f"✅ Created dataset: {filename_base}")
    else:
        print(f"✅ Dataset already exists: {filename_base}")

    return filename_base


async def run_all_evals(examples_filename: str):
    """Run all evaluations in a single pass.

    Args:
        examples_filename: Name of the JSON file containing examples
    """
    # Setup dataset
    dataset_name = await setup_dataset(examples_filename)
    print(f"📊 Using dataset from file: {examples_filename} -> {dataset_name}")

    # Create graph
    print("Creating agent network graph...")
    graph = await create_agent_network({})

    config = {
        "env": "test",
        "configurable": {
            "langgraph_auth_user": {
                "identity": f"eval_user_{langsmith_api_key[:20]}",  # Truncated for logging
                "is_authenticated": True,
                "a2a_admin_agent_key": os.getenv(
                    "A2A_ADMIN_AGENT_KEY"
                ),  # Optional, for admin tools
            }
        },
    }

    # Target function for evaluation
    async def target_function(inputs: dict) -> dict:
        """Target function that runs the graph."""
        return await run_graph(inputs, graph, config)

    # All evaluators to run in a single pass
    all_evaluators = [
        final_response_correct,
        trajectory_match,
        trajectory_subsequence,
        supervisor_classification_correct,
    ]

    print("\n" + "=" * 80)
    print("Running All Evaluations in Single Pass")
    print("=" * 80)
    print("Evaluators:")
    print("  1. Final Response Correctness (LLM-as-judge)")
    print("  2. Trajectory Matching (Exact Match)")
    print("  3. Trajectory Subsequence (Partial Match)")
    print("  4. Supervisor Classification Accuracy")
    print("  5. Human Review Appropriate (State-based)")
    print("=" * 80)
    print("\n⚠️  This will run the graph once per example and apply all evaluators")
    print("   to the same outputs for efficiency.\n")

    # Run all evaluators in a single pass
    # This executes the graph once per example and applies all evaluators to the same outputs
    results = await client.aevaluate(
        target_function,
        data=dataset_name,
        evaluators=all_evaluators,
        experiment_prefix="customer-support-e2e",
        num_repetitions=1,
        max_concurrency=4,
    )

    print("\n✅ All evaluations complete!")
    print("\n" + "=" * 80)
    print("Evaluation Results Summary")
    print("=" * 80)
    print(results)
    print("\n" + "=" * 80)
    print("\n💡 Tip: View detailed results in LangSmith UI")
    print("   Experiment: customer-support-e2e")
    print("=" * 80)


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Run evaluations for the customer support agent network"
    )
    parser.add_argument(
        "examples_file",
        type=str,
        help=(
            "Name of the JSON file containing evaluation examples "
            "(e.g., ds-curated.json, ds-synthetic.json)"
        ),
    )
    args = parser.parse_args()

    # Note: LANGSMITH_API_KEY is already validated during Client initialization above
    # If it's missing, a ValueError will be raised before reaching this point
    langsmith_key = os.getenv("LANGSMITH_API_KEY")

    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("WARNING: OPENAI_API_KEY environment variable not set. Some evaluators may fail.")

    print(f"\n{'='*80}")
    print("Starting Evaluation Suite")
    print(f"{'='*80}")
    print(f"Examples file: {args.examples_file}")
    masked_key = "*" * (len(langsmith_key) - 4) + langsmith_key[-4:] if langsmith_key else "NOT SET"
    print(f"LangSmith API Key: {masked_key}")
    print(f"OpenAI API Key: {'SET' if openai_key else 'NOT SET'}")
    print(f"{'='*80}\n")

    try:
        asyncio.run(run_all_evals(args.examples_file))
    except ValueError as e:
        # Handle error from Client initialization (missing LANGSMITH_API_KEY)
        print(f"ERROR: {e}")
        print(f"Looking for .env file in: {project_root}")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

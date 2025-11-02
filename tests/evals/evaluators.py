"""
Evaluators for the customer support agent network.
Includes LLM-as-judge, trajectory matching, and supervisor classification evaluators.
"""

from langchain.chat_models import init_chat_model

from src.utils.prompt_loader import pull_externalized_prompt
from tests.evals.graders import Grade, HITLPreparationGrade


def create_grader_llm():
    """Create an LLM configured for grading."""
    return init_chat_model("gpt-4o-mini", temperature=0).with_structured_output(
        Grade, method="json_schema"
    )


async def final_response_correct(inputs: dict, outputs: dict, reference_outputs: dict) -> float:
    """LLM-as-judge evaluator for final response correctness."""
    grader_llm = create_grader_llm()

    # Extract question from inputs
    question = (
        inputs["messages"][0]["content"] if inputs.get("messages") else inputs.get("question", "")
    )

    # Extract actual and expected responses
    ground_truth = reference_outputs.get("response", "")
    agent_network_response = outputs.get("response", "")

    # Extract domain context from state if available
    domain_context = ""
    state = outputs.get("state", {})
    if state:
        current_ticket = state.get("current_ticket", {})
        if isinstance(current_ticket, dict):
            category = current_ticket.get("category", "")
            if category:
                domain_context = f"\nDOMAIN/CATEGORY: {category}"

    # Build evaluation message
    user_message = f"""QUESTION: {question}
GROUND TRUTH RESPONSE: {ground_truth}
AGENT NETWORK RESPONSE: {agent_network_response}{domain_context}"""

    # Load grader instructions (from file or LangSmith)
    grader_instructions = pull_externalized_prompt("grader_system", index=0)

    grade = await grader_llm.ainvoke(
        [
            {"role": "system", "content": grader_instructions},
            {"role": "user", "content": user_message},
        ]
    )
    return grade.score


def trajectory_match(outputs: dict, reference_outputs: dict) -> bool:
    """Deterministic evaluator for trajectory matching."""
    actual_trajectory = outputs.get("trajectory", [])
    expected_trajectory = reference_outputs.get("trajectory", [])

    if len(actual_trajectory) != len(expected_trajectory):
        return False

    return actual_trajectory == expected_trajectory


def trajectory_subsequence(outputs: dict, reference_outputs: dict) -> float:
    """Deterministic evaluator for trajectory subsequence."""
    actual_trajectory = outputs.get("trajectory", [])
    expected_trajectory = reference_outputs.get("trajectory", [])

    if len(expected_trajectory) == 0:
        return 1.0 if len(actual_trajectory) == 0 else 0.0

    if len(expected_trajectory) > len(actual_trajectory):
        return 0.0

    # Check if expected trajectory is a subsequence of actual trajectory
    i = j = 0
    while i < len(expected_trajectory) and j < len(actual_trajectory):
        if expected_trajectory[i] == actual_trajectory[j]:
            i += 1
        j += 1

    return i / len(expected_trajectory)


def supervisor_classification_correct(outputs: dict, reference_outputs: dict) -> bool:
    """Deterministic evaluator for supervisor classification."""
    actual_classification = outputs.get("supervisor_classification", "")
    expected_classification = reference_outputs.get("supervisor_classification", "")

    return actual_classification == expected_classification


def create_hitl_grader_llm():
    """Create an LLM configured for HITL preparation grading."""
    return init_chat_model("gpt-4o-mini", temperature=0).with_structured_output(
        HITLPreparationGrade, method="json_schema"
    )


async def hitl_preparation_quality(
    inputs: dict, outputs: dict, reference_outputs: dict  # pylint: disable=unused-argument
) -> float:
    """
    Evaluate how well the output prepares a human for final action.

    Only evaluates administration cases where human_review was triggered.
    Returns 1.0 (skipped) for non-administration cases or cases without human_review.
    """

    # Filter: Only evaluate administration cases (HITL only happens for administration)
    supervisor_classification = outputs.get("supervisor_classification", "")
    if supervisor_classification != "administration":
        # Not an administration case - skip evaluation
        return 1.0

    # Check if human_review was triggered in the trajectory
    trajectory = outputs.get("trajectory", [])
    if "human_review" not in trajectory:
        # Human review was not triggered - skip evaluation
        return 1.0

    # Extract available information from outputs
    response = outputs.get("response", "")

    # Extract user question from inputs
    question = (
        inputs["messages"][0]["content"] if inputs.get("messages") else inputs.get("question", "")
    )

    # Build context from what's actually available at evaluation time
    context_parts = [
        f"Original Query: {question}",
        f"Trajectory: {' -> '.join(trajectory)}",
    ]
    if response:
        context_parts.append(f"Final Output: {response}")

    context = "\n".join(context_parts) if context_parts else "No context available"

    # Load externalized user message template
    user_message_template = pull_externalized_prompt("hitl_preparation_user", index=0)

    # Format the user message with question and context
    user_message = user_message_template.format(question=question, context=context)

    grader_llm = create_hitl_grader_llm()

    grader_instructions = pull_externalized_prompt("hitl_preparation_system", index=0)

    grade = await grader_llm.ainvoke(
        [
            {"role": "system", "content": grader_instructions},
            {"role": "user", "content": user_message},
        ]
    )
    return grade.score

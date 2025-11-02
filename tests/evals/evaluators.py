"""
Evaluators for the customer support agent network.
Includes LLM-as-judge, trajectory matching, and supervisor classification evaluators.
"""

from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field

from src.utils.prompt_loader import pull_externalized_prompt


# Grader schema for LLM-as-judge
class Grade(BaseModel):
    """Compare the expected and actual answers and grade the actual answer."""

    reasoning: str = Field(
        description="Explain your reasoning for the score, evaluating accuracy, completeness, and appropriateness."
    )
    score: float = Field(
        ge=0.0,
        le=1.0,
        description="Score between 0.0 and 1.0 indicating the level of accuracy and correctness. "
        "0.0 = completely incorrect/unhelpful, 0.5 = partially correct, 1.0 = fully correct and appropriate.",
    )


def create_grader_llm():
    """Create an LLM configured for grading."""
    return init_chat_model("gpt-4o-mini", temperature=0).with_structured_output(
        Grade, method="json_schema"
    )


async def final_response_correct(inputs: dict, outputs: dict, reference_outputs: dict) -> float:
    """LLM-as-judge evaluator for final response correctness. Returns a score between 0.0 and 1.0."""
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

"""
Grader schemas for LLM-as-judge evaluators.
These Pydantic models define the structure for LLM grading outputs.
"""

from pydantic import BaseModel, Field


class Grade(BaseModel):
    """Compare the expected and actual answers and grade the actual answer."""

    reasoning: str = Field(
        description=(
            "Explain your reasoning for the score, "
            "evaluating accuracy, completeness, and appropriateness."
        )
    )
    score: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "Score between 0.0 and 1.0 indicating the level of accuracy and correctness. "
            "0.0 = completely incorrect/unhelpful, "
            "0.5 = partially correct, "
            "1.0 = fully correct and appropriate."
        ),
    )


class HITLPreparationGrade(BaseModel):
    """Evaluate how well the output prepares a human for final action."""

    reasoning: str = Field(
        description=(
            "Explain your reasoning for the score, evaluating: "
            "1. Clarity of what action is needed, "
            "2. Completeness of context provided (original query + tool response), "
            "3. Clearness of instructions for proceeding, "
            "4. Structure and formatting for human review."
        )
    )
    score: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "Score between 0.0 and 1.0 indicating how well the output prepares "
            "the human for final action. "
            "0.0 = insufficient/unclear preparation, "
            "0.5 = partially adequate but missing key information, "
            "1.0 = excellent preparation with all context and clear instructions."
        ),
    )

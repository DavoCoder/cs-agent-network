"""Configuration for the agent network."""
from typing import Literal

from pydantic import BaseModel, Field
from typing_extensions import Annotated

from src.utils.prompt_loader import pull_externalized_prompt

SYSTEM_PROMPT_DESCRIPTION = "The system prompt for the agent. Must be a string"
HUMAN_PROMPT_DESCRIPTION = "The human prompt for the agent. Must be a string"
AI_PROMPT_DESCRIPTION = "The AI prompt for the agent. Must be a string"

MODEL_CHOICES = Literal["openai/gpt-4o-mini", "openai/o1", "openai/o1-mini"]
MODEL_CHOICES_DESCRIPTION = (
    "The model to use for the agent. Must be one of the following: "
    "openai/gpt-4o-mini, openai/o1, openai/o1-mini"
)
MODEL_CHOICES_METADATA = {"__template_metadata__": {"kind": "llm"}}
DEFAULT_MODEL = "openai/gpt-4o-mini"

TEMPERATURE_DESCRIPTION = (
    "The temperature to use for the agent. Must be between 0.0 and 1.0"
)
DEFAULT_TEMPERATURE = 0.1

TOOL_CALL_LIMIT_DESCRIPTION = (
    "The tool call limit for the agent. Must be an integer greater than 0"
)
DEFAULT_TOOL_CALL_LIMIT = 1


class Configuration(BaseModel):
    """Configuration for the agent network."""

    # Supervisor configuration
    supervisor_system_prompt: str = Field(
        default=pull_externalized_prompt("ticket_classifier_system", 0),
        description=SYSTEM_PROMPT_DESCRIPTION,
        json_schema_extra={
            "langgraph_nodes": ["supervisor"],
            "langgraph_type": "prompt"
        }
    )
    supervisor_model: Annotated[MODEL_CHOICES, MODEL_CHOICES_METADATA] = Field(
        default=DEFAULT_MODEL,
        description=MODEL_CHOICES_DESCRIPTION,
        json_schema_extra={"langgraph_nodes": ["supervisor"]}
    )
    supervisor_temperature: float = Field(
        default=0.0,
        description=TEMPERATURE_DESCRIPTION,
        json_schema_extra={"langgraph_nodes": ["supervisor"]}
    )
    unclassifiable_response_ai_prompt: str = Field(
        default=pull_externalized_prompt("unclassifiable_response_ai", 0),
        description=AI_PROMPT_DESCRIPTION,
        json_schema_extra={
            "langgraph_nodes": ["supervisor"],
            "langgraph_type": "prompt"
        }
    )

    # Technical agent configuration
    technical_agent_system_prompt: str = Field(
        default=pull_externalized_prompt("technical_agent_system", 0),
        description=SYSTEM_PROMPT_DESCRIPTION,
        json_schema_extra={
            "langgraph_nodes": ["technical"],
            "langgraph_type": "prompt"
        }
    )
    technical_agent_model: Annotated[MODEL_CHOICES, MODEL_CHOICES_METADATA] = Field(
        default=DEFAULT_MODEL,
        description=MODEL_CHOICES_DESCRIPTION,
        json_schema_extra={"langgraph_nodes": ["technical"]}
    )
    technical_agent_temperature: float = Field(
        default=0.1,
        description=TEMPERATURE_DESCRIPTION,
        json_schema_extra={"langgraph_nodes": ["technical"]}
    )
    technical_tool_call_limit: int = Field(
        default=DEFAULT_TOOL_CALL_LIMIT,
        description=TOOL_CALL_LIMIT_DESCRIPTION,
        json_schema_extra={"langgraph_nodes": ["technical"]}
    )

    # Billing agent configuration
    billing_system_prompt: str = Field(
        default=pull_externalized_prompt("billing_agent_system", 0),
        description=SYSTEM_PROMPT_DESCRIPTION,
        json_schema_extra={
            "langgraph_nodes": ["billing"],
            "langgraph_type": "prompt"
        }
    )
    billing_model: Annotated[MODEL_CHOICES, MODEL_CHOICES_METADATA] = Field(
        default=DEFAULT_MODEL,
        description=MODEL_CHOICES_DESCRIPTION,
        json_schema_extra={"langgraph_nodes": ["billing"]}
    )
    billing_temperature: float = Field(
        default=0.3,
        description=TEMPERATURE_DESCRIPTION,
        json_schema_extra={"langgraph_nodes": ["billing"]}
    )
    billing_tool_call_limit: int = Field(
        default=DEFAULT_TOOL_CALL_LIMIT,
        description=TOOL_CALL_LIMIT_DESCRIPTION,
        json_schema_extra={"langgraph_nodes": ["billing"]}
    )

    # Administration agent configuration
    administration_system_prompt: str = Field(
        default=pull_externalized_prompt("administration_agent_system", 0),
        description=SYSTEM_PROMPT_DESCRIPTION,
        json_schema_extra={
            "langgraph_nodes": ["administration"],
            "langgraph_type": "prompt"
        }
    )
    administration_model: Annotated[MODEL_CHOICES, MODEL_CHOICES_METADATA] = Field(
        default=DEFAULT_MODEL,
        description=MODEL_CHOICES_DESCRIPTION,
        json_schema_extra={"langgraph_nodes": ["administration"]}
    )
    administration_temperature: float = Field(
        default=0.1,
        description=TEMPERATURE_DESCRIPTION,
        json_schema_extra={"langgraph_nodes": ["administration"]}
    )
    administration_tool_call_limit: int = Field(
        default=DEFAULT_TOOL_CALL_LIMIT,
        description=TOOL_CALL_LIMIT_DESCRIPTION,
        json_schema_extra={"langgraph_nodes": ["administration"]}
    )

    # Human supervisor configuration
    admin_confirmation_message: str = Field(
        default=pull_externalized_prompt("admin_confirmation_message", 0),
        description="Template message for admin action confirmation requests",
        json_schema_extra={
            "langgraph_nodes": ["human_review"],
            "langgraph_type": "prompt"
        }
    )
    admin_confirmation_question: str = Field(
        default="Do you want to proceed with this administrative action?",
        description="Question prompt for admin action confirmation",
        json_schema_extra={
            "langgraph_nodes": ["human_review"],
            "langgraph_type": "prompt"
        }
    )

    # Assessment configuration
    assessment_system_prompt: str = Field(
        default=pull_externalized_prompt("assessment_system", 0),
        description=SYSTEM_PROMPT_DESCRIPTION,
        json_schema_extra={
            "langgraph_nodes": ["assessment"],
            "langgraph_type": "prompt"
        }
    )
    assessment_human_prompt: str = Field(
        default=pull_externalized_prompt("assessment_human", 0),
        description=HUMAN_PROMPT_DESCRIPTION,
        json_schema_extra={
            "langgraph_nodes": ["assessment"],
            "langgraph_type": "prompt"
        }
    )
    assessment_model: Annotated[MODEL_CHOICES, MODEL_CHOICES_METADATA] = Field(
        default=DEFAULT_MODEL,
        description=MODEL_CHOICES_DESCRIPTION,
        json_schema_extra={"langgraph_nodes": ["assessment"]}   
    )
    assessment_temperature: float = Field(
        default=0.0,
        description=TEMPERATURE_DESCRIPTION,
        json_schema_extra={"langgraph_nodes": ["assessment"]}
    )

    # Global configuration
    global_tool_call_limit: int = Field(
        default=DEFAULT_TOOL_CALL_LIMIT,
        description=TOOL_CALL_LIMIT_DESCRIPTION,
        json_schema_extra={"langgraph_nodes": ["global"]}
    )

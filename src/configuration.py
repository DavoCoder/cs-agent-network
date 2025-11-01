"""Configuration for the agent network."""
from typing import Literal
from typing_extensions import Annotated

from pydantic import BaseModel, Field


from src.prompts import load_prompt

SYSTEM_PROMPT_DESCRIPTION = "The system prompt for the agent. Must be a string"

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
        default=load_prompt("ticket_classifier_system"),
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

    # Technical agent configuration
    technical_agent_system_prompt: str = Field(
        default=load_prompt("technical_agent_system"),
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
        default=load_prompt("billing_agent_system"),
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
        default=load_prompt("administration_agent_system"),
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

    # Assessment configuration
    assessment_system_prompt: str = Field(
        default=load_prompt("assessment_system"),
        description=SYSTEM_PROMPT_DESCRIPTION,
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

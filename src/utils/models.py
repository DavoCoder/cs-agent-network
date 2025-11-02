"""Utilities for loading chat models."""
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel


def load_chat_model(fully_specified_name: str, temperature: float = 0.0) -> BaseChatModel:
    """Load a chat model from a fully specified name."""
    provider, model = fully_specified_name.split("/", maxsplit=1)
    return init_chat_model(model, model_provider=provider, temperature=temperature)
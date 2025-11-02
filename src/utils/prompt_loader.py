"""Utilities for loading prompts from LangSmith or local files with caching."""

import asyncio
import os
from pathlib import Path

from langsmith import Client

# Cache for prompts to avoid repeated API calls or file reads
_prompt_cache: dict[tuple[str, int], str] = {}


def get_prompt_path(prompt_name: str) -> Path:
    """Get the path to a prompt file."""
    # Get the directory where prompt files are located
    prompts_dir = Path(__file__).parent.parent / "prompts"

    # Return path to the prompt file
    return prompts_dir / f"{prompt_name}.txt"


def load_prompt(prompt_name: str) -> str:
    """Load a prompt from a local file."""
    prompt_path = get_prompt_path(prompt_name)

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    return prompt_path.read_text(encoding="utf-8")


async def aload_prompt(prompt_name: str) -> str:
    """Asynchronously load a prompt from a file using a thread to avoid blocking the event loop."""
    prompt_path = get_prompt_path(prompt_name)
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    # Offload blocking I/O to a thread
    return await asyncio.to_thread(prompt_path.read_text, encoding="utf-8")


def _should_pull_from_langsmith() -> bool:
    """Check if prompts should be pulled from LangSmith based on environment variable."""
    env_value = os.getenv("PULL_PROMPTS_FROM_LANGSMITH", "false")
    return env_value.lower() in ("true", "1", "yes")


def pull_externalized_prompt(prompt_name: str, index: int = 0) -> str:
    """Pull a prompt from LangSmith or local files with caching."""
    # Use tuple as cache key for singleton behavior
    cache_key = (prompt_name, index)

    # Return cached value if available
    if cache_key in _prompt_cache:
        return _prompt_cache[cache_key]

    # Check environment variable to decide source
    if _should_pull_from_langsmith():
        # Load prompt from LangSmith
        try:
            client = Client()
            prompt_template = client.pull_prompt(prompt_name)

            template = prompt_template.messages[index].prompt.template

            # Cache the result
            _prompt_cache[cache_key] = template
            print(f"************ Prompt pulled and cached from LangSmith: {prompt_name}")

            return template
        except Exception as e:
            print(f"Error pulling prompt from LangSmith: {e}, falling back to local prompt")
            # Fall through to local file loading
            template = load_prompt(prompt_name)
            _prompt_cache[cache_key] = template
            return template
    else:
        # Load prompt from local files
        template = load_prompt(prompt_name)
        # Cache the result to avoid repeated file reads
        _prompt_cache[cache_key] = template
        return template

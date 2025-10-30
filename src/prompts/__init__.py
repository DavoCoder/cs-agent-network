import os
import asyncio
from pathlib import Path


def get_prompt_path(prompt_name: str) -> Path:
    """ Get the path to a prompt file. """
    # Get the directory where this module is located
    prompts_dir = Path(__file__).parent
    
    # Return path to the prompt file
    return prompts_dir / f"{prompt_name}.txt"


def load_prompt(prompt_name: str) -> str:
    """ Load a prompt from a file. """
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


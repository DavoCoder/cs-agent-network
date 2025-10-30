import os
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


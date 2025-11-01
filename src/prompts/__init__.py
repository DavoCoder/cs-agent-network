"""Prompts package - compatibility imports for backward compatibility.

All prompt loading functionality has been moved to src.utils.prompt_loader.
This module provides compatibility imports to avoid breaking existing code.
"""
# Re-export functions from prompt_loader for backward compatibility
from src.utils.prompt_loader import (
    load_prompt,
    aload_prompt,
    get_prompt_path,
)

__all__ = ["load_prompt", "aload_prompt", "get_prompt_path"]

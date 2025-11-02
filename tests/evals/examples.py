"""
Eval examples for the customer support agent network.
Loads examples from JSON file for better readability.
"""

import json
from pathlib import Path
from typing import List


def get_examples_path() -> Path:
    """Get the path to the examples JSON file."""
    # Get the directory where this file is located
    evals_dir = Path(__file__).parent
    return evals_dir / "examples.json"


def get_examples() -> List[dict]:
    """Get the examples from the examples JSON file."""
    examples_path = get_examples_path()

    if not examples_path.exists():
        raise FileNotFoundError(
            f"Examples file not found: {examples_path}. "
            "Please create examples.json in the tests/evals directory."
        )

    with open(examples_path, "r", encoding="utf-8") as f:
        examples = json.load(f)

    return examples

"""
Custom authentication handler for LangGraph deployment.
Validates LangSmith API keys and retrieves user-specific A2A admin agent keys.
"""

import logging
import os
from typing import Any, Dict

from dotenv import load_dotenv
from langgraph_sdk import Auth

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Initialize auth
auth = Auth()


def validate_langsmith_api_key(api_key: str) -> bool:
    """Validate a LangSmith API key."""
    if not api_key:
        return False

    if len(api_key) < 20:
        return False

    # Add actual Validation here
    # Example:
    # try:
    #     client = LangSmithClient(api_key=api_key)
    #     client.validate_api_key()
    #     return True
    # except Exception:
    #     return False

    return True


def get_a2a_admin_agent_key(user_identity: str) -> str | None:
    """Retrieve the A2A admin agent key for a given user identity."""

    default_key = os.getenv("A2A_ADMIN_AGENT_KEY")
    if default_key:
        logger.info("Using default A2A_ADMIN_AGENT_KEY from environment")
        return default_key

    logger.warning(
        "No A2A admin agent key found for user %s. "
        "Set A2A_ADMIN_AGENT_KEY in environment or implement user-specific key retrieval.",
        user_identity,
    )
    return None


@auth.authenticate
async def authenticate(headers: dict) -> Auth.types.MinimalUserDict:
    """Authenticate requests using LangSmith API keys."""
    # Extract API key from headers
    # LangSmith typically uses x-api-key header
    api_key = headers.get(b"x-api-key") or headers.get("x-api-key")
    print(f"API key: {api_key}")

    # Also check Authorization header for Bearer token (alternative format)
    if not api_key:
        auth_header = headers.get(b"authorization") or headers.get("authorization")
        if auth_header:
            # Handle both bytes and string
            if isinstance(auth_header, bytes):
                auth_header = auth_header.decode("utf-8")
            if auth_header.startswith("Bearer "):
                api_key = auth_header[7:]  # Remove "Bearer " prefix
            elif auth_header.startswith("ApiKey "):
                api_key = auth_header[7:]  # Remove "ApiKey " prefix

    if not api_key:
        logger.warning("No API key found in request headers")
        raise Auth.exceptions.HTTPException(
            status_code=401,
            detail=(
                "Missing API key. " "Please provide x-api-key header or Authorization Bearer token."
            ),
        )

    # Validate the API key
    if not validate_langsmith_api_key(api_key):
        logger.warning("Invalid API key provided")
        raise Auth.exceptions.HTTPException(status_code=401, detail="Invalid API key")

    # For now, use the API key as the user identity
    user_identity = "Usr_" + api_key[:50]  # Use first 50 chars as identity (temporary)

    # Retrieve user-specific A2A admin agent key
    a2a_key = get_a2a_admin_agent_key(user_identity)

    logger.info("User authenticated: %s", user_identity)

    # Return user information
    user_info: Dict[str, Any] = {
        "identity": user_identity,
        "is_authenticated": True,
    }

    # Add A2A key if available
    if a2a_key:
        user_info["a2a_admin_agent_key"] = a2a_key
        logger.info("A2A admin agent key retrieved for user")
    else:
        logger.warning("No A2A admin agent key available for user")

    return user_info


# Export the auth object for use in langgraph.json
__all__ = ["auth", "authenticate"]

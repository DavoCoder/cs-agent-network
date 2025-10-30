"""
A2A JSON-RPC 2.0 request builder and response handler utilities
Conforms to A2A 0.3.0 (HTTP+JSON JSON-RPC transport).
"""
import uuid
from typing import Any, Dict


def build_a2a_jsonrpc_request(query: str, method: str = "message/send") -> Dict[str, Any]:
    """Build a JSON-RPC 2.0 request body for A2A message/send."""
    request_id = str(uuid.uuid4())
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
        "params": {
            "message": {
                "role": "user",
                "parts": [
                    {"kind": "text", "text": query}
                ],
                "messageId": str(uuid.uuid4()),
            },
            "metadata": {},
        },
    }


def parse_a2a_jsonrpc_response(data: Any) -> str:
    """Parse the A2A JSON-RPC response and return the result."""
    if not isinstance(data, dict):
        return str(data)

    if "error" in data and data["error"] is not None:
        err = data["error"]
        try:
            return f"A2A error {err.get('code')}: {err.get('message')}"
        except Exception:
            return f"A2A error: {err}"

    result = data.get("result")
    if isinstance(result, dict):
        artifacts = result.get("artifacts") or []
        for artifact in artifacts:
            parts = artifact.get("parts") or []
            for part in parts:
                if part.get("kind") == "text" and part.get("text"):
                    return str(part["text"])

        status = result.get("status", {})
        state = status.get("state")
        if state:
            return f"A2A task {result.get('id', '')} state: {state}"
        return str(result)

    return str(data)
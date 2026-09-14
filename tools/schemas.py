"""
JARVIS V4 - Tool Schema Validation & Helpers
Validates incoming arguments against tool input schemas and generates OpenAPI/JSON schemas.
"""

from __future__ import annotations

from typing import Dict, Any, List, Tuple
import logging

logger = logging.getLogger("JARVIS.Tools.Schemas")


def validate_tool_arguments(schema: Dict[str, Any], arguments: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates tool arguments against a lightweight JSON-schema-compatible dictionary.
    Returns (is_valid, list_of_error_messages).
    """
    errors = []
    if not isinstance(arguments, dict):
        return False, ["Arguments must be a key-value dictionary."]

    required = schema.get("required", [])
    for field in required:
        if field not in arguments or arguments[field] is None:
            errors.append(f"Missing required parameter: '{field}'")

    properties = schema.get("properties", {})
    for k, v in arguments.items():
        if k in properties:
            expected_type = properties[k].get("type")
            if expected_type == "string" and not isinstance(v, str):
                errors.append(f"Parameter '{k}' expected string, got {type(v).__name__}")
            elif expected_type == "integer" and not (isinstance(v, int) and not isinstance(v, bool)):
                errors.append(f"Parameter '{k}' expected integer, got {type(v).__name__}")
            elif expected_type == "number" and not isinstance(v, (int, float)):
                errors.append(f"Parameter '{k}' expected number, got {type(v).__name__}")
            elif expected_type == "boolean" and not isinstance(v, bool):
                errors.append(f"Parameter '{k}' expected boolean, got {type(v).__name__}")
            elif expected_type == "array" and not isinstance(v, list):
                errors.append(f"Parameter '{k}' expected array, got {type(v).__name__}")
            elif expected_type == "object" and not isinstance(v, dict):
                errors.append(f"Parameter '{k}' expected object, got {type(v).__name__}")

    return len(errors) == 0, errors


def to_openai_tool_schema(name: str, description: str, input_schema: Dict[str, Any]) -> Dict[str, Any]:
    """Formats a tool into the standard OpenAI function/tool calling format."""
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": input_schema
        }
    }

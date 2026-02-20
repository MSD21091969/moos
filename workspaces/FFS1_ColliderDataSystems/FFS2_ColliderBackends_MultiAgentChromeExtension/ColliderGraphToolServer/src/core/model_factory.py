"""Dynamic Pydantic model factory.

Converts JSON Schema ``params_schema`` dicts from ``ToolDefinition``
into concrete Pydantic models at runtime via ``pydantic.create_model()``.

This is the bridge between user-authored tool descriptions (JSON) and
the typed world of Pydantic Graph Beta steps.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, create_model

# Mapping from JSON Schema ``type`` strings to Python types.
_JSON_TYPE_MAP: dict[str, type] = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "array": list,
    "object": dict,
}


def _python_type_for(schema: dict) -> type:
    """Resolve a JSON Schema fragment to a Python type."""
    json_type = schema.get("type", "string")
    return _JSON_TYPE_MAP.get(json_type, Any)  # type: ignore[arg-type]


def build_args_model(
    tool_name: str,
    params_schema: dict,
) -> type[BaseModel]:
    """Build a dynamic Pydantic model from a JSON Schema ``properties`` dict.

    Parameters
    ----------
    tool_name:
        Used to derive the class name (e.g. ``"search"`` → ``SearchArgs``).
    params_schema:
        A JSON Schema object with at least a ``properties`` key.

    Returns
    -------
    type[BaseModel]
        A dynamically created Pydantic model whose fields match the
        declared properties, suitable for use as a Graph step input.

    Examples
    --------
    >>> schema = {
    ...     "type": "object",
    ...     "properties": {
    ...         "query": {"type": "string"},
    ...         "top_k": {"type": "integer"},
    ...     },
    ...     "required": ["query"],
    ... }
    >>> Model = build_args_model("search", schema)
    >>> m = Model(query="hello", top_k=5)
    >>> m.query
    'hello'
    """
    properties = params_schema.get("properties", {})
    required_fields = set(params_schema.get("required", []))

    field_definitions: dict[str, Any] = {}
    for field_name, field_schema in properties.items():
        py_type = _python_type_for(field_schema)
        default = field_schema.get("default", ...)

        if field_name in required_fields:
            # Required — no default
            field_definitions[field_name] = (py_type, ...)
        elif default is not ...:
            field_definitions[field_name] = (py_type, default)
        else:
            # Optional with no explicit default
            field_definitions[field_name] = (py_type | None, None)  # type: ignore[operator]

    class_name = tool_name.replace("_", " ").title().replace(" ", "") + "Args"
    return create_model(class_name, **field_definitions)

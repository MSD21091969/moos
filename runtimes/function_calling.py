"""Native Ollama function calling tools.

Converts Factory tools to Ollama native tool format.
"""
from typing import Any, Callable
import json


def to_ollama_tool(name: str, func: Callable, description: str = "") -> dict:
    """
    Convert a Python function to Ollama tool format.
    
    Ollama v0.4+ supports native function calling.
    """
    import inspect
    
    # Get function signature
    sig = inspect.signature(func)
    
    # Build parameters
    parameters = {
        "type": "object",
        "properties": {},
        "required": [],
    }
    
    for param_name, param in sig.parameters.items():
        if param_name in ("self", "kwargs"):
            continue
        
        # Infer type
        param_type = "string"
        if param.annotation != inspect.Parameter.empty:
            ann = param.annotation
            if ann == int:
                param_type = "integer"
            elif ann == float:
                param_type = "number"
            elif ann == bool:
                param_type = "boolean"
            elif ann == list:
                param_type = "array"
        
        parameters["properties"][param_name] = {
            "type": param_type,
            "description": f"Parameter: {param_name}",
        }
        
        if param.default == inspect.Parameter.empty:
            parameters["required"].append(param_name)
    
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description or func.__doc__ or f"Function: {name}",
            "parameters": parameters,
        },
    }


def build_tool_registry(tools: dict[str, Callable]) -> list[dict]:
    """
    Build Ollama tools list from a dict of functions.
    
    Args:
        tools: Dict mapping tool name to function
        
    Returns:
        List of Ollama tool definitions
    """
    ollama_tools = []
    for name, func in tools.items():
        ollama_tools.append(to_ollama_tool(name, func))
    return ollama_tools


def parse_tool_call(response: dict) -> tuple[str, dict] | None:
    """
    Parse tool call from Ollama response.
    
    Returns:
        Tuple of (tool_name, arguments) or None if no tool call
    """
    message = response.get("message", {})
    tool_calls = message.get("tool_calls", [])
    
    if not tool_calls:
        return None
    
    # Get first tool call
    call = tool_calls[0]
    func = call.get("function", {})
    
    return (
        func.get("name"),
        func.get("arguments", {}),
    )


def execute_tool(
    tool_name: str,
    arguments: dict,
    tools: dict[str, Callable],
) -> str:
    """Execute a tool and return result as string."""
    if tool_name not in tools:
        return f"Error: Unknown tool '{tool_name}'"
    
    try:
        result = tools[tool_name](**arguments)
        return str(result)
    except Exception as e:
        return f"Error executing {tool_name}: {e}"

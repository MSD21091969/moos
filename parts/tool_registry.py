"""Tool Registry - Unified tool management for agents.

Register, lookup, and execute tools across agents.
"""
from typing import Any, Callable
import inspect
import json


class ToolRegistry:
    """
    Registry for agent tools.
    
    Provides unified interface for tool management.
    """
    
    def __init__(self):
        self._tools: dict[str, Callable] = {}
        self._descriptions: dict[str, str] = {}
    
    def register(
        self,
        name: str,
        func: Callable,
        description: str | None = None,
    ) -> None:
        """
        Register a tool.
        
        Args:
            name: Tool name
            func: Tool function
            description: Human-readable description
        """
        self._tools[name] = func
        self._descriptions[name] = description or func.__doc__ or f"Tool: {name}"
    
    def get(self, name: str) -> Callable | None:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def execute(self, name: str, args: dict) -> Any:
        """
        Execute a tool with arguments.
        
        Args:
            name: Tool name
            args: Arguments dict
            
        Returns:
            Tool result
        """
        if name not in self._tools:
            raise ValueError(f"Unknown tool: {name}")
        
        return self._tools[name](**args)
    
    def list_tools(self) -> list[str]:
        """List all registered tool names."""
        return list(self._tools.keys())
    
    def to_ollama_format(self) -> list[dict]:
        """
        Convert tools to Ollama native format.
        
        For use with Ollama's function calling.
        """
        ollama_tools = []
        
        for name, func in self._tools.items():
            sig = inspect.signature(func)
            
            parameters = {
                "type": "object",
                "properties": {},
                "required": [],
            }
            
            for param_name, param in sig.parameters.items():
                if param_name in ("self", "kwargs"):
                    continue
                
                param_type = "string"
                if param.annotation != inspect.Parameter.empty:
                    ann = param.annotation
                    if ann == int:
                        param_type = "integer"
                    elif ann == float:
                        param_type = "number"
                    elif ann == bool:
                        param_type = "boolean"
                
                parameters["properties"][param_name] = {
                    "type": param_type,
                    "description": f"Parameter: {param_name}",
                }
                
                if param.default == inspect.Parameter.empty:
                    parameters["required"].append(param_name)
            
            ollama_tools.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": self._descriptions.get(name, ""),
                    "parameters": parameters,
                },
            })
        
        return ollama_tools
    
    def to_prompt_format(self) -> str:
        """
        Generate tool documentation for prompts.
        
        For models that don't support native function calling.
        """
        lines = ["## Available Tools\n"]
        
        for name, desc in self._descriptions.items():
            func = self._tools[name]
            sig = inspect.signature(func)
            
            params = []
            for pname, param in sig.parameters.items():
                if pname not in ("self", "kwargs"):
                    params.append(pname)
            
            lines.append(f"### {name}")
            lines.append(f"{desc}\n")
            if params:
                lines.append(f"Parameters: {', '.join(params)}\n")
        
        return "\n".join(lines)
    
    def parse_tool_call(self, response: str) -> tuple[str, dict] | None:
        """
        Parse a tool call from response text.
        
        Looks for TOOL_CALL: {...} pattern.
        """
        import re
        
        patterns = [
            r'TOOL_CALL:\s*(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})',
            r'\*\*TOOL_CALL:\s*(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})\*\*',
            r'`TOOL_CALL:\s*(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})`',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response)
            if match:
                try:
                    json_str = match.group(1).replace("'", '"')
                    call = json.loads(json_str)
                    return (call.get("tool"), call.get("args", {}))
                except json.JSONDecodeError:
                    continue
        
        return None
    
    def __len__(self) -> int:
        return len(self._tools)
    
    def __contains__(self, name: str) -> bool:
        return name in self._tools

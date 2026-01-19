"""Dynamic Definition Object - Runtime Pydantic Model Generation.

This module provides the `DefinitionObject` wrapper which adapts a `Definition`
(usually a CompositeDefinition) into a PydanticAI-compatible Tool with 
dynamically generated Input/Output models.
"""
from typing import Any, Callable, Type, Optional, List, Dict
from pydantic import BaseModel, create_model, Field
from pydantic_ai import RunContext

from models_v2.definition import Definition


def schema_to_python_type(schema: Dict[str, Any]) -> Type:
    """
    Convert a JSON Schema dict to a Python Type for Pydantic.
    
    Limitation: Currently supports basic scalars and list/dict containers.
    Complex nested objects will default to Any.
    """
    type_map = {
        "string": str,
        "integer": int, 
        "number": float,
        "boolean": bool,
        "array": list,
        "object": dict,
        "null": type(None)
    }
    
    req_type = schema.get("type", "string") # Default to string if unknown
    
    if req_type == "array":
        # TODO: Handle 'items' for typed lists
        return List[Any]
    
    if req_type == "object":
        # TODO: Handle 'properties' for typed dicts or nested models
        return Dict[str, Any]
        
    return type_map.get(req_type, Any)


class DefinitionObject:
    """
    Wraps a Definition to provide runtime Pydantic models and execution logic.
    
    Acts as an adapter:
    Definition (Graph Topology) <-> DefinitionObject <-> Agent (Tool)
    """
    def __init__(self, definition: Definition):
        self.definition = definition
        self._input_model: Optional[Type[BaseModel]] = None
        self._output_model: Optional[Type[BaseModel]] = None

    @property
    def input_model(self) -> Type[BaseModel]:
        """Dynamically generate the Input Pydantic Model from Input Ports."""
        if not self._input_model:
            fields = {}
            for port in self.definition.input_ports:
                py_type = schema_to_python_type(port.type_schema)
                # If optional, wrap in Optional and provide default
                if port.is_optional:
                    fields[port.name] = (Optional[py_type], None)
                else:
                    fields[port.name] = (py_type, ...)
            
            self._input_model = create_model(
                f"{self.definition.name}Input",
                **fields
            )
        return self._input_model

    @property
    def output_model(self) -> Type[BaseModel]:
        """Dynamically generate the Output Pydantic Model from Output Ports."""
        if not self._output_model:
            fields = {}
            for port in self.definition.output_ports:
                py_type = schema_to_python_type(port.type_schema)
                fields[port.name] = (py_type, ...)
                
            self._output_model = create_model(
                f"{self.definition.name}Output",
                **fields
            )
        return self._output_model

    def to_tool(self) -> Callable:
        """
        Returns an async function compatible with PydanticAI tools.
        
        The function signature will be:
        async def run_tool(ctx: RunContext, input_data: InputModel) -> OutputModel
        """
        # Capture model in closure
        InputModel = self.input_model
        
        async def run_tool(ctx: RunContext, input_data: InputModel) -> Dict[str, Any]:
            """
            Execute the definition as a tool.
            """
            # 1. Convert Model -> Dict
            inputs = input_data.model_dump()
            
            # 2. Execute Definition (Placeholder for acting Runtime)
            # In a real scenario, this would call the Runtime Service
            print(f"[{self.definition.name}] Executing with: {inputs}")
            results = self.definition.apply(inputs)
            
            # 3. Return results (PydanticAI handles Dict -> String/Model conversion)
            return results

        # Set metadata for the tool
        run_tool.__name__ = f"tool_{self.definition.name}"
        run_tool.__doc__ = self.definition.description or f"Execute {self.definition.name}"
        
        return run_tool

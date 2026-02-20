"""Core Execution Engine for Collider.

Handles dynamic tool loading and workflow orchestration.
"""

import asyncio
import importlib
import logging
from typing import Any, Dict, List, Optional

from src.schemas.registry import GraphStepEntry, SubgraphManifest

logger = logging.getLogger(__name__)


class ToolExecutionError(Exception):
    """Raised when a tool fails to execute."""
    pass


class WorkflowExecutionError(Exception):
    """Raised when a workflow fails."""
    pass


class ToolRunner:
    """Dynamically loads and executes tools based on code_ref."""

    @staticmethod
    async def execute(tool: GraphStepEntry, inputs: Dict[str, Any]) -> Any:
        """Execute a tool with given inputs."""
        if not tool.code_ref:
            # For now, if no code_ref, we just echo for testing
            logger.warning(f"Tool {tool.tool_name} has no code_ref. Echoing inputs.")
            return {"echo": inputs, "tool": tool.tool_name}

        try:
            # format: "module.path:function_name"
            if ":" not in tool.code_ref:
                raise ValueError(f"Invalid code_ref format: {tool.code_ref}. Expected 'module:func'")
            
            mod_path, func_name = tool.code_ref.split(":", 1)
            
            # Dynamic import
            # We assume the module is in the python path
            module = importlib.import_module(mod_path)
            func = getattr(module, func_name)
            
            # Inspect execution type (async vs sync)
            import inspect
            if inspect.iscoroutinefunction(func):
                result = await func(**inputs)
            else:
                result = func(**inputs)
                
            return result

        except Exception as e:
            logger.exception(f"Tool execution failed: {tool.tool_name}")
            raise ToolExecutionError(f"Tool {tool.tool_name} failed: {str(e)}")


class WorkflowExecutor:
    """Orchestrates the execution of a workflow."""

    def __init__(self, registry):
        # We need the registry to look up step definitions
        self.registry = registry

    async def execute(self, manifest: SubgraphManifest, initial_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a workflow (linear sequence for now)."""
        logger.info(f"Starting workflow {manifest.workflow_name}")
        
        context = initial_inputs.copy()
        history = []

        # Simple linear execution of steps
        # In a real graph, we'd traverse edges. Here we assume 'steps' is the order.
        for step_name in manifest.steps:
            tool_entry = self.registry.get_tool(step_name)
            if not tool_entry:
                raise WorkflowExecutionError(f"Step '{step_name}' refers to unknown tool.")

            logger.info(f"Executing step: {step_name}")
            
            # Mapper logic:
            # For this simple prototype, we pass the ENTIRE context as inputs
            # In V4, we'd use inputs_map to filter/rename keys.
            step_inputs = context 
            
            try:
                result = await ToolRunner.execute(tool_entry, step_inputs)
            except ToolExecutionError as e:
                logger.error(f"Workflow aborted at step {step_name}: {e}")
                raise e

            # Update context with results
            # We assume results are a dict and merge them? 
            # Or do we namespace them?
            # For V3 simple: if result is dict, merge. Else store as 'last_result'
            if isinstance(result, dict):
                context.update(result)
            else:
                context["last_result"] = result
                
            history.append({
                "step": step_name,
                "result": result
            })

        logger.info(f"Workflow {manifest.workflow_name} completed.")
        return context

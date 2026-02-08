"""
Workflow Engine for GraphTool Server
Executes workflows defined in .agent/workflows YAML files.

A workflow consists of:
- steps: Sequential or conditional steps
- tools: Available tools for execution
- context: Node container, user info, secrets
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Awaitable
import asyncio
import logging

logger = logging.getLogger(__name__)


class StepStatus(str, Enum):
    """Status of a workflow step."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowStatus(str, Enum):
    """Status of a workflow."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class StepResult:
    """Result of a workflow step."""

    step_id: str
    status: StepStatus
    output: Any = None
    error: str | None = None
    duration_ms: float = 0


@dataclass
class WorkflowContext:
    """Context for workflow execution."""

    user_id: str
    app_id: str
    node_path: str
    container: dict = field(default_factory=dict)
    variables: dict = field(default_factory=dict)
    secrets: dict = field(default_factory=dict)  # Injected at runtime

    def get_var(self, name: str, default: Any = None) -> Any:
        """Get a variable from context."""
        return self.variables.get(name, default)

    def set_var(self, name: str, value: Any) -> None:
        """Set a variable in context."""
        self.variables[name] = value


@dataclass
class WorkflowStep:
    """A step in a workflow."""

    id: str
    type: str  # "prompt", "tool", "condition", "loop", "parallel"
    config: dict = field(default_factory=dict)
    next_step: str | None = None
    on_error: str | None = None  # Step to run on error, or "fail"
    condition: str | None = None  # Expression to evaluate

    @classmethod
    def from_dict(cls, data: dict) -> "WorkflowStep":
        """Create step from dictionary."""
        return cls(
            id=data["id"],
            type=data["type"],
            config=data.get("config", {}),
            next_step=data.get("next"),
            on_error=data.get("on_error"),
            condition=data.get("condition"),
        )


@dataclass
class Workflow:
    """A workflow definition."""

    id: str
    name: str
    description: str = ""
    steps: list[WorkflowStep] = field(default_factory=list)
    entry_point: str = ""  # First step ID

    @classmethod
    def from_dict(cls, data: dict) -> "Workflow":
        """Create workflow from dictionary (YAML parsed)."""
        steps = [WorkflowStep.from_dict(s) for s in data.get("steps", [])]
        return cls(
            id=data.get("id", "unknown"),
            name=data.get("name", "Unnamed Workflow"),
            description=data.get("description", ""),
            steps=steps,
            entry_point=data.get("entry_point", steps[0].id if steps else ""),
        )


# Type for step executors
StepExecutor = Callable[[WorkflowStep, WorkflowContext], Awaitable[StepResult]]


class WorkflowEngine:
    """
    Executes workflows with streaming updates.
    """

    def __init__(self):
        self._executors: dict[str, StepExecutor] = {}
        self._register_builtin_executors()

    def _register_builtin_executors(self):
        """Register built-in step executors."""
        self._executors["prompt"] = self._execute_prompt
        self._executors["tool"] = self._execute_tool
        self._executors["condition"] = self._execute_condition
        self._executors["set_variable"] = self._execute_set_variable
        self._executors["parallel"] = self._execute_parallel

    def register_executor(self, step_type: str, executor: StepExecutor):
        """Register a custom step executor."""
        self._executors[step_type] = executor

    async def execute(
        self,
        workflow: Workflow,
        context: WorkflowContext,
        on_step_start: Callable[[str], Awaitable[None]] | None = None,
        on_step_complete: Callable[[StepResult], Awaitable[None]] | None = None,
    ) -> list[StepResult]:
        """
        Execute a workflow and return results for all steps.

        Args:
            workflow: The workflow to execute
            context: Execution context
            on_step_start: Callback when step starts
            on_step_complete: Callback when step completes

        Returns:
            List of step results in execution order
        """
        results: list[StepResult] = []
        steps_by_id = {s.id: s for s in workflow.steps}

        current_step_id = workflow.entry_point

        while current_step_id:
            step = steps_by_id.get(current_step_id)
            if not step:
                logger.error(f"Step not found: {current_step_id}")
                break

            # Notify step start
            if on_step_start:
                await on_step_start(step.id)

            # Check condition
            if step.condition:
                should_run = self._evaluate_condition(step.condition, context)
                if not should_run:
                    result = StepResult(
                        step_id=step.id,
                        status=StepStatus.SKIPPED,
                    )
                    results.append(result)
                    if on_step_complete:
                        await on_step_complete(result)
                    current_step_id = step.next_step
                    continue

            # Execute step
            import time

            start_time = time.time()

            try:
                executor = self._executors.get(step.type)
                if not executor:
                    raise ValueError(f"Unknown step type: {step.type}")

                result = await executor(step, context)
                result.duration_ms = (time.time() - start_time) * 1000

            except Exception as e:
                logger.exception(f"Step {step.id} failed")
                result = StepResult(
                    step_id=step.id,
                    status=StepStatus.FAILED,
                    error=str(e),
                    duration_ms=(time.time() - start_time) * 1000,
                )

            results.append(result)

            # Notify step complete
            if on_step_complete:
                await on_step_complete(result)

            # Determine next step
            if result.status == StepStatus.FAILED:
                if step.on_error and step.on_error != "fail":
                    current_step_id = step.on_error
                else:
                    break  # Stop workflow on error
            else:
                current_step_id = step.next_step

        return results

    def _evaluate_condition(self, condition: str, context: WorkflowContext) -> bool:
        """Evaluate a condition expression."""
        # Simple variable-based conditions for MVP
        # Format: "var:name == value" or "var:name"
        try:
            if condition.startswith("var:"):
                parts = condition[4:].split("==")
                var_name = parts[0].strip()
                value = context.get_var(var_name)

                if len(parts) == 1:
                    return bool(value)

                expected = parts[1].strip().strip("'\"")
                return str(value) == expected

            return True
        except Exception:
            return True

    async def _execute_prompt(
        self, step: WorkflowStep, context: WorkflowContext
    ) -> StepResult:
        """Execute a prompt step using Pydantic AI."""
        from src.graphs.pydantic_ai import agent

        prompt_template = step.config.get("prompt", "")

        # Simple variable substitution
        prompt = prompt_template
        for key, value in context.variables.items():
            prompt = prompt.replace(f"{{{key}}}", str(value))

        result = await agent.run(prompt)

        # Store output in variable if specified
        output_var = step.config.get("output_var")
        if output_var:
            context.set_var(output_var, result.data)

        return StepResult(
            step_id=step.id,
            status=StepStatus.COMPLETED,
            output=result.data,
        )

    async def _execute_tool(
        self, step: WorkflowStep, context: WorkflowContext
    ) -> StepResult:
        """Execute a tool step."""
        tool_name = step.config.get("tool")
        tool_args = step.config.get("args", {})

        # Substitute variables in args
        resolved_args = {}
        for key, value in tool_args.items():
            if isinstance(value, str) and value.startswith("var:"):
                var_name = value[4:]
                resolved_args[key] = context.get_var(var_name)
            else:
                resolved_args[key] = value

        from src.graphs.pydantic_ai import execute_tool

        result = await execute_tool(tool_name, resolved_args, context.__dict__)

        # Store output in variable if specified
        output_var = step.config.get("output_var")
        if output_var:
            context.set_var(output_var, result)

        return StepResult(
            step_id=step.id,
            status=StepStatus.COMPLETED,
            output=result,
        )

    async def _execute_condition(
        self, step: WorkflowStep, context: WorkflowContext
    ) -> StepResult:
        """Execute a condition step (branch)."""
        # Condition step just evaluates and sets next step
        condition = step.config.get("condition", "")
        result_val = self._evaluate_condition(condition, context)

        # Override next step based on condition
        if result_val:
            step.next_step = step.config.get("then")
        else:
            step.next_step = step.config.get("else")

        return StepResult(
            step_id=step.id,
            status=StepStatus.COMPLETED,
            output={"condition_result": result_val},
        )

    async def _execute_set_variable(
        self, step: WorkflowStep, context: WorkflowContext
    ) -> StepResult:
        """Set a variable in context."""
        var_name = step.config.get("name")
        var_value = step.config.get("value")

        if var_name:
            context.set_var(var_name, var_value)

        return StepResult(
            step_id=step.id,
            status=StepStatus.COMPLETED,
            output={"set": var_name, "value": var_value},
        )

    async def _execute_parallel(
        self, step: WorkflowStep, context: WorkflowContext
    ) -> StepResult:
        """Execute multiple steps in parallel."""
        parallel_steps = step.config.get("steps", [])

        # Create sub-steps
        sub_steps = [WorkflowStep.from_dict(s) for s in parallel_steps]

        # Execute in parallel
        tasks = []
        for sub_step in sub_steps:
            executor = self._executors.get(sub_step.type)
            if executor:
                tasks.append(executor(sub_step, context))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Check for failures
        outputs = []
        failed = False
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                outputs.append({"step": sub_steps[i].id, "error": str(result)})
                failed = True
            else:
                outputs.append({"step": sub_steps[i].id, "output": result.output})

        return StepResult(
            step_id=step.id,
            status=StepStatus.FAILED if failed else StepStatus.COMPLETED,
            output=outputs,
        )


# Global engine instance
workflow_engine = WorkflowEngine()

"""Tests for workflow engine module."""

import pytest
from unittest.mock import AsyncMock, patch

from src.graphs.engine import (
    WorkflowEngine,
    Workflow,
    WorkflowStep,
    WorkflowContext,
    StepResult,
    StepStatus,
)


class TestWorkflowStep:
    """Test WorkflowStep class."""

    def test_from_dict_basic(self):
        data = {
            "id": "step1",
            "type": "prompt",
            "config": {"prompt": "Hello"},
        }

        step = WorkflowStep.from_dict(data)

        assert step.id == "step1"
        assert step.type == "prompt"
        assert step.config["prompt"] == "Hello"

    def test_from_dict_with_navigation(self):
        data = {
            "id": "step1",
            "type": "prompt",
            "next": "step2",
            "on_error": "error_handler",
        }

        step = WorkflowStep.from_dict(data)

        assert step.next_step == "step2"
        assert step.on_error == "error_handler"


class TestWorkflow:
    """Test Workflow class."""

    def test_from_dict(self):
        data = {
            "id": "workflow1",
            "name": "Test Workflow",
            "description": "A test",
            "steps": [
                {"id": "step1", "type": "prompt", "config": {}},
                {"id": "step2", "type": "tool", "config": {}},
            ],
            "entry_point": "step1",
        }

        workflow = Workflow.from_dict(data)

        assert workflow.id == "workflow1"
        assert workflow.name == "Test Workflow"
        assert len(workflow.steps) == 2
        assert workflow.entry_point == "step1"

    def test_from_dict_auto_entry_point(self):
        data = {
            "id": "workflow1",
            "name": "Test",
            "steps": [
                {"id": "first", "type": "prompt", "config": {}},
            ],
        }

        workflow = Workflow.from_dict(data)

        assert workflow.entry_point == "first"


class TestWorkflowContext:
    """Test WorkflowContext class."""

    def test_get_set_var(self):
        ctx = WorkflowContext(
            user_id="user1",
            app_id="app1",
            node_path="/",
        )

        ctx.set_var("foo", "bar")

        assert ctx.get_var("foo") == "bar"
        assert ctx.get_var("missing") is None
        assert ctx.get_var("missing", "default") == "default"


class TestWorkflowEngine:
    """Test WorkflowEngine class."""

    @pytest.fixture
    def engine(self):
        return WorkflowEngine()

    @pytest.fixture
    def simple_workflow(self):
        return Workflow(
            id="test",
            name="Test",
            steps=[
                WorkflowStep(
                    id="set_var",
                    type="set_variable",
                    config={"name": "result", "value": "hello"},
                    next_step=None,
                ),
            ],
            entry_point="set_var",
        )

    @pytest.fixture
    def context(self):
        return WorkflowContext(
            user_id="user1",
            app_id="app1",
            node_path="/",
        )

    @pytest.mark.asyncio
    async def test_execute_simple_workflow(self, engine, simple_workflow, context):
        results = await engine.execute(simple_workflow, context)

        assert len(results) == 1
        assert results[0].status == StepStatus.COMPLETED
        assert context.get_var("result") == "hello"

    @pytest.mark.asyncio
    async def test_callbacks_are_called(self, engine, simple_workflow, context):
        started = []
        completed = []

        async def on_start(step_id):
            started.append(step_id)

        async def on_complete(result):
            completed.append(result)

        await engine.execute(
            simple_workflow,
            context,
            on_step_start=on_start,
            on_step_complete=on_complete,
        )

        assert started == ["set_var"]
        assert len(completed) == 1

    @pytest.mark.asyncio
    async def test_condition_skips_step(self, engine, context):
        workflow = Workflow(
            id="conditional",
            name="Conditional",
            steps=[
                WorkflowStep(
                    id="conditional_step",
                    type="set_variable",
                    config={"name": "x", "value": "set"},
                    condition="var:skip_me",  # Not set, so False
                ),
            ],
            entry_point="conditional_step",
        )

        results = await engine.execute(workflow, context)

        assert results[0].status == StepStatus.SKIPPED
        assert context.get_var("x") is None

    @pytest.mark.asyncio
    async def test_multi_step_execution(self, engine, context):
        workflow = Workflow(
            id="multi",
            name="Multi Step",
            steps=[
                WorkflowStep(
                    id="step1",
                    type="set_variable",
                    config={"name": "a", "value": 1},
                    next_step="step2",
                ),
                WorkflowStep(
                    id="step2",
                    type="set_variable",
                    config={"name": "b", "value": 2},
                    next_step=None,
                ),
            ],
            entry_point="step1",
        )

        results = await engine.execute(workflow, context)

        assert len(results) == 2
        assert all(r.status == StepStatus.COMPLETED for r in results)
        assert context.get_var("a") == 1
        assert context.get_var("b") == 2

    @pytest.mark.asyncio
    async def test_error_stops_workflow(self, engine, context):
        # Register a failing executor
        async def failing_executor(step, ctx):
            raise ValueError("Test error")

        engine.register_executor("fail", failing_executor)

        workflow = Workflow(
            id="failing",
            name="Failing",
            steps=[
                WorkflowStep(
                    id="fail_step",
                    type="fail",
                    config={},
                    next_step="never_reached",
                ),
                WorkflowStep(
                    id="never_reached",
                    type="set_variable",
                    config={"name": "x", "value": 1},
                ),
            ],
            entry_point="fail_step",
        )

        results = await engine.execute(workflow, context)

        assert len(results) == 1  # Stopped after first
        assert results[0].status == StepStatus.FAILED
        assert "Test error" in results[0].error

"""
Tests for Workspace Agent
=========================
Tests the workspace agent context building and spec loading.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess

# Use package imports to match production code paths
from agent_factory.parts.agents.workspace_agent import (
    WorkspaceAgent,
    WorkspaceContext,
)
from agent_factory.parts.templates.agent_spec import AgentSpec
from agent_factory.parts.config.settings import WorkspaceSettings


class TestWorkspaceContext:
    """Tests for WorkspaceContext model."""

    def test_to_context_string_basic(self):
        """Should format basic context."""
        ctx = WorkspaceContext(
            cwd=Path("/factory/workspace"),
            workspace_root=Path("/factory/workspace"),
            factory_root=Path("/factory"),
            path_from_root=["workspace"],
            workspace_type="workspace",
        )

        result = ctx.to_context_string()

        assert "## Current Workspace Context" in result
        assert "Working directory:" in result
        assert "workspace" in result

    def test_to_context_string_with_git(self):
        """Should include git info when available."""
        ctx = WorkspaceContext(
            cwd=Path("/factory/workspace"),
            workspace_root=Path("/factory/workspace"),
            factory_root=Path("/factory"),
            git_branch="main",
            git_status=["file1.py", "file2.py"],
            git_root=Path("/factory"),
        )

        result = ctx.to_context_string()

        assert "Git branch: main" in result
        assert "Modified files: 2" in result

    def test_to_context_string_limits_files(self):
        """Should limit displayed files to 5."""
        ctx = WorkspaceContext(
            cwd=Path("/factory"),
            workspace_root=Path("/factory"),
            factory_root=Path("/factory"),
            git_branch="main",
            git_status=[f"file{i}.py" for i in range(10)],
        )

        result = ctx.to_context_string()

        # Should show 5 files + "... and 5 more"
        assert "... and 5 more" in result


class TestWorkspaceAgentBuildContext:
    """Tests for context building."""

    def test_builds_context_from_factory_root(self, tmp_path):
        """Should build context at factory root."""
        factory = tmp_path / "factory"
        factory.mkdir()

        ctx = WorkspaceAgent._build_context(factory, factory)

        assert ctx.cwd == factory
        assert ctx.factory_root == factory
        assert ctx.workspace_type == "factory"
        assert ctx.path_from_root == []

    def test_builds_context_from_workspace(self, tmp_path):
        """Should build context from child workspace."""
        factory = tmp_path / "factory"
        workspace = factory / "workspaces" / "myproject"
        workspace.mkdir(parents=True)

        ctx = WorkspaceAgent._build_context(workspace, factory)

        assert ctx.cwd == workspace
        assert ctx.factory_root == factory
        assert ctx.workspace_type == "workspace"
        assert ctx.path_from_root == ["workspaces", "myproject"]

    def test_detects_collider_workspace(self, tmp_path):
        """Should detect collider workspace type."""
        factory = tmp_path / "factory"
        collider = factory / "workspaces" / "collider_apps"
        collider.mkdir(parents=True)

        ctx = WorkspaceAgent._build_context(collider, factory)

        assert ctx.workspace_type == "collider"

    @patch("subprocess.run")
    def test_gets_git_info(self, mock_run, tmp_path):
        """Should get git branch and status."""
        factory = tmp_path / "factory"
        factory.mkdir()

        # Mock git commands
        def mock_git_command(args, **kwargs):
            result = MagicMock()
            result.returncode = 0
            if "rev-parse" in args:
                result.stdout = str(factory)
            elif "branch" in args:
                result.stdout = "main"
            elif "status" in args:
                result.stdout = " M file1.py\n M file2.py"
            return result

        mock_run.side_effect = mock_git_command

        ctx = WorkspaceAgent._build_context(factory, factory)

        assert ctx.git_branch == "main"
        assert ctx.git_root == factory
        assert len(ctx.git_status) == 2


class TestWorkspaceAgentLoadSpec:
    """Tests for spec loading from .agent/ hierarchy."""

    def test_loads_instructions_from_agent_dir(self, tmp_path):
        """Should load instructions.md from .agent/."""
        factory = tmp_path / "factory"
        factory.mkdir()
        agent_dir = factory / ".agent"
        agent_dir.mkdir()
        (agent_dir / "instructions.md").write_text("You are a helpful assistant.")

        spec = WorkspaceAgent._load_spec_from_hierarchy(factory, factory, "workspace")

        assert "helpful assistant" in spec.instructions

    def test_loads_rules_from_hierarchy(self, tmp_path):
        """Should accumulate rules from all levels."""
        # Factory
        factory = tmp_path / "factory"
        factory.mkdir()
        factory_agent = factory / ".agent"
        factory_agent.mkdir()
        factory_rules = factory_agent / "rules"
        factory_rules.mkdir()
        (factory_rules / "sandbox.md").write_text("# Sandbox Rule\nBe safe.")

        # Workspace
        workspace = factory / "workspace"
        workspace.mkdir()
        ws_agent = workspace / ".agent"
        ws_agent.mkdir()
        ws_rules = ws_agent / "rules"
        ws_rules.mkdir()
        (ws_rules / "coding.md").write_text("# Coding Rule\nWrite clean code.")

        spec = WorkspaceAgent._load_spec_from_hierarchy(workspace, factory, "workspace")

        assert len(spec.rules) == 2
        assert any("Sandbox" in r for r in spec.rules)
        assert any("Coding" in r for r in spec.rules)

    def test_instructions_override_at_child_level(self, tmp_path):
        """Child instructions should override parent."""
        # Factory
        factory = tmp_path / "factory"
        factory.mkdir()
        factory_agent = factory / ".agent"
        factory_agent.mkdir()
        (factory_agent / "instructions.md").write_text("Factory instructions")

        # Workspace
        workspace = factory / "workspace"
        workspace.mkdir()
        ws_agent = workspace / ".agent"
        ws_agent.mkdir()
        (ws_agent / "instructions.md").write_text("Workspace instructions")

        spec = WorkspaceAgent._load_spec_from_hierarchy(workspace, factory, "workspace")

        assert spec.instructions == "Workspace instructions"


class TestWorkspaceAgentFromWorkspace:
    """Tests for WorkspaceAgent.from_workspace()."""

    def test_creates_agent_from_factory(self, tmp_path, monkeypatch):
        """Should create agent from factory root."""
        # Setup factory structure
        factory = tmp_path / "factory"
        factory.mkdir()
        agent_dir = factory / ".agent"
        agent_dir.mkdir()
        (agent_dir / "manifest.yaml").write_text("includes: []")
        (agent_dir / "instructions.md").write_text("Test instructions")

        # Setup configs
        configs_dir = agent_dir / "configs"
        configs_dir.mkdir()
        (configs_dir / "users.yaml").write_text("users: {}")

        # Setup secrets
        secrets_dir = factory / "secrets"
        secrets_dir.mkdir()

        # Clear env so it finds factory by manifest
        monkeypatch.delenv("FACTORY_ROOT", raising=False)

        agent = WorkspaceAgent.from_workspace(factory)

        assert agent.spec.id == "workspace"
        assert agent.context.workspace_type == "factory"
        assert "Test instructions" in agent.spec.instructions

    def test_raises_if_not_in_factory(self, tmp_path, monkeypatch):
        """Should raise if not in factory hierarchy."""
        monkeypatch.delenv("FACTORY_ROOT", raising=False)

        with pytest.raises(ValueError, match="Not in a Factory"):
            WorkspaceAgent.from_workspace(tmp_path)


class TestWorkspaceAgentGetSystemPrompt:
    """Tests for system prompt generation."""

    def test_includes_instructions_and_context(self, tmp_path, monkeypatch):
        """System prompt should include both instructions and context."""
        # Setup minimal factory
        factory = tmp_path / "factory"
        factory.mkdir()
        agent_dir = factory / ".agent"
        agent_dir.mkdir()
        (agent_dir / "manifest.yaml").write_text("includes: []")
        (agent_dir / "instructions.md").write_text("Base instructions here.")
        rules_dir = agent_dir / "rules"
        rules_dir.mkdir()
        (rules_dir / "test.md").write_text("# Test Rule")
        configs_dir = agent_dir / "configs"
        configs_dir.mkdir()
        (configs_dir / "users.yaml").write_text("users: {}")
        secrets_dir = factory / "secrets"
        secrets_dir.mkdir()

        monkeypatch.delenv("FACTORY_ROOT", raising=False)

        agent = WorkspaceAgent.from_workspace(factory)
        prompt = agent.get_system_prompt()

        assert "Base instructions" in prompt
        assert "## Current Workspace Context" in prompt
        assert "Test Rule" in prompt


class TestWorkspaceAgentToDict:
    """Tests for serialization."""

    def test_to_dict(self):
        """Should serialize to dict."""
        spec = AgentSpec(id="test", name="Test Agent")
        ctx = WorkspaceContext(
            cwd=Path("/factory"),
            workspace_root=Path("/factory"),
            factory_root=Path("/factory"),
        )

        # Use already-imported WorkspaceSettings
        settings = WorkspaceSettings(
            factory_root=Path("/factory"),
            secrets_dir=Path("/factory/secrets"),
        )

        agent = WorkspaceAgent(
            spec=spec,
            context=ctx,
            settings=settings,
        )

        result = agent.to_dict()

        assert result["spec"]["id"] == "test"
        assert "cwd" in result["context"]
        assert result["history_length"] == 0

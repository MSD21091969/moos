"""
Workspace Agent
===============
Generic agent that operates on filesystem/workspace context.

Loads from .agent/ hierarchy (L1 pattern) and provides:
- Workspace-aware context (cwd, git status, file tree)
- Inherits rules/instructions from parent .agent/ folders
- Can be run in any workspace via Factory parts import

This is the L1 equivalent of L2 Collider Pilots.

Usage:
    from agent_factory.parts import get_part

    WorkspaceAgent = get_part("workspace_agent_v1")

    # Load from current workspace's .agent/ hierarchy
    agent = WorkspaceAgent.from_workspace(Path.cwd())

    # Get full instructions with context
    prompt = agent.get_system_prompt()
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from agent_factory.parts.templates.agent_spec import AgentSpec
from agent_factory.parts.config.settings import (
    load_workspace_settings,
    find_factory_root,
    WorkspaceSettings,
)


class WorkspaceContext(BaseModel):
    """
    Current workspace state for context injection.

    Mirrors PilotContext from frontend but for filesystem.
    """

    # Current location
    cwd: Path
    workspace_root: Path
    factory_root: Path

    # Navigation (like breadcrumbs)
    path_from_root: list[str] = Field(default_factory=list)

    # Git state (if in git repo)
    git_branch: Optional[str] = None
    git_status: list[str] = Field(default_factory=list)  # Modified/staged files
    git_root: Optional[Path] = None

    # File context
    active_file: Optional[Path] = None
    recent_files: list[Path] = Field(default_factory=list)

    # Workspace type
    workspace_type: str = "generic"  # "factory", "collider", "application", etc.

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def to_context_string(self) -> str:
        """Format context for system prompt injection."""
        lines = [
            "## Current Workspace Context",
            f"- Working directory: {self.cwd}",
            f"- Path from root: {' > '.join(self.path_from_root) or 'root'}",
            f"- Workspace type: {self.workspace_type}",
        ]

        if self.git_branch:
            lines.append(f"- Git branch: {self.git_branch}")
            if self.git_status:
                lines.append(f"- Modified files: {len(self.git_status)}")
                for f in self.git_status[:5]:  # Limit to 5
                    lines.append(f"  - {f}")
                if len(self.git_status) > 5:
                    lines.append(f"  - ... and {len(self.git_status) - 5} more")

        if self.active_file:
            lines.append(f"- Active file: {self.active_file.name}")

        return "\n".join(lines)


class WorkspaceAgent(BaseModel):
    """
    Generic workspace agent for L1 operations.

    Specs for agents that work with code/files - can be run from
    IDE extensions, local CLI tools, etc.

    Loads configuration from .agent/ folder hierarchy (deepagent pattern).

    Usage:
        agent = WorkspaceAgent.from_workspace(path)
        agent.with_workspace_context({...})  # Inject runtime context
        prompt = agent.get_system_prompt()
    """

    # Agent specification (loaded from .agent/)
    spec: AgentSpec

    # Current context
    context: WorkspaceContext

    # Settings (from Factory hierarchy)
    settings: WorkspaceSettings

    # Chat history (for conversation continuity)
    history: list[dict[str, str]] = Field(default_factory=list)

    # Runtime context injection (like pilots have container_context)
    _runtime_context: Optional[dict[str, Any]] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def from_workspace(
        cls,
        workspace_path: Optional[Path] = None,
        agent_id: str = "workspace",
    ) -> "WorkspaceAgent":
        """
        Create a workspace agent from a directory.

        Args:
            workspace_path: Path to workspace (default: cwd)
            agent_id: Agent folder name within .agent/ (default: "workspace")

        Returns:
            Configured WorkspaceAgent
        """
        workspace_path = workspace_path or Path.cwd()
        factory_root = find_factory_root(workspace_path)

        if not factory_root:
            raise ValueError("Not in a Factory workspace hierarchy")

        # Load settings from hierarchy
        settings = load_workspace_settings(workspace_path, factory_root)

        # Build context
        context = cls._build_context(workspace_path, factory_root)

        # Load agent spec from .agent/ hierarchy
        spec = cls._load_spec_from_hierarchy(workspace_path, factory_root, agent_id)

        return cls(
            spec=spec,
            context=context,
            settings=settings,
        )

    @classmethod
    def _build_context(cls, cwd: Path, factory_root: Path) -> WorkspaceContext:
        """Build workspace context from current state."""

        # Calculate path from root
        try:
            rel_path = cwd.relative_to(factory_root)
            path_from_root = list(rel_path.parts)
        except ValueError:
            path_from_root = []

        # Detect workspace type
        workspace_type = "generic"
        if cwd == factory_root:
            workspace_type = "factory"
        elif "collider" in str(cwd).lower():
            workspace_type = "collider"
        elif "workspaces" in path_from_root:
            workspace_type = "workspace"

        # Git info
        git_branch = None
        git_status = []
        git_root = None

        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=cwd,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                git_root = Path(result.stdout.strip())

                # Get branch
                result = subprocess.run(
                    ["git", "branch", "--show-current"],
                    cwd=cwd,
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    git_branch = result.stdout.strip()

                # Get status (modified files)
                result = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=cwd,
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    git_status = [
                        line[3:]
                        for line in result.stdout.strip().split("\n")
                        if line.strip()
                    ]
        except Exception:
            pass  # Git not available

        return WorkspaceContext(
            cwd=cwd,
            workspace_root=cwd,
            factory_root=factory_root,
            path_from_root=path_from_root,
            git_branch=git_branch,
            git_status=git_status,
            git_root=git_root,
            workspace_type=workspace_type,
        )

    @classmethod
    def _load_spec_from_hierarchy(
        cls,
        workspace_path: Path,
        factory_root: Path,
        agent_id: str,
    ) -> AgentSpec:
        """
        Load and merge agent spec from .agent/ hierarchy.

        Walks from factory_root to workspace_path, merging:
        - instructions.md
        - rules/*.md
        - workflows/*.md
        - knowledge/*.md
        """
        # Collect all .agent directories
        agent_dirs = []
        current = workspace_path

        while current != factory_root.parent:
            agent_dir = current / ".agent"
            if agent_dir.exists():
                agent_dirs.insert(0, agent_dir)
            if current == factory_root:
                break
            current = current.parent

        # Start with base spec
        spec = AgentSpec(
            id=agent_id,
            name="Workspace Agent",
            version="1.0.0",
        )

        # Merge from each level (factory first, workspace last)
        all_rules = []
        all_knowledge = []

        for agent_dir in agent_dirs:
            # Load instructions (override)
            instructions_file = agent_dir / "instructions.md"
            if instructions_file.exists():
                spec.instructions = instructions_file.read_text(encoding="utf-8")

            # Load rules (accumulate)
            rules_dir = agent_dir / "rules"
            if rules_dir.exists():
                for rule_file in sorted(rules_dir.glob("*.md")):
                    all_rules.append(rule_file.read_text(encoding="utf-8"))

            # Load knowledge (accumulate)
            knowledge_dir = agent_dir / "knowledge"
            if knowledge_dir.exists():
                for kb_file in sorted(knowledge_dir.glob("*.md")):
                    all_knowledge.append(kb_file.read_text(encoding="utf-8"))

        spec.rules = all_rules
        spec.knowledge = all_knowledge

        return spec

    def get_system_prompt(self) -> str:
        """
        Build full system prompt with context.

        Combines:
        1. Base instructions from spec
        2. Rules from hierarchy
        3. Knowledge from hierarchy
        4. Current workspace context
        5. Runtime context (if injected)
        """
        parts = [self.spec.get_full_instructions()]
        parts.append("\n\n")
        parts.append(self.context.to_context_string())

        # Add runtime context if present
        if self._runtime_context:
            parts.append("\n\n## Runtime Context\n")
            if "active_file" in self._runtime_context:
                parts.append(f"- Active file: {self._runtime_context['active_file']}\n")
            if "selection" in self._runtime_context:
                parts.append(f"- Selection: {self._runtime_context['selection']}\n")
            if "cursor_line" in self._runtime_context:
                parts.append(f"- Cursor line: {self._runtime_context['cursor_line']}\n")
            if "open_files" in self._runtime_context:
                parts.append(
                    f"- Open files: {len(self._runtime_context['open_files'])}\n"
                )
            if "diagnostics" in self._runtime_context:
                parts.append(
                    f"- Diagnostics: {len(self._runtime_context['diagnostics'])} issues\n"
                )
            # Include any additional custom context
            for key, value in self._runtime_context.items():
                if key not in (
                    "active_file",
                    "selection",
                    "cursor_line",
                    "open_files",
                    "diagnostics",
                ):
                    parts.append(f"- {key}: {value}\n")

        return "".join(parts)

    def update_context(self, **kwargs: Any) -> None:
        """Update context fields (e.g., active_file changed)."""
        for key, value in kwargs.items():
            if hasattr(self.context, key):
                setattr(self.context, key, value)

    def with_workspace_context(self, context: dict[str, Any]) -> "WorkspaceAgent":
        """
        Inject runtime workspace context.

        Called when agent is initialized with additional runtime data
        (active file, selection, editor state, etc.).

        Args:
            context: Runtime workspace data

        Returns:
            Self for chaining
        """
        self._runtime_context = context
        return self

    def add_message(self, role: str, content: str) -> None:
        """Add a message to history."""
        self.history.append({"role": role, "content": content})

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.history = []

    def to_dict(self) -> dict[str, Any]:
        """Export for serialization."""
        return {
            "spec": self.spec.to_dict(),
            "context": {
                "cwd": str(self.context.cwd),
                "workspace_root": str(self.context.workspace_root),
                "factory_root": str(self.context.factory_root),
                "path_from_root": self.context.path_from_root,
                "git_branch": self.context.git_branch,
                "workspace_type": self.context.workspace_type,
            },
            "history_length": len(self.history),
        }


# Rebuild models for Python 3.14+ compatibility
# Required when nested Pydantic models are defined in the same module
WorkspaceContext.model_rebuild()
WorkspaceAgent.model_rebuild()

"""
Context Builders for Local UX
=============================
Build WorkspaceContext and ContainerContext for agents/pilots.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class WorkspaceContext:
    """Runtime context for workspace agents."""

    workspace_root: Path
    active_file: Path | None = None
    git_branch: str | None = None
    git_status: list[str] = field(default_factory=list)
    diagnostics: list[dict[str, Any]] = field(default_factory=list)

    def to_prompt_section(self) -> str:
        """Format context as markdown section for system prompt."""
        lines = ["## Workspace Context\n"]
        lines.append(f"- **Workspace root**: `{self.workspace_root}`\n")

        if self.active_file:
            lines.append(f"- **Active file**: `{self.active_file}`\n")

        if self.git_branch:
            lines.append(f"- **Git branch**: `{self.git_branch}`\n")

        if self.git_status:
            lines.append(f"- **Modified files**: {len(self.git_status)}\n")
            for f in self.git_status[:5]:  # Show first 5
                lines.append(f"  - `{f}`\n")
            if len(self.git_status) > 5:
                lines.append(f"  - ... and {len(self.git_status) - 5} more\n")

        if self.diagnostics:
            lines.append(f"- **Diagnostics**: {len(self.diagnostics)} issues\n")

        return "".join(lines)


def build_workspace_context(
    workspace_root: Path,
    active_file: Path | None = None,
) -> WorkspaceContext:
    """
    Build WorkspaceContext from filesystem state.

    Args:
        workspace_root: Root directory of the workspace
        active_file: Currently active file (optional)

    Returns:
        WorkspaceContext with git info populated
    """
    context = WorkspaceContext(
        workspace_root=workspace_root.resolve(),
        active_file=active_file.resolve() if active_file else None,
    )

    # Get git branch
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=workspace_root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            context.git_branch = result.stdout.strip() or None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Get git status (modified files)
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=workspace_root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            context.git_status = [
                line[3:].strip()
                for line in result.stdout.strip().split("\n")
                if line.strip()
            ]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return context


@dataclass
class ContainerContext:
    """Runtime context for pilots (stub - mirrors SDK type)."""

    container_id: str
    container_name: str
    canvases: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    user_id: str = "local-user"
    user_name: str = "Local User"

    def to_prompt_section(self) -> str:
        """Format context as markdown section for system prompt."""
        lines = ["## Container Context\n"]
        lines.append(
            f"- **Container**: {self.container_name} (`{self.container_id}`)\n"
        )
        lines.append(f"- **Canvases**: {len(self.canvases)}\n")
        lines.append(f"- **Permissions**: {', '.join(self.permissions)}\n")
        lines.append(f"- **User**: {self.user_name}\n")
        return "".join(lines)


def build_container_context(
    container_id: str = "local-test",
    container_name: str = "Local Test Container",
    canvases: list[str] | None = None,
    permissions: list[str] | None = None,
) -> ContainerContext:
    """
    Build ContainerContext from CLI args (stub).

    In the future, this could fetch from backend API.
    """
    return ContainerContext(
        container_id=container_id,
        container_name=container_name,
        canvases=canvases or [],
        permissions=permissions or ["read", "write"],
    )

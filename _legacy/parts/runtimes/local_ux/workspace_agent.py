"""
Workspace Agent Loader and Runner
=================================
Loads agent configuration from .agent/ hierarchy and runs interactive session.

Uses the Factory's AgentSpec pattern with hierarchy merging:
    Factory .agent/ → Workspace .agent/ → Application .agent/

Merge rules:
    - instructions: Override (last wins)
    - rules: Accumulate (all merged)
    - knowledge: Accumulate (all merged)
    - workflows: Accumulate (all merged)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import logfire
import yaml
from dotenv import load_dotenv
from rich.console import Console

# Add factory to path
FACTORY_ROOT = Path(os.getenv("FACTORY_ROOT", "D:/factory"))
if str(FACTORY_ROOT) not in sys.path:
    sys.path.insert(0, str(FACTORY_ROOT))

# Load API keys from secrets
_secrets_env = FACTORY_ROOT / "secrets" / "api_keys.env"
if _secrets_env.exists():
    load_dotenv(_secrets_env)

from parts.interfaces.cli_interface import DeepAgentCLI
from parts.templates.agent_spec import AgentSpec

from .context import WorkspaceContext, build_workspace_context

console = Console()


def find_agent_dirs(workspace_root: Path) -> list[Path]:
    """
    Find all .agent/ directories in the hierarchy from factory to workspace.

    Returns list ordered from most general (factory) to most specific (local).
    """
    seen: set[Path] = set()
    agent_dirs: list[Path] = []

    def add_if_new(path: Path) -> None:
        resolved = path.resolve()
        if resolved.exists() and resolved not in seen:
            seen.add(resolved)
            agent_dirs.append(resolved)

    # 1. Factory level (always included if exists)
    add_if_new(FACTORY_ROOT / ".agent")

    # 2. Walk up from workspace_root to find intermediate .agent/ dirs
    current = workspace_root.resolve()
    intermediate_dirs: list[Path] = []

    while current != FACTORY_ROOT.resolve() and current != current.parent:
        agent_dir = current / ".agent"
        if agent_dir.resolve() not in seen and agent_dir.exists():
            intermediate_dirs.append(agent_dir.resolve())
        current = current.parent

    # Add in order from factory-adjacent to workspace-local
    for d in reversed(intermediate_dirs):
        add_if_new(d)

    # 3. Workspace level (current directory) - skip if same as factory
    add_if_new(workspace_root / ".agent")

    return agent_dirs


def load_config_overrides(agent_dir: Path) -> dict[str, Any]:
    """Load local_ux.yaml config from an .agent/configs/ directory."""
    config_path = agent_dir / "configs" / "local_ux.yaml"
    if not config_path.exists():
        return {}

    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def merge_agent_specs(agent_dirs: list[Path]) -> AgentSpec:
    """
    Load and merge AgentSpec from multiple .agent/ directories.

    Merge rules:
        - instructions: Override (last wins)
        - rules: Accumulate (all merged)
        - knowledge: Accumulate (all merged, recursive)
        - workflows: Accumulate (all merged)
        - model/temperature: Override (last wins from configs)
    """
    # Start with base spec
    merged = AgentSpec(
        id="workspace-agent",
        name="Workspace Agent",
        model="google-gla:gemini-2.0-flash",
        temperature=0.7,
    )

    for agent_dir in agent_dirs:
        # Load spec from this directory
        spec = AgentSpec(
            id=agent_dir.name,
            name=agent_dir.name,
            agent_dir=agent_dir,
        ).load()

        # Apply merge rules
        if spec.instructions:
            merged.instructions = spec.instructions  # Override

        merged.rules.extend(spec.rules)  # Accumulate
        merged.workflows.extend(spec.workflows)  # Accumulate

        # Knowledge: recursive load from subdirectories
        knowledge_dir = agent_dir / "knowledge"
        if knowledge_dir.exists():
            for kb_file in sorted(knowledge_dir.rglob("*.md")):
                if kb_file.is_file() and not kb_file.name.startswith("_"):
                    try:
                        merged.knowledge.append(kb_file.read_text(encoding="utf-8"))
                    except (OSError, UnicodeDecodeError):
                        pass  # Skip unreadable files

        # Load config overrides
        config = load_config_overrides(agent_dir)
        if "model" in config:
            merged.model = config["model"]
        if "temperature" in config:
            merged.temperature = config["temperature"]

    return merged


def load_agent_hierarchy(workspace_root: Path) -> tuple[AgentSpec, list[Path]]:
    """
    Load and merge agent configuration from .agent/ hierarchy.

    Returns:
        Tuple of (merged AgentSpec, list of loaded .agent/ directories)
    """
    agent_dirs = find_agent_dirs(workspace_root)

    if not agent_dirs:
        console.print("[yellow]No .agent/ directories found in hierarchy[/]")
        return AgentSpec(
            id="workspace-agent",
            name="Workspace Agent",
            model="google-gla:gemini-2.0-flash",
        ), []

    spec = merge_agent_specs(agent_dirs)
    return spec, agent_dirs


def run_workspace_agent(
    workspace_root: Path,
    active_file: Path | None = None,
) -> None:
    """
    Run workspace agent in interactive mode.

    Args:
        workspace_root: Root directory of the workspace
        active_file: Currently active file (optional)
    """
    # Build workspace context
    context = build_workspace_context(workspace_root, active_file)

    # Load merged agent spec from hierarchy
    spec, agent_dirs = load_agent_hierarchy(workspace_root)

    logfire.info(
        "workspace_agent_started",
        workspace=str(workspace_root),
        model=spec.model,
        agent_dirs=[str(d) for d in agent_dirs],
    )

    # Create CLI from spec with workspace context
    cli = DeepAgentCLI.from_spec(
        spec,
        context_section=context.to_prompt_section(),
        name="Workspace Agent",
    )

    # Run interactive session
    cli.run(
        workspace=str(workspace_root),
        git_branch=context.git_branch or "N/A",
        model=spec.model,
        extra_info={
            "Loaded .agent/ dirs": "\n  " + "\n  ".join(f"• {d}" for d in agent_dirs),
            "Rules": f"{len(spec.rules)} files",
            "Knowledge": f"{len(spec.knowledge)} files",
            "Workflows": f"{len(spec.workflows)} files",
        },
    )


def main(workspace: str | None = None, active_file: str | None = None) -> None:
    """
    Entry point for workspace agent mode.

    Args:
        workspace: Workspace root path (defaults to cwd)
        active_file: Currently active file path
    """
    workspace_root = Path(workspace) if workspace else Path.cwd()
    active = Path(active_file) if active_file else None

    if not workspace_root.exists():
        console.print(f"[bold red]Error[/]: Workspace not found: {workspace_root}")
        sys.exit(1)

    run_workspace_agent(workspace_root, active)


if __name__ == "__main__":
    main()

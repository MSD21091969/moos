"""
Local UX CLI
============
Unified command-line interface for running workspace agents and pilots.

Usage:
    local-ux agent                    # Run workspace agent from cwd
    local-ux agent --workspace PATH   # Run from specific workspace
    local-ux pilot container          # Run pilot (stub)
    local-ux pilot studio             # Run pilot (stub)
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="local-ux")
def cli():
    """Local UX - Factory-level CLI for workspace agents and pilots."""
    pass


@cli.command()
@click.option(
    "--workspace",
    "-w",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Workspace root directory (defaults to current directory)",
)
@click.option(
    "--file",
    "-f",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    default=None,
    help="Active file for context",
)
def agent(workspace: Optional[Path], file: Optional[Path]):
    """
    Run a workspace agent.

    Loads configuration from .agent/ hierarchy (factory → workspace → application)
    and starts an interactive chat session.

    Examples:
        local-ux agent
        local-ux agent --workspace D:\\factory\\workspaces\\collider_apps
        local-ux agent -w . -f src/main.py
    """
    from .workspace_agent import main as run_agent

    workspace_root = workspace or Path.cwd()
    run_agent(str(workspace_root), str(file) if file else None)


@cli.command()
@click.argument("pilot_id", default="container")
@click.option(
    "--container-id",
    type=str,
    default=None,
    help="Container ID for context (future use)",
)
@click.option(
    "--container-name",
    type=str,
    default=None,
    help="Container name for context (future use)",
)
def pilot(pilot_id: str, container_id: Optional[str], container_name: Optional[str]):
    """
    Run a pilot agent (STUB - not yet implemented).

    Pilots work with Collider containers and canvases.
    This mode will be fully implemented in a future release.

    Available pilots: container, studio

    Examples:
        local-ux pilot container
        local-ux pilot studio
    """
    from .pilot_agent import run_pilot

    run_pilot(pilot_id, container_id=container_id, container_name=container_name)


@cli.command()
def info():
    """Show Local UX configuration and status."""
    import os

    from dotenv import load_dotenv
    from rich.table import Table

    factory_root = Path(os.getenv("FACTORY_ROOT", "D:/factory"))

    # Load secrets
    secrets_env = factory_root / "secrets" / "api_keys.env"
    if secrets_env.exists():
        load_dotenv(secrets_env)

    table = Table(title="Local UX Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("FACTORY_ROOT", str(factory_root))
    table.add_row("Factory .agent/", "✓" if (factory_root / ".agent").exists() else "✗")
    table.add_row("Current directory", str(Path.cwd()))
    table.add_row("Local .agent/", "✓" if (Path.cwd() / ".agent").exists() else "✗")

    # Check for config file
    config_path = factory_root / ".agent" / "configs" / "local_ux.yaml"
    table.add_row("Config file", "✓" if config_path.exists() else "✗ (using defaults)")

    # Check for API key
    api_key = os.getenv("GEMINI_API_KEY")
    table.add_row("GEMINI_API_KEY", "✓ (set)" if api_key else "✗ (missing)")

    console.print(table)


def main():
    """Entry point for the local-ux command."""
    cli()


if __name__ == "__main__":
    main()

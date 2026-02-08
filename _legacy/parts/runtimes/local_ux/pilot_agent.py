"""
Pilot Agent Runner
==================
Runs Collider pilots in local UX mode using ColliderPilotSpec.

Pilots work with container/canvas context from the Collider application.
They use the SDK's folder structure convention:
    pilots/{id}/
    ├── __init__.py      (PILOT_SPEC definition)
    ├── instructions.md  (system prompt)
    ├── rules/           (behavioral rules)
    ├── workflows/       (task sequences)
    └── knowledge/       (domain context)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Optional

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

from .context import ContainerContext, build_container_context

console = Console()

# Default pilots directory - configurable via env var, fallback to my-tiny-data-collider SDK
DEFAULT_PILOTS_DIR = Path(
    os.getenv(
        "COLLIDER_PILOTS_DIR",
        str(
            FACTORY_ROOT
            / "workspaces"
            / "collider_apps"
            / "applications"
            / "my-tiny-data-collider"
            / "shared"
            / "collider_sdk"
            / "pilots"
        ),
    )
)


def load_pilot_spec(pilot_id: str, pilots_dir: Optional[Path] = None):
    """
    Load pilot spec from the SDK.

    Args:
        pilot_id: Pilot identifier (e.g., "container", "studio")
        pilots_dir: Directory containing pilot folders

    Returns:
        ColliderPilotSpec instance
    """
    pilots_dir = pilots_dir or DEFAULT_PILOTS_DIR

    # Add collider app to path (parent of shared/)
    app_path = pilots_dir.parent.parent.parent  # my-tiny-data-collider/
    if str(app_path) not in sys.path:
        sys.path.insert(0, str(app_path))

    # Import from SDK
    from shared.collider_sdk.pilots import load_pilot

    return load_pilot(pilot_id, pilots_dir)


def run_pilot(
    pilot_id: str,
    container_id: Optional[str] = None,
    container_name: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """
    Run a pilot in local UX mode.

    Args:
        pilot_id: The pilot to run (e.g., "container", "studio")
        container_id: Container ID for context
        container_name: Container name for context
        **kwargs: Additional context fields
    """
    try:
        # Load pilot spec from SDK
        spec = load_pilot_spec(pilot_id)

        # Build container context
        context = build_container_context(
            container_id=container_id or "local-test",
            container_name=container_name or "Local Test Container",
            canvases=kwargs.get("canvases", []),
            permissions=kwargs.get("permissions", ["read", "write"]),
        )

        # Inject context into spec
        spec.with_container_context(context.__dict__)

        # Create CLI from spec
        cli = DeepAgentCLI.from_spec(
            spec,
            name=spec.name,
        )

        # Run interactive session
        cli.run(
            model=spec.model,
            extra_info={
                "Container": context.container_name,
                "Container ID": context.container_id,
                "Canvases": str(len(context.canvases)),
                "Permissions": ", ".join(context.permissions),
            },
        )

    except (ImportError, ValueError) as e:
        # SDK not available or pilot not found - show helpful message
        console.print(
            f"[bold red]Error loading pilot '{pilot_id}'[/]: {e}\n\n"
            f"[yellow]Make sure the Collider SDK is available at:[/]\n"
            f"  {DEFAULT_PILOTS_DIR}\n\n"
            f"[dim]Available pilots: container, studio[/]"
        )


def main(pilot_id: str = "container") -> None:
    """Entry point for pilot mode."""
    run_pilot(pilot_id)


if __name__ == "__main__":
    main()

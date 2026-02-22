"""ffs0-seed CLI — sync .agent/ hierarchy into ColliderDataServer DB nodes.

Usage:
    uv run ffs0-seed --root D:/FFS0_Factory --app-id <uuid>
    uv run ffs0-seed --help

Required environment variables (or pass as flags):
    COLLIDER_DATA_SERVER_URL  e.g. http://localhost:8000
    COLLIDER_USERNAME         e.g. superadmin
    COLLIDER_PASSWORD         (the superadmin password)
"""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

import click

from .agent_walker import discover_workspaces
from .node_upserter import NodeUpserter


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        format="%(levelname)s  %(message)s",
        level=level,
    )


@click.command("ffs0-seed")
@click.option(
    "--root",
    default=str(Path(__file__).parents[3]),  # D:/FFS0_Factory
    show_default=True,
    help="Monorepo root containing .agent/ directories to walk.",
)
@click.option(
    "--app-id",
    required=True,
    envvar="COLLIDER_APP_ID",
    help="Target ColliderDataServer Application UUID.",
)
@click.option(
    "--data-server-url",
    default=lambda: os.environ.get("COLLIDER_DATA_SERVER_URL", "http://localhost:8000"),
    show_default="$COLLIDER_DATA_SERVER_URL or http://localhost:8000",
    help="Base URL of the ColliderDataServer.",
)
@click.option(
    "--username",
    default=lambda: os.environ.get("COLLIDER_USERNAME", "superadmin"),
    show_default="$COLLIDER_USERNAME",
    help="ColliderDataServer login username.",
)
@click.option(
    "--password",
    default=lambda: os.environ.get("COLLIDER_PASSWORD", ""),
    show_default="$COLLIDER_PASSWORD",
    help="ColliderDataServer login password.",
)
@click.option(
    "--graph-server-url",
    default=lambda: os.environ.get("COLLIDER_GRAPH_SERVER_URL", "http://localhost:8001"),
    show_default="$COLLIDER_GRAPH_SERVER_URL or http://localhost:8001",
    help="Base URL of the ColliderGraphToolServer (for tool registration).",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Print what would be done without making any API calls.",
)
@click.option("--verbose", "-v", is_flag=True, default=False, help="Debug logging.")
def main(
    root: str,
    app_id: str,
    data_server_url: str,
    username: str,
    password: str,
    graph_server_url: str,
    dry_run: bool,
    verbose: bool,
) -> None:
    """Sync .agent/ workspace hierarchy into ColliderDataServer DB nodes."""
    _setup_logging(verbose)
    log = logging.getLogger("ffs0-seed")

    root_path = Path(root).resolve()
    if not root_path.exists():
        raise click.ClickException(f"Root path does not exist: {root_path}")

    log.info("Discovering .agent/ workspaces under %s …", root_path)
    workspaces = discover_workspaces(root_path)

    if not workspaces:
        log.warning("No .agent/ directories found under %s", root_path)
        return

    log.info("Found %d workspace(s):", len(workspaces))
    for ws in workspaces:
        parent_label = ws.parent_node_path or "(root)"
        log.info(
            "  %-50s  parent=%-30s  inst=%d rules=%d know=%d skills=%d",
            ws.node_path,
            parent_label,
            len(ws.instructions),
            len(ws.rules),
            len(ws.knowledge),
            len(ws.skills),
        )

    if dry_run:
        log.info("--- DRY RUN — no API calls will be made ---")

    upserter = NodeUpserter(
        data_server_url=data_server_url,
        username=username,
        password=password,
        app_id=app_id,
        dry_run=dry_run,
        graph_server_url=graph_server_url,
    )

    result = asyncio.run(upserter.upsert_all(workspaces))

    if not dry_run:
        log.info("Done. Upserted %d node(s):", len(result))
        for path, node_id in sorted(result.items()):
            log.info("  %s  →  %s", path, node_id)
    else:
        log.info("Dry run complete — %d node(s) would be upserted.", len(workspaces))


if __name__ == "__main__":
    main()

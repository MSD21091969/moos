"""agent_walker — discover .agent/ directories and extract NodeContainer payloads.

Walks a filesystem tree rooted at a given path, finds every directory containing
a ``.agent/manifest.yaml``, reads all context files, and returns a list of
``AgentWorkspace`` objects ordered parent-first (BFS from root).

Context file mapping (mirrors NodeContainer fields):
  - ``.agent/instructions/*.md``  →  ``container.instructions``
  - ``.agent/rules/*.md``         →  ``container.rules``
  - ``.agent/knowledge/**/*.md``  →  ``container.knowledge``
  - ``.agent/skills/*.md``        →  ``container.skills`` (SkillDefinition stubs)
  - ``.agent/tools/*.json``       →  ``container.tools`` (ToolDefinition dicts)
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class AgentWorkspace:
    """A single ``.agent/``-bearing directory with its parsed context."""

    abs_path: Path
    """Absolute path to the workspace directory (parent of ``.agent/``)."""

    node_path: str
    """Logical dot-separated path used as the DB node path, e.g. ``factory/ffs1/ffs2``."""

    manifest_name: str
    """``name`` from ``manifest.yaml``, or slugified directory name."""

    instructions: list[str]
    """Contents of ``.agent/instructions/*.md``, in alphabetical order."""

    rules: list[str]
    """Contents of ``.agent/rules/*.md``, in alphabetical order."""

    knowledge: list[str]
    """Contents of ``.agent/knowledge/**/*.md`` (non-index, non-archive), sorted."""

    skills: list[dict[str, Any]]
    """SkillDefinition dicts parsed from ``.agent/skills/*.md`` (name + markdown_body)."""

    tools: list[dict[str, Any]]
    """ToolDefinition dicts parsed from ``.agent/tools/*.json`` arrays."""

    parent_node_path: str | None = None
    """``node_path`` of the parent AgentWorkspace, or ``None`` for the root."""


def _slugify(name: str) -> str:
    """Convert a directory or manifest name to a lowercase slug."""
    slug = name.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def _read_md_files(directory: Path, recursive: bool = False) -> list[str]:
    """Read all non-index ``.md`` files from a directory.

    Args:
        directory: The directory to scan.
        recursive: If True, walk subdirectories (skips ``_archive*`` dirs).

    Returns:
        List of file contents in sorted order, skipping ``_index.md`` and empty
        files, and skipping paths containing ``_archive``.
    """
    if not directory.exists():
        return []

    if recursive:
        md_files = sorted(
            p for p in directory.rglob("*.md")
            if "_archive" not in str(p) and p.name != "_index.md"
        )
    else:
        md_files = sorted(
            p for p in directory.glob("*.md")
            if p.name != "_index.md"
        )

    contents = []
    for f in md_files:
        try:
            text = f.read_text(encoding="utf-8").strip()
            if text:
                contents.append(text)
        except OSError:
            pass
    return contents


def _parse_tool_files(tools_dir: Path) -> list[dict[str, Any]]:
    """Parse ``.agent/tools/*.json`` files into ToolDefinition-compatible dicts.

    Each JSON file must be a JSON array of ToolDefinition objects, each with
    at minimum ``name``, ``description``, ``params_schema``, and ``code_ref``.

    Args:
        tools_dir: Path to the ``.agent/tools/`` directory.

    Returns:
        Flat list of ToolDefinition dicts from all JSON files, in sorted order.
    """
    if not tools_dir.exists():
        return []

    import logging as _logging
    tools: list[dict[str, Any]] = []
    for tool_file in sorted(tools_dir.glob("*.json")):
        try:
            raw = tool_file.read_text(encoding="utf-8").strip()
            if not raw:
                continue
            data: Any = json.loads(raw)
            if isinstance(data, list):
                tools.extend(data)
            elif isinstance(data, dict):
                tools.append(data)
        except (OSError, json.JSONDecodeError) as exc:
            _logging.getLogger(__name__).warning(
                "Skipping malformed tool file %s: %s", tool_file, exc
            )
    return tools


def _parse_skill_files(skills_dir: Path) -> list[dict[str, Any]]:
    """Parse ``.agent/skills/*.md`` files into SkillDefinition-compatible dicts.

    Each skill file is treated as a markdown_body.  The skill name is derived
    from the filename (without extension), slugified.

    Args:
        skills_dir: Path to the ``.agent/skills/`` directory.

    Returns:
        List of ``{name, description, markdown_body}`` dicts.
    """
    if not skills_dir.exists():
        return []

    skills: list[dict[str, Any]] = []
    for skill_file in sorted(skills_dir.glob("*.md")):
        if skill_file.name.startswith("_"):
            continue
        try:
            body = skill_file.read_text(encoding="utf-8").strip()
            if not body:
                continue
            name = _slugify(skill_file.stem)
            # Extract first non-empty line as description
            first_line = next((l.lstrip("# ").strip() for l in body.splitlines() if l.strip()), name)
            skills.append({
                "name": name,
                "description": first_line[:200],
                "markdown_body": body,
            })
        except OSError:
            pass
    return skills


def _build_node_path(workspace_abs: Path, root_abs: Path, manifest_name: str) -> str:
    """Derive the logical node path from the filesystem path.

    Example:
        root = /D/FFS0_Factory, workspace = /D/FFS0_Factory → "factory"
        workspace = /D/FFS0_Factory/workspaces/FFS1_ColliderDataSystems → "factory/ffs1"

    The last segment always uses the ``manifest_name`` (slugified) from the
    workspace's own manifest to produce a stable, readable path.  Parent segments
    use the slugified directory names.
    """
    try:
        rel = workspace_abs.relative_to(root_abs)
    except ValueError:
        return _slugify(manifest_name)

    parts = list(rel.parts)  # may be empty for root itself
    if not parts:
        return _slugify(manifest_name)

    # Use slugified directory names for intermediate segments, manifest name for leaf
    segments = [_slugify(p) for p in parts[:-1]] + [_slugify(manifest_name)]
    # Prepend root slug
    root_slug = _slugify(root_abs.name)
    return "/".join([root_slug] + segments)


def discover_workspaces(root: Path) -> list[AgentWorkspace]:
    """Discover all ``.agent/``-bearing directories under ``root``.

    Returns ``AgentWorkspace`` objects ordered breadth-first (root first,
    deeper workspaces after their parents) so the caller can upsert nodes in
    the correct parent-before-child order.

    Args:
        root: Absolute path to the monorepo root (e.g. ``D:/FFS0_Factory``).

    Returns:
        List of ``AgentWorkspace`` instances, sorted by depth ascending.
    """
    root = root.resolve()

    _SKIP_DIRS = frozenset({"node_modules", ".venv", ".git", "__pycache__", "build", "dist"})

    # Find all dirs that have a .agent/manifest.yaml, skipping junk directories
    candidate_dirs: list[Path] = []
    for manifest in sorted(root.rglob(".agent/manifest.yaml")):
        # Skip if any path component is in the exclusion set
        if any(part in _SKIP_DIRS for part in manifest.parts):
            continue
        workspace_dir = manifest.parent.parent  # .agent/ → workspace dir
        candidate_dirs.append(workspace_dir)

    # Sort by depth (shorter path = parent first)
    candidate_dirs.sort(key=lambda p: len(p.parts))

    workspaces: list[AgentWorkspace] = []
    path_to_workspace: dict[str, AgentWorkspace] = {}

    for workspace_dir in candidate_dirs:
        agent_dir = workspace_dir / ".agent"
        manifest_path = agent_dir / "manifest.yaml"

        try:
            manifest_raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
        except Exception:  # noqa: BLE001
            manifest_raw = {}

        manifest_name: str = (
            manifest_raw.get("name")
            or manifest_raw.get("display_name")
            or workspace_dir.name
        )

        node_path = _build_node_path(workspace_dir, root, manifest_name)

        # Determine parent node_path by finding the closest ancestor workspace
        parent_node_path: str | None = None
        for ancestor_path in sorted(
            path_to_workspace.keys(),
            key=lambda p: len(p),
            reverse=True,
        ):
            try:
                workspace_dir.relative_to(
                    path_to_workspace[ancestor_path].abs_path
                )
                parent_node_path = ancestor_path
                break
            except ValueError:
                continue

        ws = AgentWorkspace(
            abs_path=workspace_dir,
            node_path=node_path,
            manifest_name=manifest_name,
            instructions=_read_md_files(agent_dir / "instructions"),
            rules=_read_md_files(agent_dir / "rules"),
            knowledge=_read_md_files(agent_dir / "knowledge", recursive=True),
            skills=_parse_skill_files(agent_dir / "skills"),
            tools=_parse_tool_files(agent_dir / "tools"),
            parent_node_path=parent_node_path,
        )
        workspaces.append(ws)
        path_to_workspace[node_path] = ws

    return workspaces

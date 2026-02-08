"""
Manifest Inheritance System
Implements cascading inheritance for .agent containers through node hierarchy.

Inheritance Rules:
- Child inherits from parent
- Child can override parent values
- Lists are merged (child extends parent)
- Dicts are deep-merged (child overrides parent keys)
- Special keys:
  - `_inherit: false` - disable inheritance for this container
  - `_override: true` on a list item - replace instead of merge
"""

from typing import Any
from dataclasses import dataclass


@dataclass
class InheritanceConfig:
    """Configuration for inheritance behavior."""

    merge_lists: bool = True  # Append child lists to parent
    merge_dicts: bool = True  # Deep merge dicts
    allow_override: bool = True  # Allow _override flags


def deep_merge(
    parent: dict, child: dict, config: InheritanceConfig | None = None
) -> dict:
    """
    Deep merge two dictionaries with inheritance semantics.

    Args:
        parent: Parent dictionary (lower priority)
        child: Child dictionary (higher priority)
        config: Inheritance configuration

    Returns:
        Merged dictionary
    """
    if config is None:
        config = InheritanceConfig()

    # Check if child explicitly disables inheritance
    if child.get("_inherit") is False:
        return {k: v for k, v in child.items() if not k.startswith("_")}

    result = {}

    # Start with parent values
    for key, parent_val in parent.items():
        if key.startswith("_"):
            continue  # Skip meta keys

        if key in child:
            child_val = child[key]
            result[key] = _merge_values(parent_val, child_val, config)
        else:
            result[key] = _deep_copy(parent_val)

    # Add child-only values
    for key, child_val in child.items():
        if key.startswith("_"):
            continue
        if key not in parent:
            result[key] = _deep_copy(child_val)

    return result


def _merge_values(parent_val: Any, child_val: Any, config: InheritanceConfig) -> Any:
    """Merge two values based on their types."""

    # Check for override flag on child
    if isinstance(child_val, dict) and child_val.get("_override"):
        return {k: v for k, v in child_val.items() if k != "_override"}

    # Both dicts: deep merge
    if (
        isinstance(parent_val, dict)
        and isinstance(child_val, dict)
        and config.merge_dicts
    ):
        return deep_merge(parent_val, child_val, config)

    # Both lists: merge or replace
    if (
        isinstance(parent_val, list)
        and isinstance(child_val, list)
        and config.merge_lists
    ):
        return _merge_lists(parent_val, child_val)

    # Different types or no merge: child wins
    return _deep_copy(child_val)


def _merge_lists(parent_list: list, child_list: list) -> list:
    """
    Merge two lists.

    Strategy:
    - Items with "_override" flag replace parent items with same id/name
    - Other items are appended
    """
    result = list(parent_list)  # Copy parent

    for child_item in child_list:
        if isinstance(child_item, dict):
            # Check for override
            if child_item.get("_override"):
                item_id = child_item.get("id") or child_item.get("name")
                if item_id:
                    # Find and replace in parent
                    for i, parent_item in enumerate(result):
                        if isinstance(parent_item, dict):
                            if (
                                parent_item.get("id") == item_id
                                or parent_item.get("name") == item_id
                            ):
                                result[i] = {
                                    k: v
                                    for k, v in child_item.items()
                                    if k != "_override"
                                }
                                break
                    else:
                        # Not found, append without override flag
                        result.append(
                            {k: v for k, v in child_item.items() if k != "_override"}
                        )
                    continue

        # Default: append
        result.append(_deep_copy(child_item))

    return result


def _deep_copy(value: Any) -> Any:
    """Create a deep copy of a value."""
    if isinstance(value, dict):
        return {k: _deep_copy(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_deep_copy(item) for item in value]
    return value


def resolve_container(
    node_path: str,
    containers: dict[str, dict],
    config: InheritanceConfig | None = None,
) -> dict:
    """
    Resolve a node's container by walking up the path and merging.

    Args:
        node_path: Path like "/app/dashboard/settings"
        containers: Dict mapping paths to containers
        config: Inheritance configuration

    Returns:
        Fully resolved container with inheritance applied

    Example:
        containers = {
            "/": {"instructions": ["Be helpful"]},
            "/app": {"instructions": ["For this app..."], "tools": [...]},
            "/app/dashboard": {"tools": [{"id": "chart", ...}]},
        }

        resolve_container("/app/dashboard", containers)
        # Returns merged container with all ancestor contributions
    """
    if config is None:
        config = InheritanceConfig()

    # Build ancestry path (root to leaf)
    ancestry = []
    parts = node_path.strip("/").split("/") if node_path != "/" else []

    # Root is always first
    ancestry.append("/")

    # Build intermediate paths
    current = ""
    for part in parts:
        current = f"{current}/{part}"
        ancestry.append(current)

    # Merge from root to leaf
    result = {}
    for path in ancestry:
        if path in containers:
            container = containers[path]
            result = deep_merge(result, container, config)

    return result


async def resolve_node_container(
    node_id: str,
    db_session,
) -> dict:
    """
    Resolve a node's container from the database with inheritance.

    Args:
        node_id: UUID of the node
        db_session: SQLAlchemy async session

    Returns:
        Fully resolved container
    """
    from sqlalchemy import select
    from src.db import Node

    # Get the target node
    result = await db_session.execute(select(Node).where(Node.id == node_id))
    node = result.scalar_one_or_none()

    if not node:
        return {}

    # Get all nodes in the same application
    all_nodes_result = await db_session.execute(
        select(Node).where(Node.application_id == node.application_id)
    )
    all_nodes = all_nodes_result.scalars().all()

    # Build containers dict
    containers = {n.path: n.container for n in all_nodes}

    # Resolve inheritance
    return resolve_container(node.path, containers)


def get_effective_instructions(container: dict) -> list[str]:
    """Extract all effective instructions from a resolved container."""
    return container.get("instructions", [])


def get_effective_tools(container: dict) -> list[dict]:
    """Extract all effective tools from a resolved container."""
    return container.get("tools", [])


def get_effective_rules(container: dict) -> list[str]:
    """Extract all effective rules from a resolved container."""
    return container.get("rules", [])


def get_effective_secrets(container: dict) -> list[str]:
    """
    Extract secret references from a resolved container.
    Returns list of secret names that need to be injected.
    """
    secrets = []

    # Check manifest for secret refs
    manifest = container.get("manifest", {})
    for key, value in manifest.items():
        if isinstance(value, str) and value.startswith("${secret:"):
            # Extract secret name from ${secret:NAME}
            secret_name = value[9:-1]  # Remove ${secret: and }
            secrets.append(secret_name)

    # Check configs for secret refs
    configs = container.get("configs", {})
    secrets.extend(_find_secret_refs(configs))

    return list(set(secrets))


def _find_secret_refs(obj: Any, refs: list | None = None) -> list[str]:
    """Recursively find ${secret:...} references in an object."""
    if refs is None:
        refs = []

    if isinstance(obj, str):
        if obj.startswith("${secret:") and obj.endswith("}"):
            refs.append(obj[9:-1])
    elif isinstance(obj, dict):
        for value in obj.values():
            _find_secret_refs(value, refs)
    elif isinstance(obj, list):
        for item in obj:
            _find_secret_refs(item, refs)

    return refs

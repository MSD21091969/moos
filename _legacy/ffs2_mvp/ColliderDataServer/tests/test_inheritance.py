"""Tests for manifest inheritance module."""

import pytest

from src.inheritance import (
    deep_merge,
    resolve_container,
    InheritanceConfig,
    get_effective_instructions,
    get_effective_tools,
    get_effective_secrets,
)


class TestDeepMerge:
    """Test deep_merge function."""

    def test_child_overrides_parent_scalar(self):
        parent = {"name": "parent", "version": "1.0"}
        child = {"name": "child"}

        result = deep_merge(parent, child)

        assert result["name"] == "child"
        assert result["version"] == "1.0"

    def test_lists_are_merged(self):
        parent = {"items": ["a", "b"]}
        child = {"items": ["c"]}

        result = deep_merge(parent, child)

        assert result["items"] == ["a", "b", "c"]

    def test_dicts_are_deep_merged(self):
        parent = {"config": {"host": "localhost", "port": 8000}}
        child = {"config": {"port": 9000}}

        result = deep_merge(parent, child)

        assert result["config"]["host"] == "localhost"
        assert result["config"]["port"] == 9000

    def test_inherit_false_disables_inheritance(self):
        parent = {"instructions": ["be helpful"], "tools": ["search"]}
        child = {"_inherit": False, "instructions": ["custom only"]}

        result = deep_merge(parent, child)

        assert result["instructions"] == ["custom only"]
        assert "tools" not in result

    def test_override_flag_replaces_list_item(self):
        parent = {"tools": [{"id": "search", "url": "old.com"}]}
        child = {"tools": [{"id": "search", "url": "new.com", "_override": True}]}

        result = deep_merge(parent, child)

        assert len(result["tools"]) == 1
        assert result["tools"][0]["url"] == "new.com"
        assert "_override" not in result["tools"][0]

    def test_child_adds_new_keys(self):
        parent = {"a": 1}
        child = {"b": 2}

        result = deep_merge(parent, child)

        assert result == {"a": 1, "b": 2}

    def test_empty_parent(self):
        parent = {}
        child = {"key": "value"}

        result = deep_merge(parent, child)

        assert result == {"key": "value"}

    def test_empty_child(self):
        parent = {"key": "value"}
        child = {}

        result = deep_merge(parent, child)

        assert result == {"key": "value"}


class TestResolveContainer:
    """Test resolve_container function."""

    def test_root_only(self):
        containers = {"/": {"instructions": ["root instruction"]}}

        result = resolve_container("/", containers)

        assert result["instructions"] == ["root instruction"]

    def test_single_level_inheritance(self):
        containers = {
            "/": {"instructions": ["root"]},
            "/app": {"instructions": ["app"]},
        }

        result = resolve_container("/app", containers)

        assert result["instructions"] == ["root", "app"]

    def test_multi_level_inheritance(self):
        containers = {
            "/": {"rules": ["rule1"]},
            "/app": {"rules": ["rule2"]},
            "/app/dashboard": {"rules": ["rule3"]},
        }

        result = resolve_container("/app/dashboard", containers)

        assert result["rules"] == ["rule1", "rule2", "rule3"]

    def test_missing_intermediate_node(self):
        containers = {
            "/": {"instructions": ["root"]},
            "/app/dashboard": {"instructions": ["dashboard"]},
        }

        # /app doesn't exist, but /app/dashboard inherits from /
        result = resolve_container("/app/dashboard", containers)

        assert result["instructions"] == ["root", "dashboard"]

    def test_path_not_in_containers(self):
        containers = {
            "/": {"instructions": ["root"]},
        }

        result = resolve_container("/nonexistent", containers)

        # Should still get root inheritance
        assert result["instructions"] == ["root"]

    def test_complex_hierarchy(self):
        containers = {
            "/": {
                "instructions": ["Be helpful"],
                "tools": [{"id": "search"}],
            },
            "/myapp": {
                "instructions": ["For MyApp..."],
                "tools": [{"id": "analyze"}],
                "configs": {"theme": "dark"},
            },
            "/myapp/settings": {
                "instructions": ["For settings page"],
                "configs": {"theme": "light"},  # Override
            },
        }

        result = resolve_container("/myapp/settings", containers)

        assert result["instructions"] == [
            "Be helpful",
            "For MyApp...",
            "For settings page",
        ]
        assert len(result["tools"]) == 2
        assert result["configs"]["theme"] == "light"


class TestGetEffectiveHelpers:
    """Test helper functions for extracting resolved values."""

    def test_get_effective_instructions(self):
        container = {"instructions": ["a", "b"], "other": "stuff"}

        result = get_effective_instructions(container)

        assert result == ["a", "b"]

    def test_get_effective_instructions_empty(self):
        container = {"other": "stuff"}

        result = get_effective_instructions(container)

        assert result == []

    def test_get_effective_tools(self):
        container = {"tools": [{"id": "search"}, {"id": "analyze"}]}

        result = get_effective_tools(container)

        assert len(result) == 2
        assert result[0]["id"] == "search"

    def test_get_effective_secrets(self):
        container = {
            "manifest": {
                "api_key": "${secret:OPENAI_API_KEY}",
                "normal": "value",
            },
            "configs": {
                "nested": {
                    "token": "${secret:GITHUB_TOKEN}",
                }
            },
        }

        result = get_effective_secrets(container)

        assert "OPENAI_API_KEY" in result
        assert "GITHUB_TOKEN" in result
        assert len(result) == 2

"""
Tests for Workspace Settings Loader
===================================
Tests the settings hierarchy and config merging.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Use package imports to match production code paths
from agent_factory.parts.config.settings import (
    load_workspace_settings,
    find_factory_root,
    load_yaml_config,
    load_secrets,
    collect_agent_dirs,
    WorkspaceSettings,
    UserConfig,
    ProviderConfig,
)


class TestFindFactoryRoot:
    """Tests for find_factory_root function."""

    def test_finds_factory_from_env(self, monkeypatch):
        """Should use FACTORY_ROOT env var if set."""
        monkeypatch.setenv("FACTORY_ROOT", "/custom/factory")
        result = find_factory_root()
        assert result == Path("/custom/factory")

    def test_finds_factory_from_manifest(self, tmp_path):
        """Should find root by manifest.yaml with includes: []."""
        # Create factory structure
        factory = tmp_path / "factory"
        factory.mkdir()
        agent_dir = factory / ".agent"
        agent_dir.mkdir()
        (agent_dir / "manifest.yaml").write_text("includes: []")

        # Create child workspace
        workspace = factory / "workspaces" / "test"
        workspace.mkdir(parents=True)

        with patch.dict("os.environ", {}, clear=True):
            result = find_factory_root(workspace)

        assert result == factory

    def test_returns_none_if_not_found(self, tmp_path, monkeypatch):
        """Should return None if no factory root found."""
        monkeypatch.delenv("FACTORY_ROOT", raising=False)
        result = find_factory_root(tmp_path)
        assert result is None


class TestLoadYamlConfig:
    """Tests for YAML config loading."""

    def test_loads_valid_yaml(self, tmp_path):
        """Should load valid YAML file."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("key: value\nlist:\n  - item1\n  - item2")

        result = load_yaml_config(config_file)

        assert result == {"key": "value", "list": ["item1", "item2"]}

    def test_returns_empty_dict_for_missing_file(self, tmp_path):
        """Should return empty dict if file doesn't exist."""
        result = load_yaml_config(tmp_path / "nonexistent.yaml")
        assert result == {}

    def test_returns_empty_dict_for_empty_file(self, tmp_path):
        """Should return empty dict for empty YAML file."""
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("")

        result = load_yaml_config(config_file)
        assert result == {}


class TestLoadSecrets:
    """Tests for secrets loading from .env files."""

    def test_loads_secrets_from_env_file(self, tmp_path):
        """Should load secrets from api_keys.env."""
        secrets_dir = tmp_path / "secrets"
        secrets_dir.mkdir()
        (secrets_dir / "api_keys.env").write_text(
            "GEMINI_API_KEY=test-key-123\nOPENAI_API_KEY=sk-test"
        )

        result = load_secrets(secrets_dir)

        assert result["GEMINI_API_KEY"] == "test-key-123"
        assert result["OPENAI_API_KEY"] == "sk-test"

    def test_returns_empty_if_no_file(self, tmp_path):
        """Should return empty dict if no api_keys.env."""
        secrets_dir = tmp_path / "secrets"
        secrets_dir.mkdir()

        result = load_secrets(secrets_dir)
        assert result == {}


class TestCollectAgentDirs:
    """Tests for .agent/ directory collection."""

    def test_collects_hierarchy(self, tmp_path):
        """Should collect .agent dirs from child to factory."""
        # Create hierarchy
        factory = tmp_path / "factory"
        factory.mkdir()
        (factory / ".agent").mkdir()

        workspace = factory / "workspaces" / "test"
        workspace.mkdir(parents=True)
        (workspace / ".agent").mkdir()

        app = workspace / "apps" / "myapp"
        app.mkdir(parents=True)
        (app / ".agent").mkdir()

        result = collect_agent_dirs(app, factory)

        # Should be ordered factory → workspace → app
        assert len(result) == 3
        assert result[0] == factory / ".agent"
        assert result[1] == workspace / ".agent"
        assert result[2] == app / ".agent"

    def test_skips_dirs_without_agent(self, tmp_path):
        """Should skip directories without .agent folder."""
        factory = tmp_path / "factory"
        factory.mkdir()
        (factory / ".agent").mkdir()

        # No .agent in workspace
        workspace = factory / "workspaces" / "test"
        workspace.mkdir(parents=True)

        app = workspace / "apps" / "myapp"
        app.mkdir(parents=True)
        (app / ".agent").mkdir()

        result = collect_agent_dirs(app, factory)

        assert len(result) == 2
        assert result[0] == factory / ".agent"
        assert result[1] == app / ".agent"


class TestWorkspaceSettings:
    """Tests for WorkspaceSettings model."""

    def test_get_secret_from_environment(self, monkeypatch):
        """Should prefer environment variable over file."""
        monkeypatch.setenv("TEST_KEY", "env-value")

        settings = WorkspaceSettings(
            factory_root=Path("/factory"),
            secrets_dir=Path("/factory/secrets"),
        )
        settings._secrets = {"TEST_KEY": "file-value"}

        result = settings.get_secret("TEST_KEY")
        assert result == "env-value"

    def test_get_secret_from_file(self):
        """Should use file value if no env var."""
        settings = WorkspaceSettings(
            factory_root=Path("/factory"),
            secrets_dir=Path("/factory/secrets"),
        )
        settings._secrets = {"TEST_KEY": "file-value"}

        with patch.dict("os.environ", {}, clear=True):
            result = settings.get_secret("TEST_KEY")

        assert result == "file-value"

    def test_get_secret_returns_none(self):
        """Should return None if secret not found."""
        settings = WorkspaceSettings(
            factory_root=Path("/factory"),
            secrets_dir=Path("/factory/secrets"),
        )

        with patch.dict("os.environ", {}, clear=True):
            result = settings.get_secret("NONEXISTENT")

        assert result is None

    def test_get_user(self):
        """Should get user by email."""
        settings = WorkspaceSettings(
            factory_root=Path("/factory"),
            secrets_dir=Path("/factory/secrets"),
            users={
                "test@example.com": UserConfig(role="admin", display_name="Test User")
            },
        )

        user = settings.get_user("test@example.com")

        assert user is not None
        assert user.role == "admin"
        assert user.display_name == "Test User"

    def test_get_model_string(self):
        """Should format model string correctly."""
        settings = WorkspaceSettings(
            factory_root=Path("/factory"),
            secrets_dir=Path("/factory/secrets"),
            default_provider="gemini",
            default_model="gemini-2.0-flash",
            api_providers={
                "gemini": ProviderConfig(name="Gemini", default_model="gemini-2.5-pro")
            },
        )

        # Default
        assert settings.get_model_string() == "gemini:gemini-2.5-pro"

        # Override model
        assert (
            settings.get_model_string(model="gemini-2.0-flash")
            == "gemini:gemini-2.0-flash"
        )

        # Override provider
        assert settings.get_model_string(provider="openai") == "openai:gemini-2.0-flash"


class TestLoadWorkspaceSettings:
    """Integration tests for load_workspace_settings."""

    def test_loads_from_real_factory(self):
        """Should load settings from actual factory structure."""
        factory_root = Path(__file__).parent.parent.parent

        # Only run if we're in actual factory
        if not (factory_root / ".agent" / "configs" / "users.yaml").exists():
            pytest.skip("Not running in factory structure")

        settings = load_workspace_settings(factory_root, factory_root)

        # Check users loaded
        assert "superuser@test.com" in settings.users
        assert settings.users["superuser@test.com"].role == "superuser"

        # Check providers loaded
        assert "gemini" in settings.api_providers
        assert "ollama" in settings.api_providers

        # Check defaults
        assert settings.default_provider == "gemini"

    def test_merges_child_overrides(self, tmp_path):
        """Should merge child configs over parent."""
        # Create factory
        factory = tmp_path / "factory"
        factory.mkdir()
        agent_dir = factory / ".agent"
        agent_dir.mkdir()
        (agent_dir / "manifest.yaml").write_text("includes: []")
        configs_dir = agent_dir / "configs"
        configs_dir.mkdir()
        (configs_dir / "users.yaml").write_text("""
default_password: factory123
users:
  admin@test.com:
    role: admin
    display_name: Factory Admin
""")

        # Create workspace with override
        workspace = factory / "workspace"
        workspace.mkdir()
        ws_agent = workspace / ".agent"
        ws_agent.mkdir()
        ws_configs = ws_agent / "configs"
        ws_configs.mkdir()
        (ws_configs / "users.yaml").write_text("""
users:
  admin@test.com:
    display_name: Workspace Admin
  user@test.com:
    role: user
""")

        # Create secrets dir
        secrets = factory / "secrets"
        secrets.mkdir()

        with patch.dict("os.environ", {}, clear=True):
            settings = load_workspace_settings(workspace, factory)

        # Factory password should be used
        assert settings.default_password == "factory123"

        # Admin display_name should be overridden
        assert settings.users["admin@test.com"].display_name == "Workspace Admin"

        # New user should be added
        assert "user@test.com" in settings.users

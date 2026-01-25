"""
Workspace Settings Loader
=========================
Unified settings management for Factory workspaces.

Walks the .agent/ hierarchy from cwd to factory root, merging configs.
Loads secrets from factory/secrets/ (never committed).

Usage:
    from agent_factory.parts.config.settings import load_workspace_settings

    settings = load_workspace_settings()

    # Access merged configs
    users = settings.users  # From .agent/configs/users.yaml
    providers = settings.api_providers  # From .agent/configs/api_providers.yaml

    # Access secrets (from factory/secrets/)
    api_key = settings.get_secret("GEMINI_API_KEY")
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field
from dotenv import dotenv_values


class UserConfig(BaseModel):
    """User configuration from users.yaml."""

    role: str = "user"
    display_name: str = ""
    clients: list[str] = Field(default_factory=list)
    permissions: dict[str, list[str]] = Field(default_factory=dict)
    preferences: dict[str, Any] = Field(default_factory=dict)


class ProviderConfig(BaseModel):
    """API provider configuration."""

    name: str
    base_url: Optional[str] = None
    env_key: Optional[str] = None
    models: list[str] = Field(default_factory=list)
    default_model: str = ""


class WorkspaceSettings(BaseModel):
    """
    Merged workspace settings from .agent/configs/ hierarchy.

    Inheritance: Factory → Workspace → Application
    Later levels override earlier ones.
    """

    # Paths
    factory_root: Path
    workspace_root: Optional[Path] = None
    secrets_dir: Path

    # Users (from users.yaml)
    users: dict[str, UserConfig] = Field(default_factory=dict)
    default_password: str = "test123"

    # API Providers (from api_providers.yaml)
    api_providers: dict[str, ProviderConfig] = Field(default_factory=dict)
    default_provider: str = "gemini"
    default_model: str = "gemini-2.0-flash"

    # Workspace defaults (from workspace_defaults.yaml)
    agent_defaults: dict[str, Any] = Field(default_factory=dict)
    pilot_defaults: dict[str, Any] = Field(default_factory=dict)
    features: dict[str, bool] = Field(default_factory=dict)
    logging: dict[str, str] = Field(default_factory=dict)

    # Cached secrets
    _secrets: dict[str, str] = {}

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def get_secret(self, key: str) -> Optional[str]:
        """
        Get a secret value.

        Priority:
        1. Environment variable
        2. secrets/api_keys.env file
        3. None
        """
        # Check environment first
        if key in os.environ:
            return os.environ[key]

        # Check cached secrets
        if key in self._secrets:
            return self._secrets[key]

        return None

    def get_user(self, email: str) -> Optional[UserConfig]:
        """Get user configuration by email."""
        return self.users.get(email)

    def get_provider(self, name: str) -> Optional[ProviderConfig]:
        """Get API provider configuration."""
        return self.api_providers.get(name)

    def get_model_string(
        self, provider: Optional[str] = None, model: Optional[str] = None
    ) -> str:
        """
        Get pydantic-ai format model string.

        Args:
            provider: Provider name (default: self.default_provider)
            model: Model name (default: provider's default or self.default_model)

        Returns:
            String like "gemini:gemini-2.0-flash"
        """
        p = provider or self.default_provider
        prov_config = self.api_providers.get(p)

        if model:
            m = model
        elif prov_config and prov_config.default_model:
            m = prov_config.default_model
        else:
            m = self.default_model

        return f"{p}:{m}"


def find_factory_root(start: Optional[Path] = None) -> Optional[Path]:
    """
    Walk up from start directory to find Factory root.

    Factory root is identified by:
    - .agent/manifest.yaml with includes: []
    - pyproject.toml with name = "agent-factory"
    - FACTORY_ROOT environment variable
    """
    # Check environment first
    if "FACTORY_ROOT" in os.environ:
        return Path(os.environ["FACTORY_ROOT"])

    current = start or Path.cwd()

    while current != current.parent:
        # Check for factory markers
        manifest = current / ".agent" / "manifest.yaml"
        if manifest.exists():
            content = manifest.read_text(encoding="utf-8")
            # Root has empty includes
            if "includes: []" in content:
                return current

        # Check pyproject.toml
        pyproject = current / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text(encoding="utf-8")
            if 'name = "agent-factory"' in content:
                return current

        current = current.parent

    return None


def load_yaml_config(path: Path) -> dict[str, Any]:
    """Load a YAML config file, return empty dict if not exists."""
    if not path.exists():
        return {}

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_secrets(secrets_dir: Path) -> dict[str, str]:
    """Load secrets from api_keys.env file."""
    secrets = {}

    api_keys_file = secrets_dir / "api_keys.env"
    if api_keys_file.exists():
        secrets.update(dotenv_values(api_keys_file))

    return secrets


def collect_agent_dirs(start: Path, factory_root: Path) -> list[Path]:
    """
    Collect all .agent directories from start up to factory_root.

    Returns list ordered from factory (first) to current (last).
    Later entries override earlier ones.
    """
    dirs = []
    current = start

    while current != factory_root.parent:
        agent_dir = current / ".agent"
        if agent_dir.exists():
            dirs.insert(0, agent_dir)  # Insert at front so factory is first

        if current == factory_root:
            break
        current = current.parent

    return dirs


def load_workspace_settings(
    start: Optional[Path] = None, factory_root: Optional[Path] = None
) -> WorkspaceSettings:
    """
    Load and merge workspace settings from .agent/configs/ hierarchy.

    Args:
        start: Starting directory (default: cwd)
        factory_root: Factory root (default: auto-detect)

    Returns:
        WorkspaceSettings with merged configuration
    """
    start = start or Path.cwd()
    factory_root = factory_root or find_factory_root(start)

    if not factory_root:
        raise ValueError(
            "Could not find Factory root. "
            "Set FACTORY_ROOT environment variable or run from within Factory."
        )

    secrets_dir = factory_root / "secrets"

    # Collect all .agent directories in hierarchy
    agent_dirs = collect_agent_dirs(start, factory_root)

    # Merge configs (later overrides earlier)
    merged_users: dict[str, dict] = {}
    merged_providers: dict[str, dict] = {}
    merged_defaults: dict[str, Any] = {}
    default_password = "test123"
    default_provider = "gemini"
    default_model = "gemini-2.0-flash"

    for agent_dir in agent_dirs:
        configs_dir = agent_dir / "configs"
        if not configs_dir.exists():
            continue

        # Users
        users_config = load_yaml_config(configs_dir / "users.yaml")
        if "default_password" in users_config:
            default_password = users_config["default_password"]
        if "users" in users_config:
            for email, user_data in users_config["users"].items():
                if email in merged_users:
                    merged_users[email].update(user_data)
                else:
                    merged_users[email] = user_data

        # Providers
        providers_config = load_yaml_config(configs_dir / "api_providers.yaml")
        if "default_provider" in providers_config:
            default_provider = providers_config["default_provider"]
        if "default_model" in providers_config:
            default_model = providers_config["default_model"]
        if "providers" in providers_config:
            for name, prov_data in providers_config["providers"].items():
                if name in merged_providers:
                    merged_providers[name].update(prov_data)
                else:
                    merged_providers[name] = prov_data

        # Workspace defaults
        defaults_config = load_yaml_config(configs_dir / "workspace_defaults.yaml")
        for key in ["agent_defaults", "pilot_defaults", "features", "logging"]:
            if key in defaults_config:
                if key not in merged_defaults:
                    merged_defaults[key] = {}
                merged_defaults[key].update(defaults_config[key])

    # Convert to typed models
    users = {email: UserConfig(**data) for email, data in merged_users.items()}

    providers = {
        name: ProviderConfig(
            name=data.get("name", name),
            **{k: v for k, v in data.items() if k != "name"},
        )
        for name, data in merged_providers.items()
    }

    # Load secrets
    secrets = load_secrets(secrets_dir)

    # Create settings object
    settings = WorkspaceSettings(
        factory_root=factory_root,
        workspace_root=start if start != factory_root else None,
        secrets_dir=secrets_dir,
        users=users,
        default_password=default_password,
        api_providers=providers,
        default_provider=default_provider,
        default_model=default_model,
        agent_defaults=merged_defaults.get("agent_defaults", {}),
        pilot_defaults=merged_defaults.get("pilot_defaults", {}),
        features=merged_defaults.get("features", {}),
        logging=merged_defaults.get("logging", {}),
    )
    settings._secrets = secrets

    return settings


# Convenience singleton
_cached_settings: Optional[WorkspaceSettings] = None


def get_settings(refresh: bool = False) -> WorkspaceSettings:
    """Get cached workspace settings (singleton pattern)."""
    global _cached_settings

    if _cached_settings is None or refresh:
        _cached_settings = load_workspace_settings()

    return _cached_settings

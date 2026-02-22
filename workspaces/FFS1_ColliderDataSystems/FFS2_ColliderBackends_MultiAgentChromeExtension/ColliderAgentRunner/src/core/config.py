"""Configuration settings for ColliderAgentRunner."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from secrets file + environment.

    Priority (highest first):
      1. Environment variables
      2. D:/FFS0_Factory/secrets/api_keys.env
      3. ../.env (FFS2 shared .env)
      4. .env (local override)

    Provider selection (AGENT_PROVIDER env var):
      - "anthropic"      — direct Anthropic API (requires ANTHROPIC_API_KEY with credits)
      - "gemini"         — Google AI Studio Gemini (requires GEMINI_API_KEY)
      - "google-vertex"  — Claude on Vertex AI (uses ADC / GOOGLE_APPLICATION_CREDENTIALS)
    """

    # LLM — provider + model (COLLIDER_AGENT_* prefix avoids collision with FFS2 AGENT_MODEL)
    collider_agent_provider: str = "anthropic"
    collider_agent_model: str | None = None

    # DataServer
    data_server_url: str = "http://localhost:8000"

    # GraphToolServer (for tool discovery)
    graph_tool_url: str = "http://localhost:8001"

    # NanoClawBridge — WebSocket URL returned to Chrome extension for direct chat
    nanoclaw_bridge_url: str = "ws://127.0.0.1:18789"
    nanoclaw_bridge_token: str = "collider-dev-token-2026"

    # NanoClaw workspace directories — context files written here for Claude Code to read
    nanoclaw_workspace_dir: str = "~/.nanoclaw/workspaces/collider"
    nanoclaw_root_workspace_dir: str = "~/.nanoclaw/workspaces/collider-root"

    # Static skills directory (collider-mcp etc.) — copied to workspace on session compose
    nanoclaw_static_skills_dir: str = ""

    # GraphToolServer MCP endpoint — used in .mcp.json for Claude Code tool access
    graph_tool_mcp_url: str = "http://localhost:8001/mcp/sse"

    # Default credentials — required; set in secrets/api_keys.env
    collider_username: str
    collider_password: str

    # Anthropic direct API (optional — only required when agent_provider=anthropic)
    anthropic_api_key: str | None = None

    # Google AI Studio (Gemini) — required when agent_provider=gemini
    gemini_api_key: str | None = None

    # Google Vertex AI (ADC) — required when agent_provider=google-vertex
    vertex_project_id: str | None = None
    vertex_region: str = "us-east5"

    # Per-role credentials — fall back to collider_username/password if not set
    collider_superadmin_username: str | None = None
    collider_superadmin_password: str | None = None
    collider_collider_admin_username: str | None = None
    collider_collider_admin_password: str | None = None
    collider_app_admin_username: str | None = None
    collider_app_admin_password: str | None = None
    collider_app_user_username: str | None = None
    collider_app_user_password: str | None = None

    # Server
    port: int = 8004
    debug: bool = False

    @property
    def effective_agent_model(self) -> str:
        """Return the resolved model name, applying per-provider defaults."""
        _defaults: dict[str, str] = {
            "anthropic": "claude-sonnet-4-6",
            "gemini": "gemini-2.5-flash",
            "google-vertex": "claude-sonnet-4-6",
        }
        return self.collider_agent_model or _defaults.get(
            self.collider_agent_provider.lower(), "gemini-2.5-flash"
        )

    model_config = SettingsConfigDict(
        env_file=[
            "D:/FFS0_Factory/secrets/api_keys.env",
            "../.env",
            ".env",
        ],
        env_ignore_empty=True,
        extra="ignore",
    )


settings: Settings = Settings()  # type: ignore[call-arg]

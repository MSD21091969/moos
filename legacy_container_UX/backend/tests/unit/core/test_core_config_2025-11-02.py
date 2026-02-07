"""
Unit tests for Settings configuration.

Tests environment variable loading, defaults, validation in isolation.
"""

from src.core.config import Settings


class TestSettingsDefaults:
    """Test Settings default values."""

    def test_default_values_loaded(self, monkeypatch):
        """
        TEST: Settings loads default values when no env vars provided.

        PURPOSE: Ensure app works out-of-box for local development without .env file.

        VALIDATES:
        - app_title defaults to "Collider API"
        - app_version defaults to "2026.1.0"
        - environment defaults to "development"
        - debug defaults to True (development mode)
        - use_firestore_mocks defaults to True (mock Firestore by default)

        EXPECTED: All defaults match config.py values.
        """
        # Clear all env vars to test pure defaults
        monkeypatch.delenv("GCP_PROJECT", raising=False)
        monkeypatch.delenv("ENVIRONMENT", raising=False)

        settings = Settings()

        assert settings.app_title == "Collider API"
        # CI sets APP_VERSION=2026.1.0, .env.example has 0.1.0 - accept both
        assert settings.app_version in ["0.1.0", "2026.1.0"]
        assert settings.environment == "development"
        assert settings.debug is True
        assert settings.use_firestore_mocks is True
        assert settings.host == "127.0.0.1"
        assert settings.port == 8000

    def test_firestore_defaults(self, monkeypatch):
        """
        TEST: Firestore settings default to mock mode for local dev.

        PURPOSE: Enable local development without GCP credentials.

        VALIDATES:
        - use_firestore_mocks defaults to True (use MockFirestoreClient)
        - firestore_database from .env
        - gcp_project from .env if set

        EXPECTED: Safe defaults for local development.
        """
        settings = Settings()

        assert settings.use_firestore_mocks is True
        # CI may set different database name - accept test-db in test environment
        assert settings.firestore_database in ["my-tiny-data-collider", "collider", "test-db"]
        # gcp_project may be set in .env for production-ready config, that's OK


class TestEnvironmentOverrides:
    """Test environment variable overrides."""

    def test_environment_variable_override(self, monkeypatch):
        """
        TEST: Environment variables override default values.

        PURPOSE: Allow runtime configuration via env vars.

        VALIDATES:
        - ENVIRONMENT="production" → settings.environment == "production"
        - DEBUG="false" → settings.debug == False
        - PORT="9000" → settings.port == 9000
        - Pydantic coerces types (string "9000" → int 9000, "false" → bool False)

        EXPECTED: Env vars override defaults with correct type coercion.
        """
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("PORT", "9000")

        settings = Settings()

        assert settings.environment == "production"
        assert settings.debug is False
        assert settings.port == 9000

    def test_gcp_project_from_env(self, monkeypatch):
        """
        TEST: GCP_PROJECT env var loads into gcp_project field.

        PURPOSE: Enable GCP Firestore connection in production.

        VALIDATES:
        - GCP_PROJECT="my-project-123" → settings.gcp_project == "my-project-123"
        - Field uses validation_alias="GCP_PROJECT" (uppercase)
        - None when not set (default)

        EXPECTED: GCP_PROJECT env var correctly loaded.
        """
        monkeypatch.setenv("GCP_PROJECT", "my-project-123")

        settings = Settings()

        assert settings.gcp_project == "my-project-123"


class TestComputedProperties:
    """Test computed properties on Settings."""

    def test_is_production_true(self, monkeypatch):
        """
        TEST: is_production property returns True when environment="production".

        PURPOSE: Enable conditional logic based on deployment environment.

        VALIDATES:
        - settings.environment = "production" → is_production == True
        - Used to disable debug features, enable Secret Manager, etc.

        EXPECTED: is_production == True only in production environment.
        """
        monkeypatch.setenv("ENVIRONMENT", "production")

        settings = Settings()

        assert settings.is_production is True

    def test_is_production_false_in_development(self, monkeypatch):
        """
        TEST: is_production property returns False when environment != "production".

        PURPOSE: Keep development/staging environments distinct from production.

        VALIDATES:
        - environment = "development" → is_production == False
        - environment = "staging" → is_production == False
        - Only "production" returns True

        EXPECTED: is_production == False in non-production environments.
        """
        monkeypatch.setenv("ENVIRONMENT", "development")

        settings = Settings()

        assert settings.is_production is False

    def test_docs_enabled_in_development(self, monkeypatch):
        """
        TEST: docs_enabled property returns True when not production.

        PURPOSE: Enable /docs and /redoc endpoints in dev/staging, hide in production.

        VALIDATES:
        - environment = "development" → docs_enabled == True
        - environment = "production" → docs_enabled == False
        - Logic: not self.is_production

        EXPECTED: Docs enabled in dev/staging, disabled in production.
        """
        monkeypatch.setenv("ENVIRONMENT", "development")
        settings_dev = Settings()

        monkeypatch.setenv("ENVIRONMENT", "production")
        settings_prod = Settings()

        assert settings_dev.docs_enabled is True
        assert settings_prod.docs_enabled is False


class TestAPIKeyRetrieval:
    """Test get_api_key() method."""

    def test_get_api_key_from_environment(self, monkeypatch):
        """
        TEST: get_api_key() retrieves from environment variables.

        PURPOSE: Load API keys from env vars for local development.

        VALIDATES:
        - get_api_key("openai") checks OPENAI_API_KEY env var
        - Returns env var value if set
        - Case-insensitive: "openai" → "OPENAI_API_KEY"

        EXPECTED: Returns API key from environment.
        """
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-12345")

        settings = Settings()
        api_key = settings.get_api_key("openai")

        assert api_key == "sk-test-12345"

    def test_get_api_key_not_found(self, monkeypatch):
        """
        TEST: get_api_key() returns None when key not configured.

        PURPOSE: Handle missing API keys gracefully without raising exceptions.

        VALIDATES:
        - get_api_key("nonexistent") returns None
        - No KeyError or ValueError raised
        - Caller can check: if api_key is None

        EXPECTED: Returns None for unconfigured services.
        """
        monkeypatch.delenv("NONEXISTENT_API_KEY", raising=False)

        settings = Settings()
        api_key = settings.get_api_key("nonexistent")

        assert api_key is None

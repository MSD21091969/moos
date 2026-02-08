"""Unit tests for src/core/env_validator.py

TEST: Environment variable validation
PURPOSE: Validate startup environment checks
VALIDATES: Required vars, errors, warnings
EXPECTED: Validation catches missing vars
"""

import pytest
import os
from unittest.mock import patch
from src.core.env_validator import (
    validate_environment,
    validate_on_startup,
    EnvironmentValidationError,
)


class TestValidateEnvironment:
    """Test validate_environment function."""

    def test_validate_production_success(self):
        """
        TEST: Validate production environment
        PURPOSE: Verify production requirements
        VALIDATES: All required vars present
        EXPECTED: Validation passes
        """
        env = {
            "ENVIRONMENT": "production",
            "JWT_SECRET_KEY": "secret",
            "ALLOWED_ORIGINS": "https://example.com",
            "K_SERVICE": "my-service",  # Cloud Run marker
        }

        with patch.dict(os.environ, env, clear=True):
            result = validate_environment("production")

            assert "ENVIRONMENT" in result
            assert "JWT_SECRET_KEY" in result

    def test_validate_production_missing_required_fails(self):
        """
        TEST: Missing required production vars
        PURPOSE: Verify error on missing vars
        VALIDATES: EnvironmentValidationError raised
        EXPECTED: Validation fails
        """
        env = {"ENVIRONMENT": "production"}

        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(EnvironmentValidationError):
                validate_environment("production")

    def test_validate_development_allows_emulator(self):
        """
        TEST: Development with Firestore emulator
        PURPOSE: Verify dev environment flexibility
        VALIDATES: No strict requirements
        EXPECTED: Validation passes
        """
        env = {"ENVIRONMENT": "development", "FIRESTORE_EMULATOR_HOST": "localhost:8080"}

        with patch.dict(os.environ, env, clear=True):
            result = validate_environment("development")

            assert isinstance(result, dict)

    def test_validate_test_environment(self):
        """
        TEST: Test environment configuration
        PURPOSE: Verify test settings
        VALIDATES: Mock Firestore enabled
        EXPECTED: DISABLE_RATE_LIMITING set
        """
        env = {"ENVIRONMENT": "test"}

        with patch.dict(os.environ, env, clear=True):
            result = validate_environment("test")

            assert result.get("DISABLE_RATE_LIMITING") == "true"


class TestValidateOnStartup:
    """Test validate_on_startup function."""

    def test_validate_on_startup_success(self):
        """
        TEST: Startup validation passes
        PURPOSE: Verify startup check
        VALIDATES: No exception raised
        EXPECTED: Validation completes
        """
        env = {"ENVIRONMENT": "development"}

        with patch.dict(os.environ, env, clear=True):
            validate_on_startup()  # Should not raise

    def test_validate_on_startup_exits_on_failure(self):
        """
        TEST: Missing ENVIRONMENT defaults to development
        PURPOSE: Verify startup fills in default
        VALIDATES: Default environment used
        EXPECTED: No exception, env var set
        """
        env = {}

        with patch.dict(os.environ, env, clear=True):
            validate_on_startup()
            assert os.environ.get("ENVIRONMENT") == "development"

    def test_validate_on_startup_exits_when_production_invalid(self):
        """
        TEST: Production startup fails when required vars missing
        PURPOSE: Validate strict mode
        EXPECTED: SystemExit raised
        """
        env = {"ENVIRONMENT": "production"}

        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(SystemExit):
                validate_on_startup()

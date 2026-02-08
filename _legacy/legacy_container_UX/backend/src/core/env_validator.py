"""Environment variable validation on startup."""

import os
import sys
from typing import Dict, List

from src.core.logging import get_logger

logger = get_logger(__name__)


class EnvironmentValidationError(Exception):
    """Raised when required environment variables are missing or invalid."""

    pass


def validate_environment(environment: str = "production") -> Dict[str, str]:
    """
    Validate required environment variables for the given environment.

    Args:
        environment: Environment name (development, test, production)

    Returns:
        Dict of validated environment variables

    Raises:
        EnvironmentValidationError: If required variables are missing or invalid
    """
    errors: List[str] = []
    warnings: List[str] = []
    config: Dict[str, str] = {}

    # Base variables (all environments)
    required_base = ["ENVIRONMENT"]
    for var in required_base:
        value = os.getenv(var)
        if not value:
            errors.append(f"Missing required environment variable: {var}")
        else:
            config[var] = value

    # Production-specific requirements
    if environment == "production":
        required_prod = [
            "JWT_SECRET_KEY",  # For authentication
            "ALLOWED_ORIGINS",  # For CORS
        ]

        for var in required_prod:
            value = os.getenv(var)
            if not value:
                errors.append(f"Missing required production variable: {var}")
            else:
                config[var] = value

        # GOOGLE_APPLICATION_CREDENTIALS check - skip file validation on Cloud Run
        # Cloud Run injects credentials automatically
        gac_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if gac_path:
            config["GOOGLE_APPLICATION_CREDENTIALS"] = gac_path
            # Only check if file exists when not on Cloud Run
            if not os.getenv("K_SERVICE") and not os.path.exists(gac_path):
                errors.append(f"GOOGLE_APPLICATION_CREDENTIALS file not found: {gac_path}")
        elif not os.getenv("K_SERVICE"):  # Not on Cloud Run
            warnings.append("GOOGLE_APPLICATION_CREDENTIALS not set - authentication may fail")

        # Optional but recommended for production
        optional_prod = [
            "LOGFIRE_TOKEN",  # For production logging
            "REDIS_URL",  # For rate limiting cache
            "GCP_PROJECT_ID",  # For Cloud Run deployment
        ]

        for var in optional_prod:
            value = os.getenv(var)
            if not value:
                warnings.append(f"Optional production variable not set: {var}")
            else:
                config[var] = value

    # Development-specific
    elif environment == "development":
        # Mock Firestore is OK in dev
        if not os.getenv("FIRESTORE_EMULATOR_HOST"):
            warnings.append(
                "FIRESTORE_EMULATOR_HOST not set - will use production Firestore if credentials exist"
            )

    # Test-specific
    elif environment == "test":
        # Tests should use mock Firestore
        config["FIRESTORE_EMULATOR_HOST"] = os.getenv("FIRESTORE_EMULATOR_HOST", "mock")
        config["DISABLE_RATE_LIMITING"] = "true"

    # Log results
    if errors:
        logger.error("Environment validation failed:")
        for error in errors:
            logger.error("Validation error", extra={"error_message": error})
        raise EnvironmentValidationError(
            f"Environment validation failed with {len(errors)} errors. See logs for details."
        )

    if warnings:
        logger.warning("Environment validation warnings:")
        for warning in warnings:
            logger.warning("Validation warning", extra={"warning_message": warning})

    logger.info("Environment validation passed", extra={"environment": environment})
    logger.info("Variables configured", extra={"count": len(config)})

    return config


def validate_on_startup() -> None:
    """
    Validate environment on application startup.

    Called from main.py lifespan. Exits process if validation fails.
    """
    environment = os.getenv("ENVIRONMENT")
    if not environment:
        environment = "development"
        os.environ["ENVIRONMENT"] = environment
        logger.warning("ENVIRONMENT not set, defaulting to development")

    try:
        validate_environment(environment)
    except EnvironmentValidationError as e:
        logger.error("Startup aborted", extra={"error": str(e)})
        sys.exit(1)

"""Structured logging with Pydantic Logfire integration.

Provides:
- Automatic FastAPI instrumentation
- Request/response tracing with correlation IDs
- Performance profiling and spans
- OpenTelemetry-compatible structured logs
"""

import logging
import os
from pathlib import Path

import logfire


def setup_logging(level: str = "INFO") -> None:
    """
    Configure Logfire-based structured logging.

    Features:
    - Automatic FastAPI request/response tracing
    - Correlation IDs for request tracking
    - Performance spans for slow operations
    - OpenTelemetry export (configurable)

    Environment Variables:
    - LOGFIRE_TOKEN: Logfire API token (production)
    - ENVIRONMENT: dev/production (controls export)
    - LOG_LEVEL: Logging level (default: INFO)

    Credentials Priority:
    1. LOGFIRE_TOKEN environment variable
    2. .logfire/logfire_credentials.json file (local dev)
    """
    # Get Logfire token from env or credentials file
    logfire_token = os.getenv("LOGFIRE_TOKEN")

    # If not in env, try reading from .logfire/logfire_credentials.json
    if not logfire_token:
        creds_file = Path(".logfire/logfire_credentials.json")
        if creds_file.exists():
            try:
                import json

                data = json.loads(creds_file.read_text())
                logfire_token = data.get("token")
            except Exception:  # nosec B110
                pass  # Expected: token loading is optional

    environment = os.getenv("ENVIRONMENT", "development")

    # Configure based on environment and token availability
    try:
        if logfire_token and environment == "production":
            # Production: Export to Logfire cloud
            logfire.configure(
                token=logfire_token,
                service_name="my-tiny-data-collider",
                environment=environment,
                send_to_logfire=True,
            )
        elif logfire_token:
            # Development with token: Send to Logfire with console output
            logfire.configure(
                token=logfire_token,
                service_name="my-tiny-data-collider",
                environment=environment,
                send_to_logfire=True,
                console=logfire.ConsoleOptions(
                    colors="auto",
                    span_style="indented",
                    include_timestamps=True,
                ),
            )
        else:
            # No token: Console only, no cloud export
            logfire.configure(
                send_to_logfire=False,
                console=logfire.ConsoleOptions(
                    colors="auto",
                    span_style="indented",
                    include_timestamps=True,
                ),
            )
    except Exception as e:  # nosec B110
        # If Logfire configuration fails, continue with console logging only
        logging.warning(
            f"Logfire configuration failed (non-fatal): {str(e)}. "
            "Continuing with console logging only.",
            exc_info=False,
        )
        logfire.configure(
            send_to_logfire=False,
            console=logfire.ConsoleOptions(
                colors="auto",
                span_style="indented",
                include_timestamps=True,
            ),
        )

    # Set log level
    logging.basicConfig(level=level)

    # Suppress noisy third-party loggers
    logging.getLogger("google").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    # Suppress Logfire distributed tracing warnings (false positives from frontend)
    logging.getLogger("logfire").setLevel(logging.ERROR)


def get_logger(name: str) -> logging.Logger:
    """
    Get logger with Logfire integration.

    Usage:
        logger = get_logger(__name__)
        logger.info("User action", extra={"user_id": "123", "action": "login"})
    """
    return logging.getLogger(name)


# Default logger
logger = get_logger("collider")

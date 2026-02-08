"""Cloud Run Job worker entrypoint.

This script runs as a Cloud Run Job and executes background tasks.
Each job execution handles one task.
"""

import asyncio
import json
import logging
import os
import sys

from src.core.background_tasks import TASK_REGISTRY
from src.core.logging import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


async def execute_task():
    """Execute background task based on environment variables."""
    task_name = os.getenv("TASK_NAME")
    task_args_str = os.getenv("TASK_ARGS", "{}")

    if not task_name:
        logger.error("TASK_NAME environment variable not set")
        sys.exit(1)

    if task_name not in TASK_REGISTRY:
        logger.error("Unknown task", extra={"task_name": task_name})
        logger.info("Available tasks", extra={"tasks": list(TASK_REGISTRY.keys())})
        sys.exit(1)

    try:
        # Parse task arguments
        task_args = json.loads(task_args_str)
        logger.info("Executing task", extra={"task_name": task_name, "args": task_args})

        # Get task function
        task_func = TASK_REGISTRY[task_name]

        # Execute task
        result = await task_func(**task_args)

        logger.info("Task completed", extra={"task_name": task_name})
        logger.info("Task result", extra={"result": result})

        # Exit with success
        sys.exit(0)

    except json.JSONDecodeError as e:
        logger.error("Invalid TASK_ARGS JSON", extra={"error": str(e)})
        sys.exit(1)

    except Exception as e:
        logger.error("Task execution failed", extra={"error": str(e)}, exc_info=True)
        sys.exit(1)


def main():
    """Main entrypoint for Cloud Run Job worker."""
    logger.info("Cloud Run Job worker starting")
    asyncio.run(execute_task())


if __name__ == "__main__":
    main()

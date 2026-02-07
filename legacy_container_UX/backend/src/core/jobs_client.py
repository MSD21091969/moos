"""Cloud Run Jobs client for triggering background tasks."""

import logging
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from google.cloud.run_v2.types import Job

try:
    from google.cloud import run_v2
    from google.cloud.run_v2.types import ExecutionTemplate, RunJobRequest

    CLOUD_RUN_AVAILABLE = True
except ImportError:
    CLOUD_RUN_AVAILABLE = False
    run_v2 = None
    ExecutionTemplate = None
    RunJobRequest = None

from src.core.config import settings

logger = logging.getLogger(__name__)


class CloudRunJobsClient:
    """Client for managing and executing Cloud Run Jobs."""

    def __init__(self):
        """Initialize Cloud Run Jobs client."""
        if not CLOUD_RUN_AVAILABLE:
            raise ImportError(
                "google-cloud-run not installed. Install with: pip install google-cloud-run"
            )
        self.client = run_v2.JobsClient()
        self.executions_client = run_v2.ExecutionsClient()
        self.project_id = settings.gcp_project
        self.region = "europe-west4"

    def _job_path(self, job_name: str) -> str:
        """Build full job path.

        Args:
            job_name: Job name

        Returns:
            Full job path for Cloud Run Jobs API
        """
        return f"projects/{self.project_id}/locations/{self.region}/jobs/{job_name}"

    async def trigger_job(
        self,
        job_name: str,
        task_name: str,
        task_args: Optional[dict[str, Any]] = None,
        timeout: int = 600,
    ) -> dict[str, str]:
        """Trigger a Cloud Run Job execution.

        Args:
            job_name: Name of the Cloud Run Job
            task_name: Task function name from background_tasks.py
            task_args: Arguments to pass to task (as JSON)
            timeout: Job timeout in seconds (default: 10 minutes)

        Returns:
            Execution details (job name, execution ID)

        Example:
            result = await trigger_job(
                job_name="background-worker",
                task_name="export_session_messages",
                task_args={"session_id": "123", "export_format": "pdf"}
            )
        """
        try:
            # Build environment variables for task execution (TODO)
            # env_vars = {
            #     "TASK_NAME": task_name,
            #     "TASK_ARGS": str(task_args or {}),
            #     "ENVIRONMENT": settings.environment,
            # }

            # Build execution request
            # parent = f"projects/{self.project_id}/locations/{self.region}"  # TODO: Use if needed
            job_path = self._job_path(job_name)

            # Trigger job execution
            request = RunJobRequest(
                name=job_path,
            )

            operation = self.client.run_job(request=request)
            logger.info(
                "Triggered Cloud Run Job", extra={"job_name": job_name, "task_name": task_name}
            )

            # Get execution details from operation
            execution_name = operation.name

            return {
                "job_name": job_name,
                "execution_id": execution_name,
                "task_name": task_name,
                "status": "triggered",
            }

        except Exception as e:
            logger.error(
                "Failed to trigger Cloud Run Job", extra={"job_name": job_name, "error": str(e)}
            )
            raise

    async def get_execution_status(self, execution_name: str) -> dict[str, Any]:
        """Get status of a job execution.

        Args:
            execution_name: Full execution name from trigger_job

        Returns:
            Execution status details
        """
        try:
            execution = self.executions_client.get_execution(name=execution_name)

            return {
                "execution_id": execution_name,
                "status": execution.completion_status,
                "start_time": execution.start_time,
                "completion_time": execution.completion_time,
            }

        except Exception as e:
            logger.error("Failed to get execution status", extra={"error": str(e)})
            raise

    async def create_job(
        self,
        job_name: str,
        image: str,
        command: list[str],
        env_vars: Optional[dict[str, str]] = None,
        timeout: int = 600,
        memory: str = "512Mi",
        cpu: str = "1",
    ) -> "Job":
        """Create a new Cloud Run Job.

        Args:
            job_name: Job name
            image: Container image URL
            command: Command to run in container
            env_vars: Environment variables
            timeout: Job timeout in seconds
            memory: Memory allocation
            cpu: CPU allocation

        Returns:
            Created Job resource
        """
        try:
            parent = f"projects/{self.project_id}/locations/{self.region}"

            job = Job(
                template=ExecutionTemplate(
                    template={
                        "containers": [
                            {
                                "image": image,
                                "command": command,
                                "env": [
                                    {"name": k, "value": v} for k, v in (env_vars or {}).items()
                                ],
                                "resources": {
                                    "limits": {
                                        "memory": memory,
                                        "cpu": cpu,
                                    }
                                },
                            }
                        ],
                        "timeout": f"{timeout}s",
                        "service_account": f"github-actions@{self.project_id}.iam.gserviceaccount.com",
                    }
                ),
            )

            request = {"parent": parent, "job": job, "job_id": job_name}
            operation = self.client.create_job(request=request)
            created_job = operation.result()

            logger.info("Created Cloud Run Job", extra={"job_name": job_name})
            return created_job

        except Exception as e:
            logger.error(
                "Failed to create Cloud Run Job", extra={"job_name": job_name, "error": str(e)}
            )
            raise


# Global client instance (lazy-loaded)
_jobs_client: Optional[CloudRunJobsClient] = None


def get_jobs_client() -> CloudRunJobsClient:
    """Get or create the jobs client instance."""
    global _jobs_client
    if _jobs_client is None:
        _jobs_client = CloudRunJobsClient()
    return _jobs_client


async def trigger_background_task(
    task_name: str,
    task_args: Optional[dict[str, Any]] = None,
) -> dict[str, str]:
    """Convenience function to trigger a background task.

    Args:
        task_name: Task function name from background_tasks.py
        task_args: Arguments to pass to task

    Returns:
        Execution details
    """
    client = get_jobs_client()
    return await client.trigger_job(
        job_name="background-worker",
        task_name=task_name,
        task_args=task_args,
    )


# Simplified JobsClient for testing (alias to CloudRunJobsClient)
JobsClient = CloudRunJobsClient

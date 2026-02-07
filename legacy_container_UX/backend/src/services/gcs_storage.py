"""Google Cloud Storage service for file operations."""

from datetime import timedelta
from typing import Optional

from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class GCSStorageProvider:
    """Provider for Google Cloud Storage operations."""

    def __init__(self, bucket_name: Optional[str] = None):
        """Initialize GCS client and bucket.

        Args:
            bucket_name: GCS bucket name. Defaults to settings.gcs_bucket_name
        """
        self.client = storage.Client()
        self.bucket_name = bucket_name or settings.gcs_bucket_name
        self.bucket = self.client.bucket(self.bucket_name)
        logger.info(f"Initialized GCS provider for bucket: {self.bucket_name}")

    def generate_signed_url(
        self,
        blob_name: str,
        expiration_minutes: int = 60,
        method: str = "GET",
        content_type: Optional[str] = None,
    ) -> str:
        """Generate time-limited signed URL for file access.

        Args:
            blob_name: Path to file in GCS bucket
            expiration_minutes: URL validity duration (default 60 minutes)
            method: HTTP method (GET for download, PUT for upload)
            content_type: MIME type for PUT requests

        Returns:
            Signed URL string

        Raises:
            GoogleCloudError: If URL generation fails
        """
        try:
            blob = self.bucket.blob(blob_name)

            url_params = {
                "version": "v4",
                "expiration": timedelta(minutes=expiration_minutes),
                "method": method,
            }

            if content_type and method == "PUT":
                url_params["content_type"] = content_type

            url = blob.generate_signed_url(**url_params)

            logger.info(
                f"Generated {method} signed URL for {blob_name} (expires in {expiration_minutes}m)"
            )
            return url

        except GoogleCloudError as e:
            logger.error(f"Failed to generate signed URL for {blob_name}: {e}")
            raise

    async def upload_file(
        self,
        blob_name: str,
        content: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload file to GCS bucket.

        Args:
            blob_name: Destination path in bucket
            content: File content as bytes
            content_type: MIME type of file

        Returns:
            Blob name (path in bucket)

        Raises:
            GoogleCloudError: If upload fails
        """
        try:
            blob = self.bucket.blob(blob_name)
            blob.upload_from_string(content, content_type=content_type)

            logger.info(f"Uploaded {len(content)} bytes to {blob_name} (type: {content_type})")
            return blob.name

        except GoogleCloudError as e:
            logger.error(f"Failed to upload {blob_name}: {e}")
            raise

    async def download_file(self, blob_name: str) -> bytes:
        """Download file from GCS bucket.

        Args:
            blob_name: Path to file in bucket

        Returns:
            File content as bytes

        Raises:
            GoogleCloudError: If download fails
        """
        try:
            blob = self.bucket.blob(blob_name)
            content = blob.download_as_bytes()

            logger.info(f"Downloaded {len(content)} bytes from {blob_name}")
            return content

        except GoogleCloudError as e:
            logger.error(f"Failed to download {blob_name}: {e}")
            raise

    async def delete_file(self, blob_name: str) -> None:
        """Delete file from GCS bucket.

        Args:
            blob_name: Path to file in bucket

        Raises:
            GoogleCloudError: If deletion fails
        """
        try:
            blob = self.bucket.blob(blob_name)
            blob.delete()

            logger.info(f"Deleted {blob_name}")

        except GoogleCloudError as e:
            logger.error(f"Failed to delete {blob_name}: {e}")
            raise

    def file_exists(self, blob_name: str) -> bool:
        """Check if file exists in bucket.

        Args:
            blob_name: Path to file in bucket

        Returns:
            True if file exists, False otherwise
        """
        blob = self.bucket.blob(blob_name)
        exists = blob.exists()

        logger.debug(f"File exists check for {blob_name}: {exists}")
        return exists

    async def list_files(self, prefix: Optional[str] = None) -> list[dict]:
        """List files in bucket with optional prefix filter.

        Args:
            prefix: Filter files by path prefix

        Returns:
            List of file metadata dicts
        """
        try:
            blobs = self.client.list_blobs(self.bucket_name, prefix=prefix)

            files = [
                {
                    "name": blob.name,
                    "size": blob.size,
                    "content_type": blob.content_type,
                    "updated": blob.updated.isoformat() if blob.updated else None,
                }
                for blob in blobs
            ]

            logger.info(f"Listed {len(files)} files (prefix: {prefix})")
            return files

        except GoogleCloudError as e:
            logger.error(f"Failed to list files: {e}")
            raise

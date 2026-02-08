"""Filesystem tools for file and directory operations."""

from pathlib import Path
from typing import Optional

from pydantic_ai import RunContext

from src.core.logging import get_logger
from src.core.tool_registry import ToolCategory, get_tool_registry
from src.models.context import SessionContext

logger = get_logger(__name__)

registry = get_tool_registry()


@registry.register(
    name="read_file",
    description="Read contents of a text file",
    category=ToolCategory.FILESYSTEM,
    required_tier="FREE",
    quota_cost=1,
    tags=["file", "read", "filesystem"],
)
async def read_file(
    ctx: RunContext[SessionContext],
    file_path: str,
    encoding: str = "utf-8",
) -> dict:
    """
    Read contents of a text file.

    Args:
        file_path: Path to file to read
        encoding: Text encoding (default: utf-8)

    Returns:
        Dict with file content and metadata
    """
    logger.info("Reading file", extra={"file_path": file_path})

    try:
        path = Path(file_path)

        if not path.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}",
            }

        if not path.is_file():
            return {
                "success": False,
                "error": f"Not a file: {file_path}",
            }

        # Read file content
        content = path.read_text(encoding=encoding)

        # Get file stats
        stats = path.stat()

        return {
            "success": True,
            "file_path": str(path.absolute()),
            "content": content,
            "size_bytes": stats.st_size,
            "lines": len(content.splitlines()),
            "encoding": encoding,
        }

    except (FileNotFoundError, IsADirectoryError, PermissionError, UnicodeDecodeError) as e:
        logger.error(f"Failed to read file: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
        }
    except Exception as e:
        logger.error(f"Unexpected error reading file: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
        }


@registry.register(
    name="write_file",
    description="Write content to a text file",
    category=ToolCategory.FILESYSTEM,
    required_tier="FREE",
    quota_cost=2,
    tags=["file", "write", "filesystem"],
)
async def write_file(
    ctx: RunContext[SessionContext],
    file_path: str,
    content: str,
    encoding: str = "utf-8",
    overwrite: bool = False,
) -> dict:
    """
    Write content to a text file.

    Args:
        file_path: Path to file to write
        content: Content to write
        encoding: Text encoding (default: utf-8)
        overwrite: Allow overwriting existing file

    Returns:
        Dict with operation result
    """
    logger.info("Writing file", extra={"file_path": file_path, "overwrite": overwrite})

    try:
        path = Path(file_path)

        if path.exists() and not overwrite:
            return {
                "success": False,
                "error": f"File exists (use overwrite=true): {file_path}",
            }

        # Create parent directories if needed
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        path.write_text(content, encoding=encoding)

        stats = path.stat()

        return {
            "success": True,
            "file_path": str(path.absolute()),
            "bytes_written": stats.st_size,
            "lines": len(content.splitlines()),
        }

    except (OSError, PermissionError) as e:
        logger.error(f"Failed to write file: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
        }
    except Exception as e:
        logger.error(f"Unexpected error writing file: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
        }


@registry.register(
    name="list_directory",
    description="List contents of a directory",
    category=ToolCategory.FILESYSTEM,
    required_tier="FREE",
    quota_cost=1,
    tags=["directory", "list", "filesystem"],
)
async def list_directory(
    ctx: RunContext[SessionContext],
    directory_path: str,
    pattern: Optional[str] = None,
    recursive: bool = False,
) -> dict:
    """
    List files and directories.

    Args:
        directory_path: Path to directory
        pattern: Optional glob pattern (e.g., "*.txt")
        recursive: Recursively list subdirectories

    Returns:
        Dict with directory contents
    """
    logger.info("Listing directory", extra={"path": directory_path, "pattern": pattern})

    try:
        path = Path(directory_path)

        if not path.exists():
            return {
                "success": False,
                "error": f"Directory not found: {directory_path}",
            }

        if not path.is_dir():
            return {
                "success": False,
                "error": f"Not a directory: {directory_path}",
            }

        # List contents
        if pattern:
            if recursive:
                items = list(path.rglob(pattern))
            else:
                items = list(path.glob(pattern))
        else:
            if recursive:
                items = list(path.rglob("*"))
            else:
                items = list(path.iterdir())

        # Build result lists
        files = []
        directories = []

        for item in items:
            item_info = {
                "name": item.name,
                "path": str(item.absolute()),
                "size": item.stat().st_size if item.is_file() else 0,
            }

            if item.is_file():
                files.append(item_info)
            elif item.is_dir():
                directories.append(item_info)

        return {
            "success": True,
            "directory": str(path.absolute()),
            "files": files,
            "directories": directories,
            "total_files": len(files),
            "total_directories": len(directories),
        }

    except Exception as e:
        logger.error(f"Failed to list directory: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
        }


@registry.register(
    name="delete_file",
    description="Delete a file",
    category=ToolCategory.FILESYSTEM,
    required_tier="PRO",
    quota_cost=2,
    tags=["file", "delete", "filesystem"],
)
async def delete_file(
    ctx: RunContext[SessionContext],
    file_path: str,
    confirm: bool = False,
) -> dict:
    """
    Delete a file.

    Args:
        file_path: Path to file to delete
        confirm: Must be true to confirm deletion

    Returns:
        Dict with operation result
    """
    logger.info("Deleting file", extra={"file_path": file_path})

    try:
        if not confirm:
            return {
                "success": False,
                "error": "Must set confirm=true to delete file",
            }

        path = Path(file_path)

        if not path.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}",
            }

        if not path.is_file():
            return {
                "success": False,
                "error": f"Not a file: {file_path}",
            }

        # Delete file
        path.unlink()

        return {
            "success": True,
            "deleted": str(path.absolute()),
        }

    except Exception as e:
        logger.error(f"Failed to delete file: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
        }


@registry.register(
    name="get_file_info",
    description="Get file or directory information",
    category=ToolCategory.FILESYSTEM,
    required_tier="FREE",
    quota_cost=1,
    tags=["file", "info", "filesystem"],
)
async def get_file_info(
    ctx: RunContext[SessionContext],
    file_path: str,
) -> dict:
    """
    Get file or directory information.

    Args:
        file_path: Path to file or directory

    Returns:
        Dict with file/directory metadata
    """
    logger.info("Getting file info", extra={"file_path": file_path})

    try:
        path = Path(file_path)

        if not path.exists():
            return {
                "success": False,
                "error": f"Path not found: {file_path}",
            }

        stats = path.stat()

        return {
            "success": True,
            "path": str(path.absolute()),
            "name": path.name,
            "type": "file" if path.is_file() else "directory",
            "size_bytes": stats.st_size,
            "created": stats.st_ctime,
            "modified": stats.st_mtime,
            "extension": path.suffix if path.is_file() else None,
        }

    except Exception as e:
        logger.error(f"Failed to get file info: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
        }


@registry.register(
    name="create_directory",
    description="Create a new directory",
    category=ToolCategory.FILESYSTEM,
    required_tier="PRO",
    quota_cost=2,
    tags=["directory", "create", "filesystem"],
)
async def create_directory(
    ctx: RunContext[SessionContext],
    directory_path: str,
    parents: bool = True,
) -> dict:
    """
    Create a directory.

    Args:
        directory_path: Path to directory to create
        parents: Create parent directories if needed

    Returns:
        Dict with operation result
    """
    logger.info("Creating directory", extra={"directory_path": directory_path})

    try:
        path = Path(directory_path)

        if path.exists():
            return {
                "success": False,
                "error": f"Path already exists: {directory_path}",
            }

        # Create directory
        path.mkdir(parents=parents, exist_ok=False)

        return {
            "success": True,
            "created": str(path.absolute()),
        }

    except Exception as e:
        logger.error(f"Failed to create directory: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
        }

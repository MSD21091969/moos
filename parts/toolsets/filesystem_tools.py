"""File system tools for the development assistant."""
import os
from pathlib import Path


def read_file(file_path: str) -> str:
    """Read the contents of a file.
    
    Args:
        file_path: Absolute or relative path to the file.
        
    Returns:
        The file contents as a string.
    """
    path = Path(file_path).resolve()
    if not path.exists():
        return f"Error: File not found: {path}"
    if not path.is_file():
        return f"Error: Not a file: {path}"
    try:
        # Check size to prevent reading massive files
        stat = path.stat()
        if stat.st_size > 10 * 1024 * 1024:  # 10MB limit
            return f"Error: File too large to read ({stat.st_size} bytes)"
            
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return "Error: File is not valid UTF-8 text"
    except Exception as e:
        return f"Error reading file: {e}"


def write_file(file_path: str, content: str) -> str:
    """Write content to a file, creating directories if needed.
    
    Args:
        file_path: Absolute or relative path to the file.
        content: The content to write.
        
    Returns:
        Success or error message.
    """
    path = Path(file_path).resolve()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return f"Successfully wrote to: {path}"
    except Exception as e:
        return f"Error writing file: {e}"


def list_directory(dir_path: str = ".") -> str:
    """List contents of a directory.
    
    Args:
        dir_path: Path to directory (default: current directory).
        
    Returns:
        Formatted directory listing.
    """
    path = Path(dir_path).resolve()
    if not path.exists():
        return f"Error: Directory not found: {path}"
    if not path.is_dir():
        return f"Error: Not a directory: {path}"
    
    try:
        items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        lines = [f"Contents of {path}:\n"]
        for item in items[:50]:  # Limit to 50 items
            prefix = "[DIR]" if item.is_dir() else "[FILE]"
            lines.append(f"  {prefix} {item.name}")
        if len(list(path.iterdir())) > 50:
            lines.append(f"  ... and {len(list(path.iterdir())) - 50} more items")
        return "\n".join(lines)
    except Exception as e:
        return f"Error listing directory: {e}"


def search_files(pattern: str, directory: str = ".") -> str:
    """Search for files matching a pattern.
    
    Args:
        pattern: Glob pattern (e.g., "*.py", "**/*.md").
        directory: Directory to search in.
        
    Returns:
        List of matching files.
    """
    path = Path(directory).resolve()
    try:
        matches = list(path.glob(pattern))[:50]
        if not matches:
            return f"No files matching '{pattern}' in {path}"
        lines = [f"Files matching '{pattern}' in {path}:\n"]
        for match in matches:
            lines.append(f"  {match.relative_to(path)}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error searching: {e}"


def get_cwd() -> str:
    """Get the current working directory."""
    return str(Path.cwd().resolve())

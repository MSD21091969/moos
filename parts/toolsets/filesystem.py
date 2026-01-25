"""Standard Filesystem Toolset.

Provides safe, scoped file operations for Agents.
"""
import os
from typing import List, Optional

class FilesystemToolset:
    """A collection of file operations scoped to a root directory."""
    
    def __init__(self, root: str):
        self.root = os.path.abspath(root)

    def list_files(self, relative_path: str = ".") -> List[str]:
        """List files in a directory."""
        target = self._safe_path(relative_path)
        if not os.path.exists(target):
            return []
        return os.listdir(target)
        
    def read_file(self, relative_path: str) -> str:
        """Read a file."""
        target = self._safe_path(relative_path)
        with open(target, 'r', encoding='utf-8') as f:
            return f.read()

    def _safe_path(self, relative_path: str) -> str:
        """Ensure path is within root."""
        # Simple security check
        full_path = os.path.abspath(os.path.join(self.root, relative_path))
        if not full_path.startswith(self.root):
            raise ValueError(f"Access denied: {relative_path} is outside {self.root}")
        return full_path
    
    @property
    def tools(self) -> List[Any]:
        """Export tool functions for Pydantic-AI."""
        # In a real implementation, we would wrap these as pydantic-ai Tools.
        # For this bootstrapper, we return the methods directly 
        # (assuming Agent class handles method inspection or we add decorators later)
        return [self.list_files, self.read_file]

"""
Native Messaging Host for FILESYST Domain
Handles filesystem operations from Chrome Extension via Native Messaging protocol

Usage:
  python host.py

Install:
  1. Register manifest at %LOCALAPPDATA%\Google\Chrome\NativeMessagingHosts\com.collider.filesyst.json
  2. Point to this script with pythonw.exe

Protocol:
  - Receives JSON messages with 4-byte length prefix (little-endian)
  - Sends JSON responses with same format
"""

import sys
import json
import struct
import os
from pathlib import Path
from typing import Any
import logging

# Configure logging to file (since stdout is used for messaging)
log_path = Path(__file__).parent / "native_host.log"
logging.basicConfig(
    filename=str(log_path),
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Allowed root paths for security
ALLOWED_ROOTS = [
    Path.home(),
    Path("D:/FFS0_Factory"),  # Development workspace
]

def is_path_allowed(path: Path) -> bool:
    """Check if path is within allowed roots"""
    try:
        resolved = path.resolve()
        return any(
            resolved == root or root in resolved.parents
            for root in ALLOWED_ROOTS
        )
    except Exception:
        return False


def read_message() -> dict | None:
    """Read a message from stdin (Chrome Native Messaging protocol)"""
    # Read 4-byte length prefix
    raw_length = sys.stdin.buffer.read(4)
    if not raw_length:
        return None
    
    message_length = struct.unpack("<I", raw_length)[0]
    
    # Read message body
    message_bytes = sys.stdin.buffer.read(message_length)
    message = json.loads(message_bytes.decode("utf-8"))
    
    logger.debug(f"Received: {message}")
    return message


def send_message(message: dict) -> None:
    """Send a message to stdout (Chrome Native Messaging protocol)"""
    encoded = json.dumps(message).encode("utf-8")
    length_prefix = struct.pack("<I", len(encoded))
    
    sys.stdout.buffer.write(length_prefix)
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()
    
    logger.debug(f"Sent: {message}")


def handle_list(path: str, options: dict | None = None) -> dict:
    """List directory contents"""
    target = Path(path).expanduser()
    
    if not is_path_allowed(target):
        return {"success": False, "error": f"Path not allowed: {path}"}
    
    if not target.exists():
        return {"success": False, "error": f"Path does not exist: {path}"}
    
    if not target.is_dir():
        return {"success": False, "error": f"Not a directory: {path}"}
    
    entries = []
    try:
        for entry in target.iterdir():
            entry_info = {
                "name": entry.name,
                "type": "directory" if entry.is_dir() else "file",
            }
            if entry.is_file():
                try:
                    entry_info["size"] = entry.stat().st_size
                except OSError:
                    entry_info["size"] = 0
            entries.append(entry_info)
        
        # Sort: directories first, then files, alphabetically
        entries.sort(key=lambda e: (e["type"] != "directory", e["name"].lower()))
        
        return {
            "success": True,
            "data": {
                "path": str(target),
                "entries": entries,
            }
        }
    except PermissionError:
        return {"success": False, "error": f"Permission denied: {path}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def handle_read(path: str, options: dict | None = None) -> dict:
    """Read file contents"""
    target = Path(path).expanduser()
    
    if not is_path_allowed(target):
        return {"success": False, "error": f"Path not allowed: {path}"}
    
    if not target.exists():
        return {"success": False, "error": f"File does not exist: {path}"}
    
    if not target.is_file():
        return {"success": False, "error": f"Not a file: {path}"}
    
    # Check file size (limit to 1MB for safety)
    max_size = options.get("max_size", 1024 * 1024) if options else 1024 * 1024
    try:
        size = target.stat().st_size
        if size > max_size:
            return {"success": False, "error": f"File too large: {size} bytes (max {max_size})"}
        
        # Try to read as text, fall back to binary info
        try:
            content = target.read_text(encoding="utf-8")
            return {
                "success": True,
                "data": {
                    "path": str(target),
                    "content": content,
                    "encoding": "utf-8",
                    "size": size,
                }
            }
        except UnicodeDecodeError:
            return {
                "success": True,
                "data": {
                    "path": str(target),
                    "binary": True,
                    "size": size,
                    "content": None,
                }
            }
    except PermissionError:
        return {"success": False, "error": f"Permission denied: {path}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def handle_write(path: str, content: str, options: dict | None = None) -> dict:
    """Write content to file"""
    target = Path(path).expanduser()
    
    if not is_path_allowed(target):
        return {"success": False, "error": f"Path not allowed: {path}"}
    
    # Create parent directories if needed
    create_dirs = options.get("create_dirs", True) if options else True
    if create_dirs:
        target.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        target.write_text(content, encoding="utf-8")
        return {
            "success": True,
            "data": {
                "path": str(target),
                "size": len(content.encode("utf-8")),
            }
        }
    except PermissionError:
        return {"success": False, "error": f"Permission denied: {path}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def handle_search(path: str, pattern: str, options: dict | None = None) -> dict:
    """Search for files matching pattern"""
    target = Path(path).expanduser()
    
    if not is_path_allowed(target):
        return {"success": False, "error": f"Path not allowed: {path}"}
    
    if not target.exists():
        return {"success": False, "error": f"Path does not exist: {path}"}
    
    max_results = options.get("max_results", 100) if options else 100
    include_content = options.get("include_content", False) if options else False
    
    matches = []
    try:
        for match in target.rglob(pattern):
            if len(matches) >= max_results:
                break
            
            match_info: dict[str, Any] = {
                "path": str(match.relative_to(target)),
                "type": "directory" if match.is_dir() else "file",
            }
            
            if include_content and match.is_file():
                try:
                    content = match.read_text(encoding="utf-8")[:500]  # First 500 chars
                    match_info["preview"] = content
                except Exception:
                    pass
            
            matches.append(match_info)
        
        return {
            "success": True,
            "data": {
                "path": str(target),
                "pattern": pattern,
                "matches": matches,
                "truncated": len(matches) >= max_results,
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def handle_sync(path: str, options: dict | None = None) -> dict:
    """Get full directory tree for sync"""
    target = Path(path).expanduser()
    
    if not is_path_allowed(target):
        return {"success": False, "error": f"Path not allowed: {path}"}
    
    if not target.exists():
        return {"success": False, "error": f"Path does not exist: {path}"}
    
    max_depth = options.get("max_depth", 3) if options else 3
    
    def build_tree(p: Path, depth: int) -> dict:
        node = {
            "name": p.name or str(p),
            "path": str(p),
            "type": "directory" if p.is_dir() else "file",
        }
        
        if p.is_dir() and depth < max_depth:
            children = []
            try:
                for child in sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                    if not child.name.startswith("."):  # Skip hidden
                        children.append(build_tree(child, depth + 1))
            except PermissionError:
                pass
            node["children"] = children
        
        return node
    
    try:
        tree = build_tree(target, 0)
        return {
            "success": True,
            "data": tree,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def process_message(message: dict) -> dict:
    """Route message to appropriate handler"""
    action = message.get("action", message.get("type"))
    path = message.get("path", "")
    content = message.get("content", "")
    pattern = message.get("pattern", "*")
    options = message.get("options", {})
    
    handlers = {
        "list": lambda: handle_list(path, options),
        "read": lambda: handle_read(path, options),
        "write": lambda: handle_write(path, content, options),
        "search": lambda: handle_search(path, pattern, options),
        "sync": lambda: handle_sync(path, options),
        "ping": lambda: {"success": True, "data": {"message": "pong", "version": "1.0.0"}},
    }
    
    handler = handlers.get(action)
    if handler:
        return handler()
    
    return {"success": False, "error": f"Unknown action: {action}"}


def main():
    """Main loop - read and process messages"""
    logger.info("Native host started")
    
    try:
        while True:
            message = read_message()
            if message is None:
                logger.info("No more messages, exiting")
                break
            
            response = process_message(message)
            send_message(response)
            
    except Exception as e:
        logger.exception("Fatal error in main loop")
        send_message({"success": False, "error": str(e)})
    
    logger.info("Native host stopped")


if __name__ == "__main__":
    main()

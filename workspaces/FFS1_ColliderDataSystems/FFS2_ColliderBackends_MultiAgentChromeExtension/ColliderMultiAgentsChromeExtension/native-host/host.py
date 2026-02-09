#!/usr/bin/env python3
"""Collider Native Messaging Host.

Handles file system operations from the Chrome extension via native messaging.
Install: Register this host in the Chrome native messaging manifest.

Protocol: Length-prefixed JSON messages on stdin/stdout.
"""

from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

import yaml


def read_message() -> dict:
    """Read a native messaging message from stdin."""
    raw_length = sys.stdin.buffer.read(4)
    if not raw_length:
        sys.exit(0)
    length = struct.unpack("=I", raw_length)[0]
    data = sys.stdin.buffer.read(length)
    return json.loads(data.decode("utf-8"))


def send_message(message: dict) -> None:
    """Write a native messaging message to stdout."""
    encoded = json.dumps(message).encode("utf-8")
    sys.stdout.buffer.write(struct.pack("=I", len(encoded)))
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()


def handle_read_file(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return {"success": False, "error": f"File not found: {path}"}
    if not p.is_file():
        return {"success": False, "error": f"Not a file: {path}"}
    content = p.read_text(encoding="utf-8")
    return {"success": True, "data": {"path": str(p), "content": content}}


def handle_write_file(path: str, content: str) -> dict:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return {"success": True, "data": {"path": str(p), "written": len(content)}}


def handle_list_dir(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return {"success": False, "error": f"Directory not found: {path}"}
    if not p.is_dir():
        return {"success": False, "error": f"Not a directory: {path}"}
    entries = []
    for entry in sorted(p.iterdir()):
        entries.append(
            {
                "name": entry.name,
                "type": "directory" if entry.is_dir() else "file",
                "size": entry.stat().st_size if entry.is_file() else None,
            }
        )
    return {"success": True, "data": {"path": str(p), "entries": entries}}


def handle_read_agent_context(path: str) -> dict:
    agent_dir = Path(path) / ".agent"
    if not agent_dir.exists():
        return {"success": False, "error": f".agent not found at: {path}"}
    container: dict = {}
    manifest_path = agent_dir / "manifest.yaml"
    if manifest_path.exists():
        container["manifest"] = (
            yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
        )
    for subdir in ["instructions", "rules", "skills", "knowledge"]:
        dir_path = agent_dir / subdir
        if dir_path.exists():
            container[subdir] = [
                f.read_text(encoding="utf-8")
                for f in sorted(dir_path.iterdir())
                if f.is_file() and f.suffix in (".md", ".txt")
            ]
    for subdir in ["tools", "workflows"]:
        dir_path = agent_dir / subdir
        if dir_path.exists():
            items = []
            for f in sorted(dir_path.iterdir()):
                if f.suffix in (".yaml", ".yml"):
                    data = yaml.safe_load(f.read_text(encoding="utf-8"))
                    if data:
                        items.append(data)
            container[subdir] = items
    configs_dir = agent_dir / "configs"
    if configs_dir.exists():
        configs = {}
        for f in sorted(configs_dir.iterdir()):
            if f.suffix in (".yaml", ".yml"):
                data = yaml.safe_load(f.read_text(encoding="utf-8"))
                if data:
                    configs[f.stem] = data
        container["configs"] = configs
    return {"success": True, "data": container}


def main() -> None:
    while True:
        message = read_message()
        action = message.get("action", "")
        path = message.get("path", "")
        if action == "read_file":
            response = handle_read_file(path)
        elif action == "write_file":
            content = message.get("content", "")
            response = handle_write_file(path, content)
        elif action == "list_dir":
            response = handle_list_dir(path)
        elif action == "read_agent_context":
            response = handle_read_agent_context(path)
        else:
            response = {"success": False, "error": f"Unknown action: {action}"}
        send_message(response)


if __name__ == "__main__":
    main()

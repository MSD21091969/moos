"""
File Cache Service - Caches canvas files to session working directory.

Storage: I:\system\.cache\{session_id}\{filename}
Eviction: Per-session (cleared on session end)
"""
import os
import shutil
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Base cache directory
CACHE_BASE = r"I:\system\.cache"


def get_cache_dir(session_id: str) -> str:
    """Get the cache directory for a session."""
    cache_dir = os.path.join(CACHE_BASE, session_id)
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


def cache_file(session_id: str, source_path: str) -> Optional[str]:
    """
    Cache a file from source path to session cache.
    Returns the cached file path, or None if source doesn't exist.
    """
    if not os.path.exists(source_path):
        logger.warning(f"Source file not found: {source_path}")
        return None
    
    cache_dir = get_cache_dir(session_id)
    filename = os.path.basename(source_path)
    cached_path = os.path.join(cache_dir, filename)
    
    # Copy file to cache
    shutil.copy2(source_path, cached_path)
    logger.info(f"Cached file: {source_path} -> {cached_path}")
    
    return cached_path


def get_cached_file_path(session_id: str, filename: str) -> Optional[str]:
    """Get the path to a cached file if it exists."""
    cache_dir = get_cache_dir(session_id)
    cached_path = os.path.join(cache_dir, filename)
    
    if os.path.exists(cached_path):
        return cached_path
    return None


def read_cached_file(session_id: str, filename: str) -> Optional[str]:
    """Read the content of a cached file as text."""
    cached_path = get_cached_file_path(session_id, filename)
    if not cached_path:
        return None
    
    try:
        with open(cached_path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        # Binary file - return indication
        return f"[Binary file: {filename}]"
    except Exception as e:
        logger.error(f"Failed to read cached file {filename}: {e}")
        return None


def clear_session_cache(session_id: str) -> bool:
    """Clear all cached files for a session."""
    cache_dir = os.path.join(CACHE_BASE, session_id)
    
    if os.path.exists(cache_dir):
        shutil.rmtree(cache_dir)
        logger.info(f"Cleared cache for session: {session_id}")
        return True
    return False


def list_cached_files(session_id: str) -> list[str]:
    """List all cached files for a session."""
    cache_dir = os.path.join(CACHE_BASE, session_id)
    
    if not os.path.exists(cache_dir):
        return []
    
    return [f for f in os.listdir(cache_dir) if os.path.isfile(os.path.join(cache_dir, f))]


# === Text Extraction (Phase 1: basic formats) ===

def extract_text(file_path: str) -> Optional[str]:
    """
    Extract text content from a file.
    Phase 1: txt, json, md, py, etc.
    Phase 2: PDF, DOCX (requires additional libs)
    """
    ext = Path(file_path).suffix.lower()
    
    # Plain text formats
    text_formats = {'.txt', '.md', '.json', '.py', '.js', '.ts', '.html', '.css', 
                    '.yaml', '.yml', '.xml', '.csv', '.log', '.ini', '.cfg', '.toml'}
    
    if ext in text_formats:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, "r", encoding="latin-1") as f:
                    return f.read()
            except Exception:
                return None
    
    # TODO Phase 2: PDF extraction
    if ext == '.pdf':
        return f"[PDF file - extraction not yet implemented: {os.path.basename(file_path)}]"
    
    # TODO Phase 2: DOCX extraction
    if ext in {'.docx', '.doc'}:
        return f"[Word document - extraction not yet implemented: {os.path.basename(file_path)}]"
    
    # Images - no text extraction (use vision tool)
    if ext in {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}:
        return f"[Image file - use vision tool: {os.path.basename(file_path)}]"
    
    return f"[Unsupported format: {ext}]"

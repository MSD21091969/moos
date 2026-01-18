"""
Dependencies and Configuration for Agent Studio

Provides:
- GCP configuration
- SessionManager for multi-user Docker sandboxes
- Per-session dependency factory with persistent storage on I:/users
"""
import os
from typing import Optional
from pydantic_ai_backends import FilesystemBackend, SessionManager

from pydantic_deep import DeepAgentDeps

# GCP Configuration
GCP_PROJECT = "mailmind-ai-djbuw"
GCP_REGION = "us-central1"
KEY_PATH = r"D:\my-tiny-data-collider\mailmind-ai-djbuw-50d63f821f84.json"

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_DIR = os.path.join(BASE_DIR, "skills")
# Persistent User Storage on I:\
USERS_ROOT = r"I:\users"
DATA_DIR = os.path.join(BASE_DIR, "data") # Fallback/shared data
DB_PATH = os.path.join(DATA_DIR, "conversations.db")

# Global SessionManager for multi-user isolation
_session_manager: Optional[SessionManager] = None
_use_docker = os.getenv("USE_DOCKER_SANDBOX", "false").lower() == "true"


def configure_gcp():
    """Set GCP environment variables."""
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = KEY_PATH
    os.environ["GOOGLE_CLOUD_PROJECT"] = GCP_PROJECT
    os.environ["GOOGLE_CLOUD_REGION"] = GCP_REGION
    os.environ["LOCATION"] = GCP_REGION


def get_session_manager() -> SessionManager:
    """Get or create the global SessionManager."""
    global _session_manager
    if _session_manager is None:
        # Configuring SessionManager to use host mounts if available
        # or managing volume persistency.
        _session_manager = SessionManager(
            default_runtime="python-datascience",
            default_idle_timeout=3600,  # 1 hour
        )
        _session_manager.start_cleanup_loop(interval=300)  # 5 min cleanup
    return _session_manager


async def get_deps_for_session(session_id: str, email: Optional[str] = None) -> DeepAgentDeps:
    """Create dependencies with isolated sandbox for a session.
    
    Args:
        session_id: Unique session identifier (e.g., WebSocket connection ID or User ID)
        email: User email address to be used for folder naming (optional)
        
    Returns:
        DeepAgentDeps with DockerSandbox or FilesystemBackend
    """
    configure_gcp()
    
    # Ensure the root users directory exists on I:\
    try:
        os.makedirs(USERS_ROOT, exist_ok=True)
    except Exception as e:
        # Fallback to local data if I:\ is not accessible
        print(f"Warning: Could not access {USERS_ROOT}, falling back to local DATA_DIR. Error: {e}")
        root = DATA_DIR
    else:
        root = USERS_ROOT

    # If email is provided, use it for the directory name to make it human-readable
    # Otherwise fallback to the session_id (which is usually the User ID)
    dir_name = email if email else session_id
    session_dir = os.path.join(root, dir_name)
    os.makedirs(session_dir, exist_ok=True)
    
    if _use_docker:
        # Docker mode: isolated container per session
        manager = get_session_manager()
        # Note: In a real production setup, we'd configure the manager 
        # to mount session_dir as a volume in the container.
        sandbox = await manager.get_or_create(session_id)
        return DeepAgentDeps(backend=sandbox)
    else:
        # Filesystem mode: persistent folder on I:\users for this session
        backend = FilesystemBackend(session_dir)
        return DeepAgentDeps(backend=backend)


def get_deps() -> DeepAgentDeps:
    """Create and return agent dependencies (sync version for simple cases)."""
    configure_gcp()
    os.makedirs(DATA_DIR, exist_ok=True)
    backend = FilesystemBackend(DATA_DIR)
    return DeepAgentDeps(backend=backend)


async def release_session(session_id: str) -> bool:
    """Release a session and clean up its sandbox."""
    if _session_manager is not None:
        return await _session_manager.release(session_id)
    return False

import os
from pydantic_ai_backends import FilesystemBackend
from pydantic_deep import DeepAgentDeps

# Configuration
GCP_PROJECT = "mailmind-ai-djbuw"
GCP_REGION = "us-central1"
KEY_PATH = r"D:\my-tiny-data-collider\mailmind-ai-djbuw-50d63f821f84.json"
STORAGE_PATH = "./data/full-stack-storage"

def get_deps() -> DeepAgentDeps:
    """
    Configures and returns the dependencies for the Deep Agent.
    - Sets GCP Environment variables.
    - Initializes FilesystemBackend for persistence.
    """
    # 1. Ensure GCP Auth
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = KEY_PATH
    os.environ["GOOGLE_CLOUD_PROJECT"] = GCP_PROJECT
    os.environ["GOOGLE_CLOUD_REGION"] = GCP_REGION
    os.environ["LOCATION"] = GCP_REGION
    
    # 2. Ensure Storage Directory
    os.makedirs(STORAGE_PATH, exist_ok=True)
    
    # 3. Create Filesystem Backend
    # Note: FilesystemBackend takes the root path as a string argument
    backend = FilesystemBackend(STORAGE_PATH)
    
    return DeepAgentDeps(backend=backend)

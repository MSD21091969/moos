"""
Script to run Alembic migrations for ColliderDataServer.
Wraps 'alembic upgrade head'.
"""
import os
import subprocess
import sys
from pathlib import Path

# Path to DataServer
SERVER_DIR = Path("../../ColliderDataServer").resolve()

def run_migrations():
    """Run alembic upgrade head in the Data Server directory."""
    if not SERVER_DIR.exists():
        print(f"Error: Could not find server directory at {SERVER_DIR}")
        sys.exit(1)

    print(f"Running migrations in {SERVER_DIR}...")
    
    # Check if alembic.ini exists
    if not (SERVER_DIR / "alembic.ini").exists():
        print("Error: alembic.ini not found.")
        sys.exit(1)

    try:
        # Run using 'uv run' to ensure venv context
        subprocess.run(
            ["uv", "run", "alembic", "upgrade", "head"],
            cwd=SERVER_DIR,
            check=True
        )
        print("Migrations applied successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_migrations()

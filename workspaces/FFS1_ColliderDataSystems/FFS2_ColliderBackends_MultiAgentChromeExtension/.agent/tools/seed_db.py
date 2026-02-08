"""
Script to seed the Collider database with initial data.
Wraps 'src.seed'.
"""
import subprocess
import sys
from pathlib import Path

# Path to DataServer
SERVER_DIR = Path("../../ColliderDataServer").resolve()

def seed_database():
    """Run the seed script."""
    if not SERVER_DIR.exists():
        print(f"Error: Could not find server directory at {SERVER_DIR}")
        sys.exit(1)

    print(f"Seeding database in {SERVER_DIR}...")

    try:
        # Run module src.seed
        subprocess.run(
            ["uv", "run", "python", "-m", "src.seed"],
            cwd=SERVER_DIR,
            check=True
        )
        print("Database seeded successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Seeding failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    seed_database()

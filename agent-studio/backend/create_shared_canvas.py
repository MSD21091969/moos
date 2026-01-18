import asyncio
import aiosqlite
import uuid
from app.db import DB_PATH

async def create_shared_canvas():
    user_id = "user123" # Mock User ID for the "Owner"
    name = "Project Alpha Blueprint"
    container_id = "container-alpha-001"
    canvas_id = str(uuid.uuid4())
    files_json = "[]"
    
    print(f"Creating Shared Canvas...")
    print(f"Name: {name}")
    print(f"Container ID: {container_id}")
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO canvasses (id, user_id, container_id, name, files) VALUES (?, ?, ?, ?, ?)",
            (canvas_id, user_id, container_id, name, files_json)
        )
        await db.commit()
    
    print("-" * 50)
    print("SUCCESS! Shared Canvas Created.")
    print(f"Canvas ID: {canvas_id}")
    print(f"Test URL: http://localhost:3000/?canvas={canvas_id}")
    print("-" * 50)

if __name__ == "__main__":
    import os
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        print("Please run the backend server at least once to initialize the DB.")
    else:
        asyncio.run(create_shared_canvas())

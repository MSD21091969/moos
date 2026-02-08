import asyncio
import aiosqlite
import json

from app.db import DB_PATH

async def inspect_canvas():
    canvas_id = "88deb841-4c94-408e-84f4-cfebe9876cf9"
    # db_path = "agent_studio.db" - WRONG, use imported DB_PATH
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT id, name, container_id FROM canvasses') as cursor:
            rows = await cursor.fetchall()
            print(f"Found {len(rows)} canvases:")
            for row in rows:
                print(dict(row))

if __name__ == "__main__":
    asyncio.run(inspect_canvas())

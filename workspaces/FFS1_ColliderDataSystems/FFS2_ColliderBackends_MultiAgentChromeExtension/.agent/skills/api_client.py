"""
Simple API Client for interacting with ColliderDataServer.
Useful for checking server health or creating test data from the Agent context.
"""
import httpx
import asyncio
import os

BASE_URL = os.getenv("DATA_SERVER_URL", "http://localhost:8000/api/v1")

class ColliderClient:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url)

    async def close(self):
        await self.client.aclose()

    async def check_health(self) -> bool:
        """Check if server is healthy."""
        try:
            resp = await self.client.get("/health")
            return resp.status_code == 200
        except Exception:
            return False

    async def get_apps(self) -> list[dict]:
        """List registered applications."""
        resp = await self.client.get("/apps")
        resp.raise_for_status()
        return resp.json()

    async def create_node(self, app_id: str, path: str, content: str):
        """Create a new node."""
        payload = {
            "path": path,
            "content": content,
            "type": "file"
        }
        resp = await self.client.post(f"/apps/{app_id}/nodes", json=payload)
        resp.raise_for_status()
        return resp.json()

# Example Usage
if __name__ == "__main__":
    async def main():
        client = ColliderClient()
        if await client.check_health():
            print("Server is UP")
            try:
                apps = await client.get_apps()
                print(f"Found {len(apps)} apps: {[a['id'] for a in apps]}")
            except Exception as e:
                print(f"Error fetching apps: {e}")
        else:
            print("Server is DOWN")
        await client.close()

    asyncio.run(main())

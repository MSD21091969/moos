import asyncio
import websockets
import requests
import json
import sys

# Login to get valid token
BASE_URL = "http://127.0.0.1:8000"

async def test_ws():
    print(f"1. Logging in to {BASE_URL}...")
    try:
        resp = requests.post(f"{BASE_URL}/api/login", data={
            "username": "superuser@test.com",
            "password": "test123"
        })
        if resp.status_code != 200:
            print(f"Login Failed: {resp.status_code} {resp.text}")
            return
        
        token = resp.json()["access_token"]
        print(f"Login Success. Token: {token[:10]}...")
    except Exception as e:
        print(f"Connection refused during login (Server down?): {e}")
        return

    ws_url = f"ws://127.0.0.1:8000/ws/chat?token={token}"
    print(f"2. Connecting to WebSocket: {ws_url}")
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print("   [WS] Connected!")
            
            # Wait for initial skills update
            msg = await websocket.recv()
            print(f"   [WS] Received: {msg[:100]}...")
            
            # Send a ping
            print("   [WS] Sending ping...")
            await websocket.send(json.dumps({"type": "ping", "content": "hello"}))
            
            # Wait a bit
            await asyncio.sleep(2)
            print("   [WS] Closing...")
            
    except websockets.exceptions.ConnectionClosed as e:
        print(f"   [WS] Closed Unexpectedly: Code={e.code}, Reason={e.reason}")
    except Exception as e:
        print(f"   [WS] Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_ws())

import requests
import sys

BASE_URL = "http://localhost:8000"

def test_connection():
    # 1. Login
    print(f"Logging in to {BASE_URL}...")
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
        
        # 2. Test /api/files
        print("Testing /api/files...")
        files_resp = requests.get(f"{BASE_URL}/api/files", headers={
            "Authorization": f"Bearer {token}"
        })
        
        if files_resp.status_code == 200:
            print(f"Files API Success: {files_resp.json()}")
        else:
            print(f"Files API Failed: {files_resp.status_code} {files_resp.text}")

    except Exception as e:
        print(f"Connection Error: {e}")

if __name__ == "__main__":
    test_connection()

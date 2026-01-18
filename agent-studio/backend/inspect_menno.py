
import sqlite3
import os

# Use agent_studio.db this time to be sure
DB_PATH = r"D:\agent-factory\agent-studio\backend\agent_studio.db"

def inspect_menno():
    if not os.path.exists(DB_PATH):
        print(f"Error: {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Check users table
        print("--- USERS ---")
        cursor.execute("SELECT id, email FROM users")
        for row in cursor.fetchall():
            print(dict(row))
            
        # Check canvasses
        print("\n--- CANVASSES ---")
        cursor.execute("SELECT id, name, files, user_id, container_id FROM canvasses")
        for row in cursor.fetchall():
            print(f"Canvas: {row['name']}")
            print(f"  Files: {row['files']}")
            print(f"  Owner: {row['user_id']}")
            print("-" * 20)
            
    except Exception as e:
        print(f"Error inspecting DB: {e}")
        
    conn.close()

if __name__ == "__main__":
    inspect_menno()

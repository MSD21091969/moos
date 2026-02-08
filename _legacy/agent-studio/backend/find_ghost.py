
import sqlite3
import os

DB_PATH = r"D:\agent-factory\agent-studio\backend\data\conversations.db"

def find_weird_canvas():
    print(f"Checking {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Search for the weird name
    target_name = "New Canvassdafsdfvasdfasdfasd"
    print(f"Searching for canvas: '{target_name}'")
    
    cursor.execute("SELECT * FROM canvasses WHERE name LIKE ?", ('%' + target_name + '%',))
    rows = cursor.fetchall()
    
    if not rows:
        print("❌ NOT FOUND. Dumping all canvas names:")
        cursor.execute("SELECT name, user_id FROM canvasses")
        for r in cursor.fetchall():
            print(f" - {r['name']} (User: {r['user_id']})")
    else:
        print(f"✅ FOUND {len(rows)} matches!")
        for r in rows:
            print(f"ID: {r['id']}")
            print(f"Name: {r['name']}")
            print(f"Files: {r['files']}")
            print("-" * 20)

    conn.close()

if __name__ == "__main__":
    find_weird_canvas()

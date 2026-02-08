
import sqlite3
import os

DB_PATH = r"D:\agent-factory\agent-studio\backend\data\conversations.db"

def scan_files():
    print(f"Scanning {DB_PATH} for remaining files...")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, files FROM canvasses")
    rows = cursor.fetchall()
    
    found = False
    for r in rows:
        files = r['files']
        # Check raw string for safety
        if "ageeth" in files or "4396_" in files:
            print(f"🚨 FOUND in Canvas '{r['name']}' (ID: {r['id']})")
            print(f"   Raw Content: {files}")
            found = True
            
    if not found:
        print("✅ Clean. No forbidden files found in any canvas.")

    conn.close()

if __name__ == "__main__":
    scan_files()

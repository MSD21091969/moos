
import sqlite3
import os

DB_PATH = r"D:\agent-factory\agent-studio\backend\data\conversations.db"

def kill_ghost_canvas():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    target_name = "New Canvassdafsdfvasdfasdfasd"
    print(f"Deleting canvas: '{target_name}'...")
    
    cursor.execute("DELETE FROM canvasses WHERE name = ?", (target_name,))
    
    if cursor.rowcount > 0:
        print(f"SUCCESS: Deleted {cursor.rowcount} canvas(ses).")
    else:
        print("Not found (maybe already deleted?).")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    kill_ghost_canvas()

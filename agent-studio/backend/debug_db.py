
import sqlite3
import os

DB_PATH = r"D:\agent-factory\agent-studio\backend\data\conversations.db"

if not os.path.exists(DB_PATH):
    print(f"Database not found at {DB_PATH}")
    exit(1)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

def print_table(table_name):
    print(f"\n--- Table: {table_name} ---")
    try:
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        # Get headers
        headers = [description[0] for description in cursor.description]
        print(" | ".join(headers))
        print("-" * (len(headers) * 10))
        
        if not rows:
            print("(Empty)")
        else:
            for row in rows:
                print(row)
    except Exception as e:
        print(f"Error reading {table_name}: {e}")

print_table("users")
print_table("containers")
print_table("container_acl")
print_table("canvasses")

conn.close()

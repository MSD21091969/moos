import argparse
import asyncio
from typing import List
from google.cloud import firestore

# Keep these users
KEEP_EMAILS = {
    "enterprise@test.com",
    "pro@test.com",
    "test@test.com"
}

def cleanup_firestore(project_id: str, database_id: str, dry_run: bool = False):
    print(f"🔌 Connecting to Firestore project: {project_id}, database: {database_id}")
    db = firestore.Client(project=project_id, database=database_id)

    # Get all top-level collections
    collections = list(db.collections())
    print(f"found {len(collections)} top-level collections: {[c.id for c in collections]}")

    for collection in collections:
        coll_id = collection.id
        print(f"\n📂 Processing collection: {coll_id}")

        if coll_id == "users":
            # Special handling for users
            process_users_collection(db, collection, dry_run)
        else:
            # Delete everything else
            delete_entire_collection(db, collection, dry_run)

def process_users_collection(db: firestore.Client, collection, dry_run: bool):
    docs = list(collection.stream())
    print(f"   Found {len(docs)} user documents.")
    
    for doc in docs:
        data = doc.to_dict()
        email = data.get("email")
        doc_id = doc.id
        
        # Check if we should keep this user
        # We check both the 'email' field and the document ID (just in case)
        should_keep = (email in KEEP_EMAILS) or (doc_id in KEEP_EMAILS)
        
        if should_keep:
            print(f"   ✅ Keeping user: {doc_id} ({email})")
        else:
            if dry_run:
                print(f"   [DRY RUN] Would delete user: {doc_id} ({email})")
            else:
                print(f"   🗑️ Deleting user: {doc_id} ({email})")
                # Use recursive delete to ensure subcollections (if any) are gone
                db.recursive_delete(doc.reference)

def delete_entire_collection(db: firestore.Client, collection, dry_run: bool):
    # For non-user collections, we want to delete everything.
    # recursive_delete on a collection reference deletes all documents and subcollections.
    
    # Note: recursive_delete might not be directly callable on collection in all versions,
    # but usually we pass the reference to client.recursive_delete
    
    print(f"   WARNING: Wiping entire collection '{collection.id}'")
    
    # To be safe and show progress, let's count first (optional, but good for logs)
    # docs = list(collection.limit(5).stream())
    # if not docs:
    #     print("   (Empty collection)")
    #     return

    if dry_run:
        print(f"   [DRY RUN] Would recursively delete collection: {collection.id}")
    else:
        print(f"   🗑️ Recursively deleting collection: {collection.id}")
        # db.recursive_delete(collection) # This deletes documents in the collection
        # But wait, recursive_delete takes a reference.
        # Let's use the bulk writer for efficiency if needed, but standard call is fine.
        db.recursive_delete(collection)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cleanup Firestore data")
    parser.add_argument("--project", type=str, default="my-tiny-data-collider", help="GCP Project ID")
    parser.add_argument("--database", type=str, default="(default)", help="Firestore Database ID")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without executing")
    
    args = parser.parse_args()
    
    cleanup_firestore(args.project, args.database, args.dry_run)

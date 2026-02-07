#!/usr/bin/env python
"""Clean up Firestore test data."""

from google.cloud import firestore

db = firestore.Client(project='mailmind-ai-djbuw', database='my-tiny-data-collider')

# Delete all sessions first (children of usersessions)
print("🗑️  Deleting sessions...")
sessions = db.collection('sessions').stream()
session_count = 0
for doc in sessions:
    # Delete resources subcollection
    resources = doc.reference.collection('resources').stream()
    for res_doc in resources:
        res_doc.reference.delete()
    
    doc.reference.delete()
    session_count += 1

print(f"✅ Deleted {session_count} sessions and their resources")

# Get all usersessions
print("🗑️  Deleting usersessions...")
usersessions = db.collection('usersessions').stream()
usersession_ids = [doc.id for doc in usersessions]

# Delete all usersessions and their resources
for usersession_id in usersession_ids:
    usersession_ref = db.collection('usersessions').document(usersession_id)
    
    # Delete resources subcollection
    resources = usersession_ref.collection('resources').stream()
    for res_doc in resources:
        res_doc.reference.delete()
    
    usersession_ref.delete()

print(f"✅ Deleted {len(usersession_ids)} UserSessions and their resources")
print("🧹 Firestore cleaned up!")

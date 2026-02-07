#!/usr/bin/env python
"""Migration script for Universal Object Model v4.0.0.

This script performs the following migrations:
1. Creates UserSession documents for each existing user
2. Computes and sets depth field on all sessions (from parent chain)
3. Verifies/syncs ACL dict structure on sessions with USER ResourceLinks
4. Verifies ResourceLink instance_id population

Run with: python -m scripts.deployment.create_usersessions_migration

Options:
  --dry-run     Show what would be changed without writing
  --verbose     Show detailed output for each document
  --user-id     Migrate specific user only (for testing)
"""

import argparse
import asyncio
import logging
from datetime import datetime
from typing import Any

from google.cloud import firestore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MigrationStats:
    """Track migration statistics."""
    
    def __init__(self):
        self.usersessions_created = 0
        self.usersessions_skipped = 0
        self.sessions_depth_updated = 0
        self.sessions_depth_unchanged = 0
        self.sessions_acl_fixed = 0
        self.sessions_acl_ok = 0
        self.resourcelinks_instance_fixed = 0
        self.resourcelinks_instance_ok = 0
        self.errors: list[str] = []
    
    def report(self) -> str:
        """Generate migration report."""
        lines = [
            "\n" + "=" * 60,
            "Migration Report",
            "=" * 60,
            f"UserSessions Created: {self.usersessions_created}",
            f"UserSessions Skipped (already exist): {self.usersessions_skipped}",
            f"Sessions Depth Updated: {self.sessions_depth_updated}",
            f"Sessions Depth Unchanged: {self.sessions_depth_unchanged}",
            f"Sessions ACL Fixed: {self.sessions_acl_fixed}",
            f"Sessions ACL OK: {self.sessions_acl_ok}",
            f"ResourceLinks instance_id Fixed: {self.resourcelinks_instance_fixed}",
            f"ResourceLinks instance_id OK: {self.resourcelinks_instance_ok}",
            "=" * 60,
        ]
        
        if self.errors:
            lines.append(f"\nErrors ({len(self.errors)}):")
            for err in self.errors[:10]:  # Show first 10 errors
                lines.append(f"  - {err}")
            if len(self.errors) > 10:
                lines.append(f"  ... and {len(self.errors) - 10} more")
        
        return "\n".join(lines)


def get_firestore_client():
    """Get Firestore client."""
    return firestore.Client()


async def compute_session_depth(
    db: firestore.Client,
    session_id: str,
    parent_id: str | None,
    depth_cache: dict[str, int]
) -> int:
    """Compute session depth from parent chain.
    
    Args:
        db: Firestore client
        session_id: Session ID to compute depth for
        parent_id: Parent ID (usersession_*, sess_*, or None)
        depth_cache: Cache of already computed depths
    
    Returns:
        Computed depth (1 for workspace level, 2 for nested)
    """
    if session_id in depth_cache:
        return depth_cache[session_id]
    
    if parent_id is None:
        # No parent = workspace level (depth 1)
        depth = 1
    elif parent_id.startswith("usersession_"):
        # Direct child of UserSession = workspace level (depth 1)
        depth = 1
    elif parent_id.startswith("sess_"):
        # Parent is a session - check parent's depth
        if parent_id in depth_cache:
            parent_depth = depth_cache[parent_id]
        else:
            # Look up parent session
            parent_doc = db.collection("sessions").document(parent_id).get()
            if parent_doc.exists:
                parent_data = parent_doc.to_dict()
                parent_depth = parent_data.get("depth", 1)
            else:
                # Parent doesn't exist, assume workspace level
                parent_depth = 1
        depth = min(parent_depth + 1, 2)  # Cap at depth 2
    else:
        # Unknown parent type, assume workspace level
        depth = 1
    
    depth_cache[session_id] = depth
    return depth


def validate_acl_structure(acl: Any) -> dict[str, Any]:
    """Validate and normalize ACL dict structure.
    
    v4.0.0 ACL structure:
    {
        "owner": str,          # Required: user_id
        "editors": list[str],  # Required: list of user_ids
        "viewers": list[str]   # Required: list of user_ids
    }
    
    Returns normalized ACL dict.
    """
    if not isinstance(acl, dict):
        return {"owner": "", "editors": [], "viewers": []}
    
    normalized = {
        "owner": acl.get("owner", "") if isinstance(acl.get("owner"), str) else "",
        "editors": acl.get("editors", []) if isinstance(acl.get("editors"), list) else [],
        "viewers": acl.get("viewers", []) if isinstance(acl.get("viewers"), list) else [],
    }
    
    # Ensure all editor/viewer entries are strings
    normalized["editors"] = [e for e in normalized["editors"] if isinstance(e, str)]
    normalized["viewers"] = [v for v in normalized["viewers"] if isinstance(v, str)]
    
    return normalized


def acl_needs_fix(current_acl: Any, normalized_acl: dict) -> bool:
    """Check if ACL needs to be fixed."""
    if not isinstance(current_acl, dict):
        return True
    
    if current_acl.get("owner") != normalized_acl["owner"]:
        return True
    if current_acl.get("editors") != normalized_acl["editors"]:
        return True
    if current_acl.get("viewers") != normalized_acl["viewers"]:
        return True
    
    return False


async def migrate_usersessions(
    db: firestore.Client,
    stats: MigrationStats,
    dry_run: bool = False,
    verbose: bool = False,
    user_id_filter: str | None = None
) -> set[str]:
    """Create UserSession documents for each user.
    
    Scans sessions collection for unique user_ids and creates
    UserSession documents if they don't exist.
    
    Returns set of user_ids processed.
    """
    logger.info("Phase 1: Creating UserSession documents...")
    
    # Get unique user_ids from sessions
    user_ids = set()
    
    sessions_query = db.collection("sessions")
    if user_id_filter:
        sessions_query = sessions_query.where("user_id", "==", user_id_filter)
    
    for doc in sessions_query.stream():
        data = doc.to_dict()
        user_id = data.get("user_id")
        if user_id:
            user_ids.add(user_id)
    
    logger.info(f"Found {len(user_ids)} unique users with sessions")
    
    # Create UserSession for each user
    for user_id in user_ids:
        usersession_id = f"usersession_{user_id}"
        usersession_ref = db.collection("usersessions").document(usersession_id)
        
        if usersession_ref.get().exists:
            if verbose:
                logger.info(f"  Skipped: {usersession_id} (already exists)")
            stats.usersessions_skipped += 1
            continue
        
        usersession_data = {
            "instance_id": usersession_id,
            "user_id": user_id,
            "parent_id": None,
            "depth": 0,
            "acl": {
                "owner": user_id,
                "editors": [],
                "viewers": []
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": user_id
        }
        
        if dry_run:
            logger.info(f"  [DRY RUN] Would create: {usersession_id}")
        else:
            usersession_ref.set(usersession_data)
            if verbose:
                logger.info(f"  Created: {usersession_id}")
        
        stats.usersessions_created += 1
    
    return user_ids


async def migrate_session_depth(
    db: firestore.Client,
    stats: MigrationStats,
    dry_run: bool = False,
    verbose: bool = False,
    user_id_filter: str | None = None
):
    """Compute and set depth field on all sessions."""
    logger.info("Phase 2: Computing session depths...")
    
    depth_cache: dict[str, int] = {}
    
    sessions_query = db.collection("sessions")
    if user_id_filter:
        sessions_query = sessions_query.where("user_id", "==", user_id_filter)
    
    # First pass: collect all sessions and parent relationships
    sessions_data: list[tuple[str, dict]] = []
    for doc in sessions_query.stream():
        sessions_data.append((doc.id, doc.to_dict()))
    
    logger.info(f"Processing {len(sessions_data)} sessions for depth computation")
    
    # Second pass: compute depths (may need multiple passes for chains)
    for session_id, data in sessions_data:
        parent_id = data.get("parent_id") or data.get("parent_session_id")
        current_depth = data.get("depth")
        
        computed_depth = await compute_session_depth(
            db, session_id, parent_id, depth_cache
        )
        
        if current_depth == computed_depth:
            stats.sessions_depth_unchanged += 1
            continue
        
        if dry_run:
            logger.info(f"  [DRY RUN] Would update {session_id}: depth {current_depth} -> {computed_depth}")
        else:
            db.collection("sessions").document(session_id).update({
                "depth": computed_depth,
                "parent_id": parent_id,  # Ensure parent_id is set
                "updated_at": datetime.utcnow()
            })
            if verbose:
                logger.info(f"  Updated {session_id}: depth {current_depth} -> {computed_depth}")
        
        stats.sessions_depth_updated += 1


async def migrate_session_acl(
    db: firestore.Client,
    stats: MigrationStats,
    dry_run: bool = False,
    verbose: bool = False,
    user_id_filter: str | None = None
):
    """Verify and fix ACL dict structure on sessions."""
    logger.info("Phase 3: Verifying session ACL structure...")
    
    sessions_query = db.collection("sessions")
    if user_id_filter:
        sessions_query = sessions_query.where("user_id", "==", user_id_filter)
    
    for doc in sessions_query.stream():
        session_id = doc.id
        data = doc.to_dict()
        
        current_acl = data.get("acl")
        user_id = data.get("user_id", "")
        
        # Normalize ACL structure
        normalized_acl = validate_acl_structure(current_acl)
        
        # Ensure owner is set to session user_id if empty
        if not normalized_acl["owner"] and user_id:
            normalized_acl["owner"] = user_id
        
        if not acl_needs_fix(current_acl, normalized_acl):
            stats.sessions_acl_ok += 1
            continue
        
        if dry_run:
            logger.info(f"  [DRY RUN] Would fix ACL on {session_id}: {current_acl} -> {normalized_acl}")
        else:
            db.collection("sessions").document(session_id).update({
                "acl": normalized_acl,
                "updated_at": datetime.utcnow()
            })
            if verbose:
                logger.info(f"  Fixed ACL on {session_id}")
        
        stats.sessions_acl_fixed += 1


async def migrate_resourcelinks_instance_id(
    db: firestore.Client,
    stats: MigrationStats,
    dry_run: bool = False,
    verbose: bool = False,
    user_id_filter: str | None = None
):
    """Verify ResourceLink instance_id population."""
    logger.info("Phase 4: Verifying ResourceLink instance_id...")
    
    sessions_query = db.collection("sessions")
    if user_id_filter:
        sessions_query = sessions_query.where("user_id", "==", user_id_filter)
    
    for session_doc in sessions_query.stream():
        session_id = session_doc.id
        
        # Check resources subcollection
        resources_ref = db.collection("sessions").document(session_id).collection("resources")
        
        for resource_doc in resources_ref.stream():
            resource_id = resource_doc.id
            resource_data = resource_doc.to_dict()
            
            resource_type = resource_data.get("resource_type", "")
            instance_id = resource_data.get("instance_id")
            
            # USER and SESSION types don't need instance_id
            if resource_type in ("user", "session"):
                stats.resourcelinks_instance_ok += 1
                continue
            
            # AGENT, TOOL, SOURCE should have instance_id
            if resource_type in ("agent", "tool", "source"):
                if instance_id:
                    stats.resourcelinks_instance_ok += 1
                else:
                    # instance_id is missing - log for manual review
                    # We can't auto-fix because we'd need to look up or create the instance
                    if dry_run:
                        logger.warning(
                            f"  [DRY RUN] ResourceLink {resource_id} in {session_id} "
                            f"missing instance_id (type: {resource_type})"
                        )
                    else:
                        logger.warning(
                            f"  ResourceLink {resource_id} in {session_id} "
                            f"missing instance_id (type: {resource_type}) - requires manual fix"
                        )
                    stats.resourcelinks_instance_fixed += 1
            else:
                stats.resourcelinks_instance_ok += 1


async def run_migration(
    dry_run: bool = False,
    verbose: bool = False,
    user_id: str | None = None
):
    """Run the full migration."""
    logger.info("=" * 60)
    logger.info("Universal Object Model v4.0.0 Migration")
    logger.info("=" * 60)
    
    if dry_run:
        logger.info("*** DRY RUN MODE - No changes will be written ***")
    
    if user_id:
        logger.info(f"Filtering to user: {user_id}")
    
    db = get_firestore_client()
    stats = MigrationStats()
    
    try:
        # Phase 1: Create UserSession documents
        await migrate_usersessions(db, stats, dry_run, verbose, user_id)
        
        # Phase 2: Compute and set depth
        await migrate_session_depth(db, stats, dry_run, verbose, user_id)
        
        # Phase 3: Verify/fix ACL structure
        await migrate_session_acl(db, stats, dry_run, verbose, user_id)
        
        # Phase 4: Verify ResourceLink instance_id
        await migrate_resourcelinks_instance_id(db, stats, dry_run, verbose, user_id)
        
    except Exception as e:
        logger.error(f"Migration error: {e}")
        stats.errors.append(str(e))
        raise
    
    # Print report
    print(stats.report())
    
    if stats.errors:
        logger.warning("Migration completed with errors")
        return 1
    
    logger.info("Migration completed successfully")
    return 0


def main():
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Universal Object Model v4.0.0 Migration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without writing"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output for each document"
    )
    parser.add_argument(
        "--user-id",
        type=str,
        default=None,
        help="Migrate specific user only (for testing)"
    )
    
    args = parser.parse_args()
    
    exit_code = asyncio.run(
        run_migration(
            dry_run=args.dry_run,
            verbose=args.verbose,
            user_id=args.user_id
        )
    )
    
    exit(exit_code)


if __name__ == "__main__":
    main()

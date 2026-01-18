"""
Mock Access Control List (ACL) Registry for Collider Integration.

This module simulates the authorization logic that will eventually reside in the 
Collider application. In the full architecture, Canvases are dependencies of 
Containers, and access to a Canvas is determined by the user's rights on the 
parent Container.
"""

def check_container_access(user_id: str, container_id: str) -> bool:
    """
    Check if a user has access to a specific container.
    
    In the production Collider architecture:
    1. Check if user_id is the owner of container_id.
    2. Check if user_id is in the ACL (editors/viewers) of container_id.
    
    For THIS dev/mock implementation:
    - Returns True for ANY valid container_id to facilitate testing "Shared via Link".
    - Returns False if container_id is None or empty.
    """
    if not container_id:
        return False
        
    # TODO: In real implementation, query the Container Registry / ACL table
    # For now, we assume if you have the link/ID and it's a container_canvas, you have access.
    return True

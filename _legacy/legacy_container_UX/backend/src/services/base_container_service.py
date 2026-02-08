"""Base container service with shared logic for all container operations.

Extracts common functionality from SessionService and ContainerService:
- Depth validation (tier-gated)
- ACL verification
- Containment rules
- Resource link management

All container services should extend this base class and use ContainerRegistry.
"""

from datetime import datetime, UTC
from enum import Enum
from typing import Literal

from src.core.exceptions import (
    CircularDependencyError,
    DepthLimitError,
    InvalidContainmentError,
    NotFoundError,
    PermissionDeniedError,
)
from src.core.logging import get_logger
from src.models.permissions import Tier
from src.services.container_registry import (
    ContainerRegistry,
    ContainerType,
    get_container_registry,
)

logger = get_logger(__name__)


# ============================================================================
# Tier-Gated Depth Limits
# ============================================================================

# Depth limits: FREE=L2 (depth 1), PRO/ENT=L4 (depth 3)
# At max depth, only SOURCE can be added (one level deeper)
TIER_MAX_DEPTH = {
    Tier.FREE: 1,
    Tier.PRO: 3,
    Tier.ENTERPRISE: 3,
}


# ============================================================================
# Containment Rules (What can contain what)
# ============================================================================

# L0: UserSession can only contain SESSION and USER
# Sessions can contain AGENT, TOOL, SOURCE, nested SESSION
# Agents can contain TOOL, SOURCE
# Tools can contain SOURCE
# Sources are terminal (cannot contain anything)
# Users are terminal (cannot contain anything)

ALLOWED_CHILDREN = {
    ContainerType.USERSESSION: {ContainerType.SESSION},  # USER via ResourceLink, not as container
    ContainerType.SESSION: {ContainerType.SESSION, ContainerType.AGENT, ContainerType.TOOL, ContainerType.SOURCE},
    ContainerType.AGENT: {ContainerType.TOOL, ContainerType.SOURCE},
    ContainerType.TOOL: {ContainerType.SOURCE},
    ContainerType.SOURCE: set(),  # Terminal
}


class BaseContainerService:
    """Base class for container services with shared validation logic.
    
    Provides:
    - Tier-gated depth validation
    - Containment rule enforcement
    - ACL verification helpers
    - ResourceLink management via ContainerRegistry
    
    Subclasses can override for type-specific behavior.
    """

    def __init__(self, registry: ContainerRegistry | None = None):
        """Initialize with optional registry (defaults to global).
        
        Args:
            registry: ContainerRegistry instance (None = use global)
        """
        self._registry = registry

    @property
    def registry(self) -> ContainerRegistry:
        """Get ContainerRegistry (lazy initialization)."""
        if self._registry is None:
            self._registry = get_container_registry()
        return self._registry

    # ========================================================================
    # Depth Validation
    # ========================================================================

    def get_max_depth(self, tier: Tier | str) -> int:
        """Get max container depth for user tier.
        
        Args:
            tier: User tier (FREE, PRO, ENTERPRISE)
            
        Returns:
            Max allowed depth for tier
        """
        if isinstance(tier, str):
            try:
                tier = Tier(tier.lower())
            except ValueError:
                return TIER_MAX_DEPTH[Tier.FREE]  # Default to FREE
        
        return TIER_MAX_DEPTH.get(tier, TIER_MAX_DEPTH[Tier.FREE])

    def validate_depth(
        self,
        parent_depth: int | None,
        child_type: ContainerType,
        user_tier: Tier | str
    ) -> int:
        """Validate and compute child depth.
        
        Rules:
        - If parent_depth is None (Orphan): new_depth = 1
        - Else: new_depth = parent_depth + 1
        - If new_depth <= max_depth: OK for all types
        - If new_depth == max_depth + 1: Only SOURCE allowed
        - If new_depth > max_depth + 1: Block everything
        
        Args:
            parent_depth: Parent container's depth (None = Orphan/Root)
            child_type: Type of child to add
            user_tier: User's subscription tier
            
        Returns:
            New depth for child
            
        Raises:
            DepthLimitError: Would exceed tier limit
        """
        max_depth = self.get_max_depth(user_tier)
        
        # Treat None (Orphan) as Depth 0 (Root Context), so child becomes Depth 1
        current_depth = parent_depth if parent_depth is not None else 0
        new_depth = current_depth + 1
        
        if new_depth > max_depth + 1:
            raise DepthLimitError(
                f"Depth {new_depth} exceeds absolute limit {max_depth + 1} for tier {user_tier}"
            )
        
        if new_depth == max_depth + 1 and child_type != ContainerType.SOURCE:
            raise DepthLimitError(
                f"Only SOURCE allowed at depth {new_depth} (Tier {user_tier} limit)"
            )
        
        return new_depth

    # ========================================================================
    # Containment Rules
    # ========================================================================

    def validate_containment(
        self,
        parent_type: ContainerType,
        child_type: ContainerType
    ) -> None:
        """Validate that parent can contain child type.
        
        Args:
            parent_type: Parent container type
            child_type: Child container type
            
        Raises:
            InvalidContainmentError: Container type not allowed in parent
        """
        allowed = ALLOWED_CHILDREN.get(parent_type, set())
        
        if child_type not in allowed:
            raise InvalidContainmentError(
                f"{parent_type.value} cannot contain {child_type.value}. "
                f"Allowed: {[t.value for t in allowed]}"
            )

    def is_terminal(self, container_type: ContainerType) -> bool:
        """Check if container type is terminal (cannot have children).
        
        Args:
            container_type: Container type to check
            
        Returns:
            True if terminal
        """
        return len(ALLOWED_CHILDREN.get(container_type, set())) == 0

    # ========================================================================
    # ACL Helpers
    # ========================================================================

    def user_can_access(self, user_id: str, acl: dict) -> bool:
        """Check if user has any access (viewer+).
        
        Args:
            user_id: User ID to check
            acl: ACL dict {owner, editors, viewers}
            
        Returns:
            True if user has viewer, editor, or owner access
        """
        if not acl:
            return False
        
        if acl.get("owner") == user_id:
            return True
        if user_id in acl.get("editors", []):
            return True
        if user_id in acl.get("viewers", []):
            return True
        
        return False

    def user_can_edit(self, user_id: str, acl: dict) -> bool:
        """Check if user has edit access (editor+).
        
        Args:
            user_id: User ID to check
            acl: ACL dict {owner, editors, viewers}
            
        Returns:
            True if user has editor or owner access
        """
        if not acl:
            return False
        
        if acl.get("owner") == user_id:
            return True
        if user_id in acl.get("editors", []):
            return True
        
        return False

    def user_is_owner(self, user_id: str, acl: dict) -> bool:
        """Check if user is owner.
        
        Args:
            user_id: User ID to check
            acl: ACL dict {owner, editors, viewers}
            
        Returns:
            True if user is owner
        """
        return acl.get("owner") == user_id

    def get_user_role(self, user_id: str, acl: dict) -> str | None:
        """Get user's role in ACL.
        
        Args:
            user_id: User ID to check
            acl: ACL dict
            
        Returns:
            "owner", "editor", "viewer", or None
        """
        if acl.get("owner") == user_id:
            return "owner"
        if user_id in acl.get("editors", []):
            return "editor"
        if user_id in acl.get("viewers", []):
            return "viewer"
        return None

    # ========================================================================
    # Cycle Detection
    # ========================================================================

    async def would_create_cycle(
        self,
        parent_id: str,
        child_id: str
    ) -> bool:
        """Check if linking child to parent would create a cycle.
        
        Walks up from parent to check if child is an ancestor.
        
        Args:
            parent_id: Proposed parent container ID
            child_id: Proposed child container ID
            
        Returns:
            True if would create cycle
        """
        # Walk up the tree from parent
        current_id = parent_id
        visited = set()
        
        while current_id:
            if current_id == child_id:
                return True
            
            if current_id in visited:
                # Already in a cycle (shouldn't happen)
                return True
            
            visited.add(current_id)
            
            # Get parent's parent
            container_type = self._infer_container_type(current_id)
            if not container_type:
                break
            
            container = await self.registry.get(container_type, current_id, user_id=None)
            if not container:
                break
            
            current_id = container.get("parent_id")
        
        return False

    def _infer_container_type(self, container_id: str) -> ContainerType | None:
        """Infer container type from ID prefix.
        
        Args:
            container_id: Container instance ID
            
        Returns:
            ContainerType or None if unknown
        """
        if container_id.startswith("usersession_"):
            return ContainerType.USERSESSION
        elif container_id.startswith("sess_"):
            return ContainerType.SESSION
        elif container_id.startswith("agent_"):
            return ContainerType.AGENT
        elif container_id.startswith("tool_"):
            return ContainerType.TOOL
        elif container_id.startswith("source_"):
            return ContainerType.SOURCE
        return None

    # ========================================================================
    # Container Creation Helper
    # ========================================================================

    async def create_container(
        self,
        container_type: ContainerType,
        parent_id: str | None,
        user_id: str,
        user_tier: Tier | str,
        data: dict
    ) -> dict:
        """Create a new container with full validation.
        
        Args:
            container_type: Type of container to create
            parent_id: Parent container ID (None for Orphan)
            user_id: User creating the container
            user_tier: User's subscription tier
            data: Container data (instance_id must be provided)
            
        Returns:
            Created container data
            
        Raises:
            NotFoundError: Parent doesn't exist
            PermissionDeniedError: User can't edit parent
            DepthLimitError: Would exceed tier depth limit
            InvalidContainmentError: Container type not allowed in parent
            CircularDependencyError: Would create cycle
        """
        parent_depth = None
        
        if parent_id:
            # 1. Get parent
            parent_type = self._infer_container_type(parent_id)
            if not parent_type:
                raise NotFoundError(f"Cannot determine type of parent {parent_id}")
            
            parent = await self.registry.get(parent_type, parent_id, user_id=None)
            if not parent:
                raise NotFoundError(f"Parent {parent_id} not found")
            
            # 2. ACL check (user must be able to edit parent)
            if not self.user_can_edit(user_id, parent.get("acl", {})):
                raise PermissionDeniedError(f"User {user_id} cannot edit parent {parent_id}")
            
            # 3. Containment rules
            self.validate_containment(parent_type, container_type)
            
            parent_depth = parent.get("depth", 0)
        
        # 4. Depth validation (handles parent_depth=None for Orphans)
        new_depth = self.validate_depth(parent_depth, container_type, user_tier)
        
        # 5. Cycle detection (for nested sessions)
        instance_id = data.get("instance_id")
        if parent_id and instance_id and await self.would_create_cycle(parent_id, instance_id):
            raise CircularDependencyError(f"Adding {instance_id} to {parent_id} would create cycle")
        
        # 6. Set hierarchy fields
        data["parent_id"] = parent_id
        data["depth"] = new_depth
        data["acl"] = {"owner": user_id, "editors": [], "viewers": []}
        
        # 7. Register via ContainerRegistry
        result = await self.registry.register(container_type, data, user_id)
        
        logger.info(
            "Created container",
            extra={
                "container_type": container_type.value,
                "instance_id": instance_id,
                "parent_id": parent_id,
                "depth": new_depth,
                "user_id": user_id
            }
        )
        
        return result

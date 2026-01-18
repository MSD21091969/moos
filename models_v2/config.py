"""Configuration constants for Collider mathematical models v2.

GPU Settings, Recursion Limits, and Validation Rules.
"""
import os
from typing import Literal

# ============================================================================
# RECURSION DEPTH LIMITS
# ============================================================================

MAX_RECURSION_DEPTH: int = int(os.getenv("COLLIDER_MAX_DEPTH", "10"))
RECURSION_DEPTH_WARNING: int = 5

# ============================================================================
# GPU SETTINGS
# ============================================================================

GPU_MODE: Literal["auto", "gpu", "cpu"] = os.getenv("COLLIDER_GPU_MODE", "auto")  # type: ignore
CPU_PERFORMANCE_WARNING_NODES: int = 500

# ============================================================================
# MATHEMATICAL VALIDATION
# ============================================================================

VALIDATE_CATEGORY_LAWS: bool = os.getenv("COLLIDER_VALIDATE_LAWS", "true").lower() == "true"
VALIDATE_BOUNDARY_TRI_METHOD: bool = os.getenv("COLLIDER_VALIDATE_BOUNDARY", "true").lower() == "true"

# ============================================================================
# EMBEDDING SETTINGS
# ============================================================================

DEFAULT_EMBEDDING_DIM: int = 256
DEPTH_DECAY_FACTOR: float = 0.9
SEMANTIC_EMBEDDING_MODEL: str = os.getenv("COLLIDER_EMBEDDING_MODEL", "nomic-embed-text")

# Aliases
EMBEDDING_DIMENSION = DEFAULT_EMBEDDING_DIM
EMBEDDING_DECAY_FACTOR = DEPTH_DECAY_FACTOR

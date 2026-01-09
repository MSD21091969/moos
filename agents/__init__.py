"""Factory Agents - Configured agents for different environments.

Agents are built from Parts:
- Local: Gödel (meta), Pilot (dev assistant)
- Frontend: ChatAgent (user-facing)
- Backend: MaintenanceAgent (automation)
"""

from .local import PilotAgent
from .frontend import ChatAgent
from .backend import MaintenanceAgent

# Note: Gödel is in definitions/ as the meta-agent

__all__ = [
    # Local
    "PilotAgent",
    # Frontend
    "ChatAgent",
    # Backend
    "MaintenanceAgent",
]

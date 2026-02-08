# Agents package
# Import available agents - some may have heavy dependencies
try:
    from .tracer import TracerAgent
except ImportError:
    TracerAgent = None  # type: ignore

try:
    from .workspace_agent import WorkspaceAgent, WorkspaceContext
except ImportError:
    WorkspaceAgent = None  # type: ignore
    WorkspaceContext = None  # type: ignore

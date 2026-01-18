# Legacy Agent Cleanup - Walkthrough

## Objective

Remove deprecated BaseAgent pattern and Factory internal agents, keeping only the modern DeepAgent template pattern.

---

## What Was Removed

### 1. Legacy Base Class

```
❌ D:\agent-factory\parts\base_agent.py
```

- OLD agent pattern (ABC base class)
- Custom tool registry, IOSchema, AgentConfig
- No UserObject integration
- No Factory models awareness

### 2. Factory Internal Agents

```
❌ D:\agent-factory\agents\local\pilot.py (PilotAgent)
   - Development assistant with file/git tools
   - Using BaseAgent pattern

❌ D:\agent-factory\agents\frontend\chat_agent.py (ChatAgent)
   - User-facing chat with mock tools
   - TODO stubs, not connected to backend

❌ D:\agent-factory\agents\backend\maintenance.py (MaintenanceAgent)
   - Backend automation with mock tools
   - TODO stubs, not connected to backend
```

---

## What Remains (CLEAN Architecture)

### ✅ Templates (NEW Pattern)

```
D:\agent-factory\templates\
├── factory_agent.py       # Base template with UserObject
├── deep_agent.py          # Pydantic-deep wrapper
└── agent_runner.py        # CLI runner with interface selection
```

### ✅ Workspace Agents (Production)

```
D:\IADORE\agents\agatha.py
- DeepAgent pattern ✅
- FilesystemToolset
- OllamaModel("agatha:latest")
- Workspace rules auto-load

D:\dev-assistant\agents\collider_pilot.py
- DeepAgent pattern ✅
- ContainerToolset + LinkToolset
- ColliderBackend (SQLite connection)
- Skills: graph_audit, container_inspector
- OllamaModel("deepseek-r1:14b")
```

### ✅ Supporting Infrastructure

```
parts/toolsets/            # 5 toolsets (Container, Link, Definition, Filesystem, SubAgent)
runtimes/backends/         # 2 backends (StateBackend, ColliderBackend)
knowledge/                 # Skills system + research archives
interfaces/                # 3 interfaces (CLI, API, Gradio)
```

---

## Verification

### Cleanup Status

```powershell
# Agents directory now minimal
D:\agent-factory\agents\
├── __init__.py           # Updated with deprecation notice
└── __pycache__/          # Python cache
```

### Workspace Agents Still Functional

Both workspace agents remain fully operational:

- ✅ Agatha imports DeepAgent from templates/
- ✅ Collider Pilot imports DeepAgent from templates/
- ✅ Both use toolsets from parts/toolsets/
- ✅ Both load workspace-guide.md for context

### Git Status

```
All deleted files tracked for commit
No impact on workspace agents (external directories)
```

---

## Benefits

### 1. Single Agent Pattern ✅

```
BEFORE: Two patterns (BaseAgent vs DeepAgent)
AFTER: One pattern (DeepAgent only)
```

### 2. No Mock Code ✅

```
BEFORE: Chat/Maintenance agents with TODO stubs
AFTER: Only production-ready agents
```

### 3. Clear Documentation ✅

```
agents/__init__.py now documents:
- What was removed
- Why it was removed
- Where to find current pattern
```

### 4. Reduced Maintenance ✅

```
BEFORE: Maintain two agent architectures
AFTER: Single source of truth (templates/)
```

---

## Migration Path (For Future Agents)

### Creating New Agents

```python
# Use templates/DeepAgent pattern
from agent_factory.models import UserObject
from agent_factory.templates import DeepAgent
from agent_factory.parts.toolsets import ContainerToolset
from agent_factory.interfaces import DeepAgentCLI

user = UserObject(auth_provider_id="local", email="user@localhost")
agent = DeepAgent(
    user=user,
    model="ollama:llama3.1:8b",
    toolsets=[ContainerToolset()],
    skills=[],
)

cli = DeepAgentCLI(agent, name="MyAgent")
```

### Adding Functionality

```python
# Use existing toolsets
from agent_factory.parts.toolsets import (
    ContainerToolset,      # Container CRUD
    LinkToolset,           # Graph traversal
    DefinitionToolset,     # Definition registry
    FilesystemToolset,     # File operations
    SubAgentToolset,       # Delegation
)

# Or create custom toolset
class CustomToolset:
    def my_tool(self, arg: str) -> str:
        return f"Result: {arg}"
```

---

## Summary

**Removed**:

- ❌ parts/base_agent.py (OLD pattern)
- ❌ agents/local/pilot.py (BaseAgent)
- ❌ agents/frontend/chat_agent.py (BaseAgent + mocks)
- ❌ agents/backend/maintenance.py (BaseAgent + mocks)

**Kept**:

- ✅ templates/ (DeepAgent pattern)
- ✅ Workspace agents (Agatha, Collider Pilot)
- ✅ All infrastructure (toolsets, backends, skills, interfaces)

**Result**: Clean, single-pattern architecture focused on production-ready DeepAgent template! 🎉

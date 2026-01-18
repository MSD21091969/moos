# Agent Factory - Complete Component Inventory

## 🚨 CRITICAL FINDING: Two Agent Architectures Running in Parallel

You have **TWO SEPARATE** agent patterns in your workspace:

```
├── OLD PATTERN (parts/)
│   └── BaseAgent + ModelAdapter + ToolRegistry
│       └── Used by: Pilot, ChatAgent, MaintenanceAgent (Factory internal)
│
└── NEW PATTERN (templates/)
    └── FactoryAgent + DeepAgent + agent_runner
        └── Used by: Agatha (IADORE), Collider Pilot (dev-assistant) ✅
```

**Status**: Workspace agents (Agatha, Collider Pilot) use **NEW pattern** ✅  
**Issue**: Factory internal agents (Pilot, ChatAgent, Maintenance) still use **OLD pattern** ⚠️

---

## Agent Component Map

### 1. Templates (NEW Pattern) ✅ CURRENT

#### `templates/factory_agent.py`

```python
class FactoryAgent:
    """Base template for Factory-compliant agents"""
    # Uses: PydanticAI Agent wrapper
    # Features:
    - UserObject integration (R=0 identity)
    - .with_container() scoping
    - .with_definition() blueprint
    - PydanticAI standard interface
```

#### `templates/deep_agent.py`

```python
class DeepAgent(FactoryAgent):
    """pydantic-deep wrapper for advanced capabilities"""
    # Features:
    - Toolsets registration (ContainerToolset, LinkToolset, etc.)
    - Skills loading (markdown prompts)
    - File uploads
    - Streaming responses
    - Backend integration (StateBackend, ColliderBackend)
```

#### `templates/agent_runner.py`

```python
def run():
    """Unified CLI runner"""
    # Features:
    - Interface selection (CLI/API/Gradio)
    - Workspace rules auto-loading
    - Click CLI integration
```

**Used By**:

- ✅ `D:\IADORE\agents\agatha.py` (DeepAgent)
- ✅ `D:\dev-assistant\agents\collider_pilot.py` (DeepAgent)

---

### 2. Parts (OLD Pattern) ⚠️ LEGACY

#### `parts/base_agent.py`

```python
class BaseAgent(ABC):
    """Abstract base for OLD agent pattern"""
    # Features:
    - IOSchema (content + metadata)
    - AgentConfig
    - Tool registry (simple dict)
    - No UserObject integration
    - No Factory models awareness
```

**Used By** (Factory Internal):

- ⚠️ `agents/local/pilot.py` (PilotAgent)
- ⚠️ `agents/frontend/chat_agent.py` (ChatAgent)
- ⚠️ `agents/backend/maintenance.py` (MaintenanceAgent)

---

## Workspace Agents Analysis

### ✅ Agatha (IADORE)

```python
# File: D:\IADORE\agents\agatha.py
# Pattern: DeepAgent ✅

Components:
- UserObject identity
- OllamaModel("agatha:latest")
- FilesystemToolset
- Workspace rules auto-load
- DeepAgentCLI interface

Connectivity: FULL
- ✅ UserObject (R=0 root)
- ✅ Factory models (Container, Link, Definition)
- ✅ Toolsets
- ✅ Workspace guides
- ✅ Interfaces (CLI/API/Gradio)

Status: Production-ready ✅
```

### ✅ Collider Pilot (dev-assistant)

```python
# File: D:\dev-assistant\agents\collider_pilot.py
# Pattern: DeepAgent ✅

Components:
- UserObject identity
- OllamaModel("deepseek-r1:14b")
- ContainerToolset + LinkToolset
- ColliderBackend (SQLite connection)
- Skills: graph_audit, container_inspector
- Workspace rules auto-load
- DeepAgentCLI interface

Connectivity: FULL
- ✅ UserObject (R=0 root)
- ✅ Factory models
- ✅ Toolsets (Container, Link)
- ✅ Backend (Collider DB)
- ✅ Skills system
- ✅ Workspace guides
- ✅ Interfaces (CLI/API/Gradio)

Status: Production-ready ✅
```

---

## Factory Internal Agents (OLD Pattern)

### ⚠️ PilotAgent (agents/local/pilot.py)

```python
# Pattern: BaseAgent (OLD)

Tools:
- read_file, write_file, list_dir
- run_command
- git_status, git_diff

Issues:
- ❌ No UserObject integration
- ❌ No Factory models (Container, Link, Definition)
- ❌ Manual tool registry (not Toolsets)
- ❌ Custom ModelAdapter (not PydanticAI)

Purpose: Development assistant for local Factory environment
Status: DEPRECATED - migrate to DeepAgent pattern
```

### ⚠️ ChatAgent (agents/frontend/chat_agent.py)

```python
# Pattern: BaseAgent (OLD)

Tools:
- get_container_info (TODO: connect to backend)
- list_containers (TODO: connect)
- explain_definition (TODO: connect)

Issues:
- ❌ No UserObject
- ❌ Mock tools (not connected to real backend)
- ❌ Not using Factory toolsets

Purpose: User-facing chat for Collider frontend
Status: DEPRECATED - migrate to DeepAgent OR remove
```

### ⚠️ MaintenanceAgent (agents/backend/maintenance.py)

```python
# Pattern: BaseAgent (OLD)

Tools:
- check_orphans, validate_links
- check_definitions
- get_health_metrics, cleanup

Issues:
- ❌ No UserObject
- ❌ Mock tools (TODO: connect to backend)
- ❌ Not using Factory toolsets

Purpose: Backend maintenance automation
Status: DEPRECATED - migrate to DeepAgent OR remove
```

---

## Interfaces (Fully Connected) ✅

### `interfaces/cli_interface.py`

```python
class DeepAgentCLI:
    # Features:
    - Rich terminal UI
    - Streaming support
    - History management
    - Markdown rendering

Used by: Agatha ✅, Collider Pilot ✅
```

### `interfaces/api_interface.py`

```python
class DeepAgentAPI:
    # Features:
    - FastAPI server
    - SSE streaming
    - OpenAPI docs
    - CORS support

Status: Ready, not actively used
```

### `interfaces/gradio_interface.py`

```python
class DeepAgentGradio:
    # Features:
    - Web UI
    - File uploads
    - Streaming chat
    - Share links

Status: Ready, not actively used
```

---

## Toolsets (Fully Integrated) ✅

All toolsets in `parts/toolsets/`:

| Toolset             | Purpose                           | Used By           |
| ------------------- | --------------------------------- | ----------------- |
| `ContainerToolset`  | Container CRUD                    | Collider Pilot ✅ |
| `LinkToolset`       | Link management + graph traversal | Collider Pilot ✅ |
| `DefinitionToolset` | Definition registry               | Available ✅      |
| `FilesystemToolset` | Secure file operations            | Agatha ✅         |
| `SubAgentToolset`   | Delegation                        | Available ✅      |

**Status**: Production-ready, workspace agents using them correctly ✅

---

## Backends (Fully Integrated) ✅

### `runtimes/backends/state_backend.py`

```python
class StateBackend:
    # In-memory state for testing
```

### `runtimes/backends/collider_backend.py`

```python
class ColliderBackend:
    # SQLite integration
    # Used by: Collider Pilot ✅
```

**Status**: Production-ready, Collider Pilot connects to DB ✅

---

## Skills System (Fully Integrated) ✅

### `knowledge/__init__.py`

```python
def load_skills(skill_name: str) -> dict:
    # Loads markdown skills with frontmatter
```

### `knowledge/skills/graph_audit.md`

### `knowledge/skills/container_inspector.md`

**Used By**: Collider Pilot ✅

---

## Connectivity Matrix

| Component           | Agatha (IADORE)           | Collider Pilot (dev-assistant)       | Factory Agents (Pilot/Chat/Maintenance) |
| ------------------- | ------------------------- | ------------------------------------ | --------------------------------------- |
| **UserObject**      | ✅ Connected              | ✅ Connected                         | ❌ Not using                            |
| **Factory Models**  | ✅ Aware                  | ✅ Aware                             | ❌ Not aware                            |
| **Toolsets**        | ✅ FilesystemToolset      | ✅ Container + Link                  | ❌ Custom tools                         |
| **Backends**        | ⚠️ None (no DB needed)    | ✅ ColliderBackend                   | ❌ Mocks                                |
| **Skills**          | ⚠️ None (simple use case) | ✅ graph_audit + container_inspector | ❌ Not using                            |
| **Interfaces**      | ✅ CLI                    | ✅ CLI                               | ❌ Direct instantiation                 |
| **Workspace Rules** | ✅ Auto-load              | ✅ Auto-load                         | ❌ No awareness                         |
| **PydanticAI**      | ✅ Via DeepAgent          | ✅ Via DeepAgent                     | ❌ Custom adapter                       |

---

## Redundancies & Cleanup Opportunities

### 1. Two Agent Patterns ⚠️ MAJOR

**Redundancy**: `BaseAgent` (parts/) vs `FactoryAgent/DeepAgent` (templates/)

**Recommendation**:

```
✅ KEEP: templates/FactoryAgent + DeepAgent (NEW pattern)
❌ DEPRECATE: parts/BaseAgent (OLD pattern)

Actions:
1. Migrate Factory agents to DeepAgent:
   - agents/local/pilot.py → templates/DeepAgent
   - agents/frontend/chat_agent.py → templates/DeepAgent OR remove
   - agents/backend/maintenance.py → templates/DeepAgent OR remove

2. Delete parts/base_agent.py after migration
```

### 2. Mock Agents (Not Connected)

**Agents with TODO stubs**:

- `agents/frontend/chat_agent.py` - All tools are mocks
- `agents/backend/maintenance.py` - All tools are mocks
- `agents/local/pilot.py` - Functional but isolated

**Recommendation**:

```
Option A: Migrate to DeepAgent + connect to real backends
Option B: Remove if not actively used

Current: Workspace agents (Agatha, Collider Pilot) are fully functional ✅
Factory internal agents can be removed if not needed
```

### 3. Unused Interfaces

**Current Usage**:

- CLI: ✅ Agatha + Collider Pilot
- API: ❌ Not used
- Gradio: ❌ Not used

**Recommendation**:

```
✅ KEEP: All interfaces (ready for deployment)
They work, just not actively used in local dev workflow
Can be activated via agent_runner.py --interface api/gradio
```

### 4. Custom Tool Implementations

**Redundancy**: Factory agents implement custom tools instead of using Toolsets

**Example**:

```python
# Pilot agent (OLD)
def read_file(self, path: str) -> str:
    # Custom implementation

# Should use:
from agent_factory.parts.toolsets import FilesystemToolset
```

**Recommendation**:

```
✅ Workspace agents use Toolsets correctly
❌ Factory agents should be migrated to use Toolsets
```

---

## Action Plan for Cleanup

### Phase 1: Assess Factory Internal Agents

```
1. Determine if Pilot/Chat/Maintenance are actively used
2. If YES → migrate to DeepAgent pattern
3. If NO → delete agents/local, agents/frontend, agents/backend
```

### Phase 2: Consolidate Agent Pattern

```
1. Remove parts/base_agent.py (if Factory agents deleted)
2. Keep only templates/ pattern
3. All future agents use DeepAgent
```

### Phase 3: Documentation

```
1. Update workspace-guide.md with single agent pattern
2. Add examples of creating new DeepAgent instances
3. Document toolset usage
```

---

## ✅ What's Working Perfectly

**Workspace Agents**:

- Agatha (IADORE) - File management ✅
- Collider Pilot (dev-assistant) - Graph debugging ✅

**Infrastructure**:

- DeepAgent template ✅
- All 5 toolsets ✅
- 2 backends (State + Collider) ✅
- Skills system ✅
- 3 interfaces (CLI/API/Gradio) ✅
- Workspace rules auto-loading ✅

**Connectivity**: FULL

- UserObject integration ✅
- Factory models access ✅
- Backend integration (Collider DB) ✅
- Workspace context awareness ✅

---

## Summary

**Current State**: ✅ **Workspace agents fully connected and production-ready**

**Key Findings**:

1. **Agatha** and **Collider Pilot** use correct DeepAgent pattern ✅
2. Factory internal agents use deprecated BaseAgent pattern ⚠️
3. All infrastructure (toolsets, backends, skills, interfaces) working ✅

**Cleanup Needed**:

- Decide fate of Factory internal agents (Pilot, Chat, Maintenance)
- Optionally remove OLD `parts/BaseAgent` pattern
- Document single agent pattern going forward

**No Critical Issues**: Your workspace agents (the ones you actually use) are perfectly connected! 🎉

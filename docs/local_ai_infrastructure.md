# Local AI Agent Infrastructure: Workspaces 1 & 3

**Complete Environment Setup for Running Pydantic-Deep Agents**

---

## 1. Enhanced Workspace Structure

### IADORE (Workspace 1) - Personal AI Environment

```
D:\IADORE\
├── .venv\                           # Python 3.12+ environment
├── .agent\
│   ├── workflows\                   # Synced from Factory
│   └── rules\
│       ├── personal-rules.md       # Workspace-specific overrides
│       └── agent-personality.md    # Personal agent behavior
├── knowledge\
│   ├── personal\                    # Personal knowledge base
│   └── synced\                      # Synced from Factory (read-only)
├── agents\                          # Local agent definitions
│   ├── agatha.py                    # Personal file manager agent
│   ├── researcher.py                # Research assistant
│   └── __init__.py
├── skills\                          # Agent skill definitions
│   ├── file_organizer.md
│   ├── email_parser.md
│   └── summarizer.md
├── toolsets\                        # Custom toolset implementations
│   ├── personal_filesystem.py
│   └── email_client.py
├── backends\                        # State/execution backends
│   └── local_state.py               # Inherits from Factory StateBackend
├── uploads\                         # Agent file upload directory
└── pyproject.toml
```

### Dev-Assistant (Workspace 3) - Assembly/Testing Environment

```
D:\dev-assistant\
├── .venv\                           # Python 3.12+ environment
├── .agent\
│   ├── workflows\                   # Synced from Factory
│   └── rules\
│       ├── dev-rules.md             # Testing & debugging rules
│       └── pilot-rules.md           # Collider pilot behavior
├── knowledge\
│   ├── collider\                    # Collider-specific knowledge
│   │   ├── architecture.md
│   │   └── api-specs.md
│   └── synced\                      # Synced from Factory
├── agents\                          # Development agents
│   ├── collider_pilot.py            # Graph debugging agent
│   ├── test_runner.py               # Automated testing agent
│   └── code_reviewer.py             # Code analysis agent
├── skills\                          # Dev-specific skills
│   ├── graph_audit.md
│   ├── container_inspector.md
│   └── link_tracer.md
├── toolsets\                        # Assembly/testing toolsets
│   ├── collider_graph.py            # Graph inspection tools
│   ├── container_builder.py         # Container creation tools
│   └── runtime_debugger.py          # Runtime execution tools
├── backends\
│   └── collider_state.py            # Shared DB access (collider.db)
├── uploads\
├── tests\                           # Agent behavior tests
└── pyproject.toml
```

---

## 2. Factory Requirements for Pydantic-Deep Agents

### What Factory Must Produce

**A. Base Agent Templates** (`agent-factory/templates/agents/`)

```python
# Standard agent structure with Factory models
from agent_factory.models import UserObject, Container, Definition
from pydantic_ai import Agent
from pydantic_ai.models import Model

class FactoryAgent:
    """Base template for all workspace agents."""
    def __init__(self, model: Model, user: UserObject):
        self.user = user
        self.agent = Agent(model)

    async def run(self, prompt: str):
        # Uses Factory Definition for behavior
        pass
```

**B. Toolsets** (`agent-factory/parts/toolsets/`)

```python
# Factory-standard toolsets
- container_toolset.py     # Create/inspect Containers
- link_toolset.py          # Create/traverse Links
- definition_toolset.py    # Registry operations
- filesystem_toolset.py    # File operations
- subagent_toolset.py      # Delegate to nested agents
```

**C. Backends** (`agent-factory/runtimes/backends/`)

```python
# State management backends
- state_backend.py         # In-memory (StateBackend)
- sqlite_backend.py        # SQLite persistence
- redis_backend.py         # Redis cache
- collider_backend.py      # Collider DB integration
```

**D. Skills System** (`agent-factory/knowledge/skills/`)

```markdown
# Markdown-based skill definitions

- container_operations.md
- graph_traversal.md
- definition_compilation.md
```

**E. Vector Store Integration** (`agent-factory/runtimes/vector_store.py`)

```python
# Already exists - needs standardization
- FAISS index for knowledge retrieval
- Sentence-transformers embeddings
- Integration with agent context
```

---

## 3. Dependency Specifications

### IADORE `pyproject.toml`

```toml
[project]
name = "iadore-workspace"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "agent-factory @ file:///D:/agent-factory",

    # Pydantic-Deep ecosystem
    "pydantic-deep>=0.3.0",
    "pydantic-ai>=0.0.14",
    "pydantic-ai-backend>=0.1.0",
    "pydantic-ai-todo>=0.1.0",

    # Local AI Stack
    "ollama>=0.3.0",
    "sentence-transformers>=3.0.0",

    # Personal toolsets
    "watchdog>=4.0.0",          # File monitoring
    "python-magic>=0.4.27",     # File type detection
]
```

### Dev-Assistant `pyproject.toml`

```toml
[project]
name = "dev-assistant"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "agent-factory @ file:///D:/agent-factory",

    # Pydantic-Deep ecosystem
    "pydantic-deep>=0.3.0",
    "pydantic-ai>=0.0.14",
    "pydantic-ai-backend>=0.1.0",

    # Collider integration
    "networkx>=3.4.0",
    "sqlalchemy>=2.0.45",
    "aiosqlite>=0.22.1",

    # Testing toolsets
    "pytest>=8.3.0",
    "pytest-asyncio>=0.23.0",
]
```

### Factory `pyproject.toml` (UPDATED)

```toml
[project]
name = "agent-factory"
version = "0.2.0"
requires-python = ">=3.12"  # Lowered from 3.14 for compatibility
dependencies = [
    # Core
    "pydantic>=2.12.5",
    "pydantic-ai>=0.0.14",
    "ollama>=0.6.1",

    # Agent framework (to produce templates)
    "pydantic-deep>=0.3.0",
    "pydantic-ai-backend>=0.1.0",

    # Vector store
    "faiss-cpu>=1.13.2",
    "sentence-transformers>=3.0.0",

    # Toolset dependencies
    "networkx>=3.4.0",      # Graph operations
    "sqlalchemy>=2.0.45",   # DB backends
]
```

---

## 4. What Workspaces 1 & 3 Need from Factory

### A. Models (Already Available)

✅ `from agent_factory.models import UserObject, Container, Link, Definition`

### B. Base Agent Templates (**NEW**)

```python
from agent_factory.templates import FactoryAgent, DeepAgent
```

### C. Toolsets (**NEW**)

```python
from agent_factory.parts.toolsets import (
    ContainerToolset,
    LinkToolset,
    DefinitionToolset,
    FilesystemToolset,
    SubAgentToolset,
)
```

### D. Backends (**Extend Existing**)

```python
from agent_factory.runtimes.backends import (
    StateBackend,
    SQLiteBackend,
    ColliderBackend,
)
```

### E. Skills Loader (**NEW**)

```python
from agent_factory.knowledge import load_skills

skills = load_skills("graph_traversal")
agent = DeepAgent(skills=[skills])
```

---

## 5. Agent Initialization Pattern

### IADORE Agent (Personal File Manager)

```python
# iadore/agents/agatha.py
from agent_factory.models import UserObject
from agent_factory.templates import DeepAgent
from agent_factory.parts.toolsets import FilesystemToolset
from agent_factory.knowledge import load_skills
from pydantic_ai.models.ollama import OllamaModel

# User identity
user = UserObject(
    auth_provider_id="local",
    email="maassen@localhost",
    tier="pro"
)

# Skills from Factory
skills = [
    load_skills("file_organizer"),
    load_skills("summarizer"),
]

# Toolsets
toolsets = [
    FilesystemToolset(base_path="D:/IADORE"),
]

# Local LLM
model = OllamaModel("llama3.1:8b")

# Create agent
agatha = DeepAgent(
    user=user,
    model=model,
    toolsets=toolsets,
    skills=skills,
    system_prompt="You are Agatha, a personal file management assistant."
)

# Run
result = await agatha.run("Organize my downloads folder by file type")
```

### Dev-Assistant Agent (Collider Pilot)

```python
# dev-assistant/agents/collider_pilot.py
from agent_factory.models import UserObject
from agent_factory.templates import DeepAgent
from agent_factory.parts.toolsets import ContainerToolset, LinkToolset
from agent_factory.runtimes.backends import ColliderBackend
from agent_factory.knowledge import load_skills

user = UserObject(
    auth_provider_id="local",
    email="dev@localhost",
    tier="enterprise"
)

skills = [
    load_skills("graph_audit"),
    load_skills("container_inspector"),
]

# Connect to Collider DB
backend = ColliderBackend(db_path="D:/my-tiny-data-collider/collider.db")

toolsets = [
    ContainerToolset(backend=backend),
    LinkToolset(backend=backend),
]

model = OllamaModel("deepseek-coder-v2:16b")

pilot = DeepAgent(
    user=user,
    model=model,
    toolsets=toolsets,
    skills=skills,
    backend=backend,
    system_prompt="You are a Collider graph debugging pilot."
)

# Run graph audit
result = await pilot.run("Audit all containers for orphaned links")
```

---

## 6. Factory Production Roadmap

To support this, Factory needs to produce:

### Phase 1: Templates (**Immediate**)

- [ ] `templates/agents/factory_agent.py` - Base agent class
- [ ] `templates/agents/deep_agent.py` - Pydantic-deep wrapper
- [ ] `templates/agents/__init__.py` - Export all templates

### Phase 2: Toolsets (**Week 1**)

- [ ] `parts/toolsets/container_toolset.py`
- [ ] `parts/toolsets/link_toolset.py`
- [ ] `parts/toolsets/definition_toolset.py`
- [ ] `parts/toolsets/filesystem_toolset.py`
- [ ] `parts/toolsets/subagent_toolset.py`

### Phase 3: Backends (**Week 1**)

- [ ] Extend `runtimes/backends/state.py` for pydantic-ai-backend
- [ ] Add `runtimes/backends/collider.py` for shared DB access

### Phase 4: Skills System (**Week 2**)

- [ ] `knowledge/skills/` directory structure
- [ ] Markdown skill loader in `knowledge/__init__.py`
- [ ] Example skills: `graph_audit.md`, `container_inspector.md`

### Phase 5: Documentation (**Week 2**)

- [ ] Agent creation guide
- [ ] Toolset API reference
- [ ] Skills authoring guide

---

## 7. Complete Example: Full Stack

```python
# Factory produces the parts
from agent_factory.models import UserObject, Container, Definition
from agent_factory.templates import DeepAgent
from agent_factory.parts.toolsets import ContainerToolset
from agent_factory.runtimes.backends import ColliderBackend
from agent_factory.knowledge import load_skills

# Workspace imports Factory parts
user = UserObject(auth_provider_id="local", email="user@localhost")
backend = ColliderBackend()
toolsets = [ContainerToolset(backend)]
skills = [load_skills("graph_audit")]

agent = DeepAgent(
    user=user,
    model="ollama:llama3.1",
    toolsets=toolsets,
    skills=skills,
    backend=backend
)

# Agent uses Factory models internally
result = await agent.run("Create a new container called 'Trip to Paris'")
# Agent calls ContainerToolset.create_container()
# Which uses Factory's Container model
# Persists to Collider DB via ColliderBackend
```

---

## Summary

**Workspaces 1 & 3 Need**:

1. ✅ Models (already exist)
2. 🔨 Agent templates (to be built)
3. 🔨 Toolsets (to be built)
4. 🔨 Skills system (to be built)
5. ✅ Backends (extend existing)

**Factory Must Facilitate**:

- Standardized agent initialization
- Toolset registry for Container/Link/Definition operations
- Skills as markdown prompts
- Backend abstraction for state management
- Vector store integration for knowledge retrieval

**Result**: IADORE and dev-assistant become **fully capable AI environments** that can run pydantic-deep agents using Factory-produced parts.

# Development Environment Setup: Industry Best Practices

**Three-Workspace Factory-First Architecture**

---

## 1. Directory Structure

```
D:\
├── IADORE\                          # Workspace 1: Personal Development
│   ├── .venv\                       # Isolated Python environment
│   ├── .agent\
│   │   ├── workflows\               # Synced from Factory
│   │   └── rules\                   # Workspace-specific overrides
│   ├── knowledge\                   # Synced from Factory + personal
│   ├── agents\                      # Personal agent definitions
│   └── pyproject.toml               # Depends on: agent-factory (editable)
│
├── agent-factory\                   # Workspace 2: UPSTREAM PRODUCER
│   ├── .venv\                       # Isolated Python environment
│   ├── models\                      # v3 Source of Truth
│   │   ├── user_object.py
│   │   ├── user_workspace_container.py
│   │   ├── container.py
│   │   ├── link.py
│   │   └── definition.py
│   ├── parts\                       # Reusable components
│   ├── runtimes\                    # Execution engines
│   ├── tools\                       # Godel toolkit
│   ├── knowledge\                   # MASTER knowledge base
│   │   └── .sync_manifest.json     # Tracks what to sync
│   ├── .agent\workflows\            # MASTER workflows
│   ├── pyproject.toml               # No Factory dependency (it IS Factory)
│   └── sync_to_workspaces.py       # Sync script
│
├── dev-assistant\                   # Workspace 3: Assembly + Testing
│   ├── .venv\                       # Isolated Python environment
│   ├── .agent\workflows\            # Synced from Factory
│   ├── knowledge\                   # Synced from Factory
│   ├── src\                         # Local pilot tools
│   └── pyproject.toml               # Depends on: agent-factory (editable)
│
└── my-tiny-data-collider\           # Application: Collider
    ├── .venv\                       # Isolated Python environment
    ├── backend\
    ├── runtime\
    ├── shared\domain\               # TO BE REPLACED with Factory models
    ├── frontend\
    └── pyproject.toml               # Depends on: agent-factory (editable)
```

---

## 2. Python Environment Configuration

### Factory `pyproject.toml`

```toml
[project]
name = "agent-factory"
version = "0.2.0"
requires-python = ">=3.14"
dependencies = [
    "pydantic>=2.12.5",
    "pydantic-ai>=1.40.0",
    "ollama>=0.6.1",
    "faiss-cpu>=1.13.2",
]

[project.optional-dependencies]
dev = ["pytest", "ruff", "mypy"]
```

### IADORE `pyproject.toml`

```toml
[project]
name = "iadore-workspace"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "agent-factory @ file:///D:/agent-factory",  # Editable local install
]
```

### Collider `pyproject.toml` (UPDATED)

```toml
[project]
name = "tiny-data-collider"
version = "3.4.0"  # Bump after v3 migration
dependencies = [
    "agent-factory @ file:///D:/agent-factory",  # NEW: Import Factory models
    "fastapi>=0.115.0",
    "networkx>=3.4.0",
    # ... rest of dependencies
]
```

### Installation Commands

```powershell
# 1. Factory (no dependencies on other workspaces)
cd D:\agent-factory
uv sync --dev

# 2. IADORE
cd D:\IADORE
uv sync  # Auto-installs Factory as editable

# 3. Collider
cd D:\my-tiny-data-collider
uv sync  # Auto-installs Factory as editable

# 4. Dev-Assistant
cd D:\dev-assistant
uv sync  # Auto-installs Factory as editable
```

---

## 3. Import Path Examples

### In Collider (AFTER migration)

**OLD** (shared/domain/models.py):

```python
from shared.domain.models import UserContainer, Link, UserDefinition
```

**NEW** (Factory import):

```python
from agent_factory.models import Container, Link, Definition, UserObject, UserWorkspaceContainer
```

### In IADORE

```python
from agent_factory.models import UserObject, Definition
from agent_factory.parts import BaseAgent
from agent_factory.runtimes import FatRuntime
```

### In Dev-Assistant Pilot

```python
from agent_factory.models import Container, Link
from agent_factory.tools import eval_definition, seed_definition
```

---

## 4. Knowledge Sync System

### Factory `knowledge/.sync_manifest.json`

```json
{
  "version": "1.0.0",
  "last_sync": "2026-01-13T15:00:00Z",
  "sync_targets": {
    "workflows": ["graph-audit.md", "subgraph-resolution.md"],
    "knowledge": ["collider.md", "environment.md"],
    "rules": ["factory-rules.md"]
  },
  "workspaces": [
    { "path": "D:/IADORE", "enabled": true },
    { "path": "D:/dev-assistant", "enabled": true },
    { "path": "D:/my-tiny-data-collider", "enabled": false }
  ]
}
```

### Sync Script: `agent-factory/sync_to_workspaces.py`

```python
"""Sync knowledge, workflows, rules from Factory to workspaces."""
import json
import shutil
from pathlib import Path

MANIFEST = Path(__file__).parent / "knowledge" / ".sync_manifest.json"

def sync():
    with open(MANIFEST) as f:
        manifest = json.load(f)

    factory_root = Path(__file__).parent

    for workspace in manifest["workspaces"]:
        if not workspace["enabled"]:
            continue

        ws_path = Path(workspace["path"])

        # Sync workflows
        for wf in manifest["sync_targets"]["workflows"]:
            src = factory_root / ".agent" / "workflows" / wf
            dst = ws_path / ".agent" / "workflows" / wf
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"✓ Synced {wf} -> {ws_path.name}")

        # Sync knowledge (similar pattern)
        # ...

if __name__ == "__main__":
    sync()
```

**Usage**:

```powershell
cd D:\agent-factory
uv run python sync_to_workspaces.py
```

---

## 5. Git Tagging Workflow

### Factory Versioning

```powershell
# After stable Factory changes
cd D:\agent-factory
git add .
git commit -m "feat: Add CompositeDefinition merger runtime"
git tag -a v0.2.0 -m "Release: Composite definition support"
git push origin v0.2.0
```

### Workspace Update Pattern

```powershell
# In IADORE, after Factory tag
cd D:\agent-factory
git pull --tags
git checkout v0.2.0

# Workspaces with editable install auto-update
cd D:\IADORE
uv run python -c "from agent_factory.models import Definition; print(Definition.__version__)"
# Output: 0.2.0
```

### Rollback Strategy

```powershell
# If Factory v0.2.0 breaks Collider
cd D:\agent-factory
git checkout v0.1.9  # Previous stable

# All workspaces now use v0.1.9 (editable install)
```

---

## 6. AI Context Separation Strategy

### Desktop 1: IADORE (Personal)

**Antigravity Window**: Cloud AI  
**Local AI**: Personal agents (Agatha, custom assistants)  
**Context**: `IADORE/knowledge/` + `IADORE/.agent/rules/personal-rules.md`  
**Purpose**: File management, personal projects, testing Factory parts on personal data

### Desktop 2: FACTORY

**Antigravity Window**: Cloud AI (strategic discussion like this)  
**Local AI**: Godel (meta-agent, design evaluation)  
**Context**: `agent-factory/knowledge/` (master) + Modelfile.godel  
**Purpose**: Design, produce parts, research, meta-programming

### Desktop 3: COLLIDER

**Antigravity Window**: Cloud AI (code-focused)  
**Local AI**: Dev Pilot (graph debugging, container inspection)  
**Context**: `my-tiny-data-collider/.agent/` + `dev-assistant/knowledge/`  
**Purpose**: Application code, testing, assembly, runtime debugging

---

## 7. Collider v3.3 → Factory v3 Migration

### Phase 1: Dual Import (Compatibility Layer)

```python
# shared/domain/models.py (TEMPORARY)
from agent_factory.models import (
    UserObject,
    Container as FactoryContainer,
    Link as FactoryLink,
    Definition as FactoryDefinition,
)

# Aliases for backward compatibility
UserContainer = FactoryContainer
UserDefinition = FactoryDefinition
```

### Phase 2: Backend Migration

```python
# backend/main.py
- from shared.domain.models import UserContainer, Link
+ from agent_factory.models import Container, Link
```

### Phase 3: Remove Shared Models

```powershell
rm -r shared/domain/models.py
# Update all imports across backend/, runtime/, tests/
```

---

## 8. Industry Best Practices Checklist

- [x] **Single Source of Truth**: Factory produces all models
- [x] **Editable Install**: Instant propagation without rebuild
- [x] **Independent Repos**: Desktop-scoped version control
- [x] **Knowledge Replication**: AI context per workspace
- [x] **Git Tagging**: Semantic versioning for Factory releases
- [x] **Environment Isolation**: Each workspace has `.venv`
- [ ] **CI/CD Pipeline**: GitHub Actions for Factory testing
- [ ] **Pre-commit Hooks**: Ruff, mypy in Factory repo
- [ ] **Documentation**: Sphinx auto-gen from Factory docstrings

---

## Next Steps

1. Run `sync_to_workspaces.py` to populate IADORE/dev-assistant knowledge
2. Update Collider `pyproject.toml` to depend on Factory
3. Migrate Collider imports (Phase 1: dual import layer)
4. Tag Factory as `v0.2.0` (first "production" release)
5. Set up pre-commit hooks in Factory for code quality

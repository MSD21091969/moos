# DeepAgent Unified Structure

> **Date**: 2026-01-25  
> **Scope**: L1 (Workspace Agents) + L2 (Application Pilots)  
> **Status**: ✅ IMPLEMENTED

---

## Implementation Summary

### What Was Built

```
shared/pilots/
├── __init__.py               ← Exports load_pilot() + legacy specs
├── base.py                   ← ColliderPilotSpec with load() method
│
├── container/                ← CONTAINER PILOT (NEW)
│   ├── __init__.py           ← PILOT_SPEC definition
│   ├── instructions.md       ← System prompt (externalized)
│   ├── rules/
│   │   └── modifiers.md      ← Behavioral rules
│   ├── workflows/
│   │   └── share-container.md
│   └── knowledge/
│       └── collider-concepts.md
│
└── studio/                   ← STUDIO PILOT (NEW)
    ├── __init__.py
    ├── instructions.md
    ├── rules/
    │   └── modifiers.md
    ├── workflows/
    │   ├── commit-workflow.md
    │   └── upload-workflow.md
    └── knowledge/
        └── canvas-concepts.md
```

### API Endpoints Added

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/pilots` | GET | List available pilots |
| `/api/pilots/{id}` | GET | Get pilot config (for frontend) |
| `/api/pilots/{id}/workflows` | GET | Get workflows with content |

### How Frontend Loads

```typescript
// Option 1: API call (dynamic)
const response = await fetch(`/api/pilots/${pilotId}`);
const spec = await response.json();

// Option 2: Build-time (run generate_pilot_specs.py)
import pilotSpecs from "./generated/pilotSpecs.json";
```

---

## Executive Summary

### Current State
- **L1 Agents** (IDE/CLI): Use `.agent/` folder hierarchy with manifest.yaml inheritance
- **L2 Pilots** (Frontend): Use `shared/pilots/*.py` flat structure with hardcoded TypeScript copies

### Proposed State
- **Unified Pattern**: Both L1 and L2 use folder-based dynamic loading
- **Shared Structure**: `instructions.md`, `rules/`, `workflows/`, `knowledge/`
- **Single Source of Truth**: Python specs generate JSON for frontend

---

## Research Findings

### 1. Current `.agent/` Pattern (L1 - Code Implementation)

**Factory Root** (`D:\factory\.agent\`):
```
.agent/
├── manifest.yaml        ← Inheritance config
├── rules/               ← Markdown files
│   ├── sandbox.md
│   ├── identity.md
│   └── code_patterns.md
├── instructions/        ← Agent guidance
│   └── instruction_inheritance.md
└── workflows/           ← Task sequences
```

**Inheritance Chain**:
```
D:\factory\.agent\                     ← FACTORY (global)
    ↓ includes
D:\factory\workspaces\collider_apps\.agent\   ← WORKSPACE
    ↓ includes  
D:\factory\..\my-tiny-data-collider\.agent\   ← APPLICATION
```

**manifest.yaml Pattern**:
```yaml
includes:
  - path: "../../.agent"
    type: "factory"
    load:
      - rules/sandbox.md
      - rules/code_patterns.md

local:
  rules: "./rules/"
  instructions: "./instructions/"
  workflows: "./workflows/"
```

### 2. Current `shared/pilots/` Pattern (L2 - Application Runtime)

**Location**: `my-tiny-data-collider/shared/pilots/`
```
pilots/
├── __init__.py          ← Exports all specs
├── base.py              ← ColliderPilotSpec base model
├── container_pilot.py   ← Inline INSTRUCTIONS string
└── studio_pilot.py      ← Inline INSTRUCTIONS string
```

**ColliderPilotSpec Fields** (from base.py):
```python
class ColliderPilotSpec(BaseModel):
    id: str                           # "container-pilot"
    name: str
    version: str = "1.0.0"
    
    instructions: str                 # System prompt (inline string!)
    instruction_modifiers: list[str]  # Collider rules
    
    include_filesystem: bool = False
    include_todo: bool = False
    include_subagents: bool = False
    
    subagents: list[SubAgentConfig]
    skills: list[SkillConfig]         # ← Already has skill support!
    
    model: str = "gemini-2.0-flash"
    temperature: float = 0.7
```

### 3. `knowledge/__init__.py` Skill Loader

**Factory already has dynamic loading**:
```python
def load_skills(skill_name: str, skills_dir: Optional[Path] = None) -> Dict:
    """Load skill definition from markdown file."""
    if skills_dir is None:
        skills_dir = Path(__file__).parent / "skills"
    
    skill_file = skills_dir / f"{skill_name}.md"
    content = skill_file.read_text()
    
    # Parse frontmatter if present (YAML-like)
    # Returns: {"name": ..., "prompt": ..., "metadata": ...}
```

---

## Proposed Unified Structure

### L2 Pilots Folder Pattern

```
shared/pilots/
├── __init__.py               ← Pilot registry + loader
├── base.py                   ← ColliderPilotSpec base class
│
├── container/                ← CONTAINER PILOT
│   ├── __init__.py           ← ContainerPilotSpec class
│   ├── instructions.md       ← System prompt (EXTERNALIZED)
│   ├── rules/                ← Pilot-specific rules
│   │   ├── acl.md            ← ACL handling rules
│   │   └── navigation.md     ← Container nav rules
│   ├── workflows/            ← Task sequences
│   │   └── share-container.md
│   └── knowledge/            ← Domain context
│       └── collider-concepts.md
│
├── studio/                   ← STUDIO PILOT
│   ├── __init__.py           ← StudioPilotSpec class
│   ├── instructions.md       ← System prompt
│   ├── rules/
│   │   ├── file-operations.md
│   │   └── versioning.md
│   ├── workflows/
│   │   ├── commit-workflow.md
│   │   └── upload-workflow.md
│   └── knowledge/
│       └── canvas-concepts.md
│
└── graph/                    ← NEW: GRAPH PILOT
    ├── __init__.py
    ├── instructions.md
    ├── rules/
    └── knowledge/
```

### Updated `base.py` with Dynamic Loading

```python
"""
Base Pilot Specification with Dynamic Loading
=============================================
"""
from __future__ import annotations
from pathlib import Path
from typing import Any, Optional
from pydantic import BaseModel, Field


class ColliderPilotSpec(BaseModel):
    """Template for Collider pilots with folder-based loading."""
    
    # Identity
    id: str
    name: str
    version: str = "1.0.0"
    
    # Dynamic Loading Paths (NEW)
    pilot_dir: Optional[Path] = None  # e.g., shared/pilots/container/
    
    # Loaded Content (populated by load())
    instructions: str = ""
    rules: list[str] = Field(default_factory=list)
    workflows: list[dict] = Field(default_factory=list)
    knowledge: list[str] = Field(default_factory=list)
    
    # Capabilities
    include_filesystem: bool = False
    include_todo: bool = False
    include_subagents: bool = False
    subagents: list[SubAgentConfig] = Field(default_factory=list)
    
    # LLM Config
    model: str = "gemini-2.0-flash"
    temperature: float = 0.7
    max_tokens: int = 4096
    
    def load(self) -> "ColliderPilotSpec":
        """Load content from pilot_dir if set."""
        if not self.pilot_dir or not self.pilot_dir.exists():
            return self
            
        # Load instructions.md
        instructions_file = self.pilot_dir / "instructions.md"
        if instructions_file.exists():
            self.instructions = instructions_file.read_text(encoding="utf-8")
        
        # Load rules/*.md
        rules_dir = self.pilot_dir / "rules"
        if rules_dir.exists():
            for rule_file in rules_dir.glob("*.md"):
                self.rules.append(rule_file.read_text(encoding="utf-8"))
        
        # Load knowledge/*.md
        knowledge_dir = self.pilot_dir / "knowledge"
        if knowledge_dir.exists():
            for kb_file in knowledge_dir.glob("*.md"):
                self.knowledge.append(kb_file.read_text(encoding="utf-8"))
        
        # Load workflows/*.md (with frontmatter parsing)
        workflows_dir = self.pilot_dir / "workflows"
        if workflows_dir.exists():
            for wf_file in workflows_dir.glob("*.md"):
                self.workflows.append({
                    "name": wf_file.stem,
                    "content": wf_file.read_text(encoding="utf-8")
                })
        
        return self
    
    def get_full_instructions(self) -> str:
        """Compose complete system prompt."""
        parts = [self.instructions]
        
        if self.rules:
            parts.append("\n\n## Rules\n")
            parts.extend(self.rules)
        
        if self.knowledge:
            parts.append("\n\n## Context\n")
            parts.extend(self.knowledge)
        
        return "\n".join(parts)
    
    def to_frontend_config(self) -> dict[str, Any]:
        """Export for frontend consumption (API response)."""
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "instructions": self.get_full_instructions(),
            "model": self.model,
            "temperature": self.temperature,
            "maxTokens": self.max_tokens,
            "includeFilesystem": self.include_filesystem,
            "includeTodo": self.include_todo,
            "workflows": [w["name"] for w in self.workflows],
        }


def load_pilot(pilot_id: str, pilots_dir: Optional[Path] = None) -> ColliderPilotSpec:
    """
    Factory function to load a pilot by ID.
    
    Usage:
        pilot = load_pilot("container")
        config = pilot.to_frontend_config()
    """
    if pilots_dir is None:
        pilots_dir = Path(__file__).parent
    
    pilot_dir = pilots_dir / pilot_id
    if not pilot_dir.exists():
        raise ValueError(f"Pilot '{pilot_id}' not found at {pilot_dir}")
    
    # Import spec from pilot's __init__.py
    spec_module = pilot_dir / "__init__.py"
    if spec_module.exists():
        # Dynamic import
        import importlib.util
        spec = importlib.util.spec_from_file_location(f"pilots.{pilot_id}", spec_module)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Expect PILOT_SPEC in module
        if hasattr(module, "PILOT_SPEC"):
            pilot = module.PILOT_SPEC
            pilot.pilot_dir = pilot_dir
            return pilot.load()
    
    raise ValueError(f"Pilot '{pilot_id}' has no valid spec")
```

### Example: `container/__init__.py`

```python
"""Container Pilot Specification."""
from pathlib import Path
from ..base import ColliderPilotSpec, SubAgentConfig

# Minimal spec - instructions loaded from instructions.md
PILOT_SPEC = ColliderPilotSpec(
    id="container-pilot",
    name="Container Pilot",
    version="1.0.0",
    model="gemini-2.0-flash",
    temperature=0.7,
    max_tokens=2048,
    include_filesystem=False,
    include_todo=True,
    include_subagents=False,
)
```

### Example: `container/instructions.md`

```markdown
---
version: "1.0"
author: collider
---

# Container Pilot

You are the Collider Pilot, a helpful assistant for the Collider application.

## IMPORTANT: What "Container" Means in Collider

In Collider, a "container" is NOT a Docker container. It is:
- A **context wrapper** that organizes user work
- Holds **canvases** (visual workspaces for files/artifacts)
- Can be **nested** (containers within containers)
- Can be **owned** or **shared** with others

## Your Role

Help users organize their work in Collider's container system:
- Create and manage containers
- Navigate between containers
- Share containers with collaborators
- Organize canvases within containers

## Communication Style

- Be concise and helpful
- Reference their current context naturally
- Suggest next actions when relevant
```

---

## Frontend Loading Strategy

### Option A: API Endpoint (Recommended)

**Backend Route** (`main.py`):
```python
from fastapi import FastAPI
from shared.pilots import load_pilot

@app.get("/api/pilots/{pilot_id}")
async def get_pilot_config(pilot_id: str):
    """Return pilot configuration for frontend."""
    try:
        pilot = load_pilot(pilot_id)
        return pilot.to_frontend_config()
    except ValueError as e:
        raise HTTPException(404, str(e))

@app.get("/api/pilots")
async def list_pilots():
    """List available pilots."""
    pilots_dir = Path(__file__).parent.parent / "shared" / "pilots"
    return {
        "pilots": [
            d.name for d in pilots_dir.iterdir() 
            if d.is_dir() and not d.name.startswith("_")
        ]
    }
```

**Frontend Service Update** (`pilotService.ts`):
```typescript
// Instead of hardcoded specs:
async function loadPilotSpec(pilotId: string): Promise<PilotSpec> {
  const response = await fetch(`/api/pilots/${pilotId}`);
  if (!response.ok) throw new Error(`Failed to load pilot: ${pilotId}`);
  return response.json();
}

export class PilotService {
  private spec: PilotSpec | null = null;
  
  async initialize(apiKey: string, clientId: string): Promise<void> {
    // Load spec from backend
    const pilotId = clientId === "studio-app" ? "studio" : "container";
    this.spec = await loadPilotSpec(pilotId);
    
    // Initialize Gemini with loaded spec
    this.genAI = new GoogleGenerativeAI(apiKey);
    this.rebuildModel();
  }
}
```

### Option B: Build-Time Generation

**Build Script** (`generate_pilot_specs.py`):
```python
import json
from pathlib import Path
from shared.pilots import load_pilot

def generate_frontend_specs():
    pilots_dir = Path(__file__).parent / "shared" / "pilots"
    output_dir = Path(__file__).parent / "frontend" / "src" / "pilot" / "generated"
    output_dir.mkdir(exist_ok=True)
    
    specs = {}
    for pilot_dir in pilots_dir.iterdir():
        if pilot_dir.is_dir() and not pilot_dir.name.startswith("_"):
            try:
                pilot = load_pilot(pilot_dir.name)
                specs[pilot.id] = pilot.to_frontend_config()
            except Exception as e:
                print(f"Skipping {pilot_dir.name}: {e}")
    
    (output_dir / "pilotSpecs.json").write_text(
        json.dumps(specs, indent=2)
    )
    print(f"Generated specs for {len(specs)} pilots")

if __name__ == "__main__":
    generate_frontend_specs()
```

**Frontend Import**:
```typescript
import pilotSpecs from "./generated/pilotSpecs.json";

const spec = pilotSpecs["container-pilot"];
```

---

## Migration Plan

### Phase 1: Create Folder Structure (Day 1)

```powershell
# Create new structure
cd D:\factory\workspaces\collider_apps\applications\my-tiny-data-collider\shared\pilots

# Container pilot
mkdir container
mkdir container/rules
mkdir container/workflows  
mkdir container/knowledge

# Studio pilot
mkdir studio
mkdir studio/rules
mkdir studio/workflows
mkdir studio/knowledge
```

### Phase 2: Extract Instructions (Day 1)

1. Move `CONTAINER_PILOT_INSTRUCTIONS` → `container/instructions.md`
2. Move `CONTAINER_PILOT_MODIFIERS` → `container/rules/modifiers.md`
3. Repeat for studio pilot

### Phase 3: Update `base.py` (Day 2)

1. Add `pilot_dir` field
2. Add `load()` method
3. Add `load_pilot()` factory function
4. Keep backward compatibility (inline strings still work)

### Phase 4: Add Backend Endpoint (Day 2)

1. Add `/api/pilots/{id}` route
2. Add `/api/pilots` list route
3. Test with curl/Postman

### Phase 5: Update Frontend (Day 3)

1. Replace hardcoded specs with API fetch
2. Handle loading states
3. Add spec caching

### Phase 6: Verify Parity (Day 3)

1. Compare old vs new system prompts
2. Test both pilots end-to-end
3. Remove old hardcoded specs from `pilotService.ts`

---

## Alignment with L1 `.agent/` Pattern

| Feature | L1 (.agent/) | L2 (pilots/) |
|---------|-------------|--------------|
| **Manifest** | `manifest.yaml` | `__init__.py` (spec) |
| **Instructions** | `instructions/*.md` | `instructions.md` |
| **Rules** | `rules/*.md` | `rules/*.md` |
| **Workflows** | `workflows/*.md` | `workflows/*.md` |
| **Knowledge** | via sync/symlinks | `knowledge/*.md` |
| **Inheritance** | `includes:` in manifest | Python import chain |

### Key Difference

- **L1** is read by IDE (VS Code) which understands `.agent/` convention
- **L2** is loaded by Python, then served to frontend via API

### Potential Unification

Could create a universal loader that reads either format:

```python
def load_agent_context(path: Path) -> AgentContext:
    """Load from either .agent/ or pilots/ format."""
    
    if (path / "manifest.yaml").exists():
        return load_from_manifest(path)  # L1 format
    elif (path / "__init__.py").exists():
        return load_from_pilot(path)      # L2 format
    else:
        raise ValueError(f"Unknown agent format at {path}")
```

---

## Files to Modify

### Create New Files

| File | Purpose |
|------|---------|
| `shared/pilots/container/__init__.py` | Minimal spec definition |
| `shared/pilots/container/instructions.md` | Externalized system prompt |
| `shared/pilots/container/rules/modifiers.md` | Extracted modifiers |
| `shared/pilots/studio/__init__.py` | Minimal spec definition |
| `shared/pilots/studio/instructions.md` | Externalized system prompt |
| `shared/pilots/studio/rules/modifiers.md` | Extracted modifiers |

### Modify Existing Files

| File | Changes |
|------|---------|
| `shared/pilots/base.py` | Add `pilot_dir`, `load()`, `load_pilot()` |
| `shared/pilots/__init__.py` | Export `load_pilot` |
| `backend/main.py` | Add `/api/pilots/` routes |
| `frontend/src/pilot/pilotService.ts` | Replace hardcoded specs with API fetch |

### Delete After Migration

| File | Reason |
|------|--------|
| `shared/pilots/container_pilot.py` | Replaced by `container/` folder |
| `shared/pilots/studio_pilot.py` | Replaced by `studio/` folder |

---

## Appendix: pydantic-deep Reference

The `pydantic-deep` library (used in `parts/agents/collider_pilot.py`) provides:

```python
from pydantic_deep import create_deep_agent, DeepAgentDeps

agent = create_deep_agent(
    model="ollama:deepseek-r1:14b",
    instructions="...",           # System prompt
    tools=[...],                  # Tool functions
    include_filesystem=True,      # Built-in file tools
    deps_type=DeepAgentDeps       # Dependency injection type
)
```

The `ColliderPilotSpec` mirrors this pattern for frontend consumption:
- `instructions` → System prompt
- `include_filesystem` → Whether to enable file tools
- `skills` → Additional capabilities (maps to `skill_directories` concept)

---

*Research completed: 2026-01-25*

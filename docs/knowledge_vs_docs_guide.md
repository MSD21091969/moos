# knowledge/ vs docs/ - Directory Purpose Distinction

## Core Difference

```
knowledge/   → AI Agent Context (machine-consumable)
docs/        → Human Documentation (human-readable)
```

---

## `/knowledge` - AI Agent Context

**Purpose**: **Direct agent consumption** via system prompts, RAG, skill loading

**Consumers**:

- Local AI agents (Agatha, Collider Pilot, etc.)
- DeepAgent skill system
- IDE Code Assist (context injection)
- Vector stores / embeddings

**Format Requirements**:

- **Optimized for LLM parsing**
- Concise, structured markdown
- Minimal prose, maximum signal
- Frontmatter metadata (YAML)
- Code examples inline
- **No lengthy explanations**

**Content Types**:

```
knowledge/
├── factory_domain.md          # Core concepts (Container/Link/Definition)
├── formal_systems.md          # Mathematical/logical foundations
├── reasoning_protocol.md      # Agent reasoning patterns
├── skills/                    # Agent skill definitions
│   ├── graph_audit.md
│   └── container_inspector.md
├── research/                  # Research findings (for agent reference)
│   └── pydantic_graph/
│       ├── findings.md        # Condensed research results
│       └── ...
└── development/               # Implementation algorithms
    ├── graph_integration_roadmap.md
    └── composite_definitions.md
```

**Example - knowledge/factory_domain.md**:

````markdown
# Factory Domain Knowledge

## Container (Recursive)

```python
class Container:
    links: list[Link]
    position: Position
```
````

- R=1: First space (I/O boundaries only)
- R>1: Nested spaces (peer topology)

## Link (West → North → East)

- owner_id: West container
- definition_id: North (behavior)
- eastside_container_id: East container

```

**Style**: Dense, reference-oriented, code-heavy

---

## `/docs` - Human Documentation

**Purpose**: **Human understanding** via reading, tutorials, walkthroughs

**Consumers**:
- Developers
- Team members
- Future you (onboarding)
- Documentation sites
- IDE hover hints (secondary)

**Format Requirements**:
- **Optimized for human comprehension**
- Narrative explanations
- Context and rationale
- Step-by-step guides
- Visual aids (diagrams, screenshots)
- **Longer is fine if it helps understanding**

**Content Types**:
```

docs/
├── INDEX.md # Master index (navigation)
├── dev_environment_setup.md # Developer onboarding
├── local_ai_infrastructure.md # Infrastructure explanation
├── knowledge_organization_plan.md # This meta-document
├── architecture/ # Design decisions (WHY)
│ ├── recursive_containers.md
│ ├── link_topology.md
│ └── definition_system.md
├── planning/phases/ # Project planning
│ ├── phase_1_foundation.md
│ └── phase_2_graph_integration.md
├── conversations/ # Historical context
│ └── README.md
└── walkthroughs/ # Process documentation
└── legacy_cleanup.md

````

**Example - docs/architecture/recursive_containers.md**:
```markdown
# Recursive Container Architecture

## Pattern: R=0 → R=1 → R>1

### R=0: UserObject (Root)

**Role**: Pure ownership context, NOT a space
**Holds**: Account info, registries, workspace reference
**NOT displayed**: As graph or visual node

The UserObject serves as the root of the entire Container hierarchy.
Unlike Containers, it is not visualized as a node in the graph...
[continues with detailed explanation]

### Code Example
```python
# R=0: UserObject
user = UserObject(auth_id="local", email="user@localhost")
...
````

### Visual Representation

[ASCII diagram showing hierarchy]

````

**Style**: Narrative, educational, context-rich

---

## Practical Guidelines

### When to Use `/knowledge`

✅ **Agent skill definitions** (loaded at runtime)
```markdown
---
name: graph_audit
description: Forensic graph analysis
---
# Instructions for agent...
````

✅ **Core domain concepts** (injected into agent prompts)

```markdown
# Container Model

- Pure space, holds Links
- No definition_id on Container
```

✅ **Research findings** (for agent reference)

```markdown
# Pydantic-Graph Findings

- Use beta for parallel execution
- Container → Node mapping: ...
```

✅ **Implementation algorithms** (agent can follow)

```markdown
# Composite Definition Algorithm

1. Extract all Links
2. Find boundaries (predecessors == [])
3. Aggregate schemas
```

### When to Use `/docs`

✅ **Architecture decisions** (explain WHY)

```markdown
# Why Link-Based Edges?

We chose to put relationships on Links rather than Containers because:

1. Separation of concerns (space vs relationship)
2. Enables recursive nesting without circular refs
3. Allows multiple dependency types per Container
```

✅ **Setup guides** (step-by-step)

````markdown
# Dev Environment Setup

## Prerequisites

1. Install Python 3.12+
2. Install uv: `pip install uv`
3. Clone repository

## Step 1: Create Virtual Environment

```powershell
cd D:\agent-factory
uv venv
```
````

✅ **Project planning** (phases, milestones)

```markdown
# Phase 2: Graph Integration

## Deliverables

- [ ] Model mapping
- [ ] Graph builder
- [ ] Execution runtime
```

✅ **Walkthroughs** (document what was done)

```markdown
# Legacy Cleanup Walkthrough

## What Was Removed

- parts/base_agent.py (OLD pattern)
- Reason: Consolidate to DeepAgent pattern
```

---

## Content Migration Strategy

### IADORE Knowledge Files → Factory

| File                            | Type              | Destination                                            | Reason                   |
| ------------------------------- | ----------------- | ------------------------------------------------------ | ------------------------ |
| `Collider Research Plan v2.pdf` | Research          | `knowledge/research/collider/`                         | Agent reference material |
| `Implementing PIKE-RAG.pdf`     | Research          | `knowledge/research/pike_rag/`                         | Implementation patterns  |
| `Recursive Orchestration.pdf`   | Research          | `knowledge/research/orchestration/`                    | System design concepts   |
| `gemini 3 answer to prompt.txt` | Research findings | `knowledge/research/pydantic_graph/gemini_findings.md` | Research output          |

**Processing**:

1. **Extract** key findings from PDFs
2. **Condense** into markdown (agents can't read PDFs directly)
3. **Store** original PDFs in `docs/references/` (human archive)
4. **Create** markdown summaries in `knowledge/research/` (AI consumption)

---

## Example: Dual Documentation

### Same Topic, Two Audiences

**knowledge/research/pydantic_graph/findings.md**:

```markdown
# Pydantic-Graph Findings

## Recommendation: Use beta

- Parallel execution (Fork/Join)
- Enhanced I/O typing
- Better for recursive Containers

## Mappings

- Container → Node (with R handling)
- Link → Edge (predecessors/successors)
- Definition → Graph (composite subgraphs)
```

**docs/architecture/pydantic_graph_integration.md**:

```markdown
# Pydantic-Graph Integration Architecture

## Why pydantic-graph.beta?

After extensive research (see knowledge/research/pydantic_graph/),
we chose the beta version because:

1. **Parallel Execution**: Our Container graphs often have parallel
   branches that can execute concurrently. The beta's Fork/Join nodes
   enable this naturally.

2. **Enhanced Type Safety**: The beta's InputT/OutputT types map
   cleanly to our Definition.input_schema/output_schema, providing
   better compile-time guarantees.

[continues with detailed rationale, diagrams, examples]
```

---

## Summary Table

| Aspect       | `/knowledge`        | `/docs`                    |
| ------------ | ------------------- | -------------------------- |
| **Audience** | AI Agents           | Humans                     |
| **Length**   | Concise             | As needed                  |
| **Style**    | Reference           | Narrative                  |
| **Code**     | Inline examples     | Full walkthroughs          |
| **Diagrams** | ASCII/Mermaid       | Complex visuals OK         |
| **Updates**  | When logic changes  | When understanding changes |
| **Format**   | Structured markdown | Flexible                   |

---

## Current Factory Structure Usage

### ✅ Correct Usage

- `knowledge/factory_domain.md` - Concise domain ref for agents ✅
- `knowledge/skills/graph_audit.md` - Agent skill definition ✅
- `docs/architecture/recursive_containers.md` - Human explanation ✅
- `docs/planning/phases/phase_2_graph_integration.md` - Human planning ✅

### 🔄 Could Improve

- Research PDFs in IADORE → Need markdown summaries for agents
- Long explanations in knowledge/ → Move narrative parts to docs/
- Agent-facing algorithms in docs/ → Move to knowledge/development/

---

## For Your IADORE Files

**Recommended Integration**:

1. **PDFs (3 files)**:

   - Store originals: `docs/references/iadore_research/`
   - Extract summaries: `knowledge/research/<topic>/summary.md`

2. **gemini 3 answer to prompt.txt**:
   - Copy to: `knowledge/research/pydantic_graph/gemini_findings.md`
   - Keep structured for agent reference

**Why Split**:

- Agents can't parse PDFs natively (need markdown)
- Humans want originals (citations, full context)
- Both versions serve different needs

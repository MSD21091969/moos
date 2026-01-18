# Factory Knowledge Organization Plan

## Objective

Integrate Gemini 3.0 Deep Research findings (pydantic-graph integration) into Factory workspace structure to enable:

1. Local agent knowledge access
2. IDE Code Assist contextual awareness
3. Phased development workflow
4. Research findings archival

---

## Proposed Factory Structure

```
D:\agent-factory\
├── knowledge\                    # Core knowledge (exists)
│   ├── skills\                   # Agent skills (exists)
│   ├── factory_domain.md         # EXISTS
│   ├── formal_systems.md         # EXISTS
│   ├── reasoning_protocol.md     # EXISTS
│   │
│   ├── research\                 # NEW - Research archives
│   │   ├── pydantic_graph\
│   │   │   ├── findings.md       # Gemini 3 research summary
│   │   │   ├── library_comparison.md
│   │   │   ├── model_mapping.md
│   │   │   └── implementation_patterns.md
│   │   └── README.md
│   │
│   └── development\              # NEW - Dev roadmaps
│       ├── graph_integration_roadmap.md
│       ├── composite_definitions.md
│       └── execution_strategy.md
│
├── docs\                         # Documentation (exists)
│   ├── pipeline_status.md        # EXISTS
│   │
│   ├── conversations\            # NEW - Important conversations
│   │   ├── 2026-01-13_local_ai_infrastructure.md
│   │   ├── 2026-01-14_pydantic_graph_research.md
│   │   └── README.md
│   │
│   ├── architecture\             # NEW - Architecture decisions
│   │   ├── recursive_containers.md
│   │   ├── link_topology.md
│   │   └── definition_system.md
│   │
│   └── planning\                 # NEW - Planning docs
│       ├── phases\
│       │   ├── phase_1_foundation.md
│       │   ├── phase_2_graph_integration.md
│       │   ├── phase_3_composite_defs.md
│       │   └── phase_4_multi_agent.md
│       └── milestones.md
│
├── .agent\
│   ├── workflows\
│   └── rules\
│       └── development-context.md  # NEW - Points to research/dev files
│
└── workspace-guide.md           # EXISTS - Will update
```

---

## Knowledge Organization Types

### 1. Research Archives (`knowledge/research/`)

**Purpose**: Store completed research findings  
**Consumers**: Local agents, IDE Code Assist, developers  
**Format**: Markdown with code examples

- `pydantic_graph/findings.md` - Gemini 3 research summary
- `pydantic_graph/library_comparison.md` - Regular vs beta analysis
- `pydantic_graph/model_mapping.md` - Container/Link/Definition mappings
- `pydantic_graph/implementation_patterns.md` - Code patterns

### 2. Development Roadmaps (`knowledge/development/`)

**Purpose**: Actionable development plans from research  
**Consumers**: Local agents (planning workflows), developers  
**Format**: Structured markdown with tasks

- `graph_integration_roadmap.md` - Phased implementation plan
- `composite_definitions.md` - I/O aggregation algorithm
- `execution_strategy.md` - DeepAgent + pydantic-graph integration

### 3. Conversations (`docs/conversations/`)

**Purpose**: Archive significant IDE conversations  
**Consumers**: IDE Code Assist (context building), knowledge review  
**Format**: Dated markdown exports

- `2026-01-13_local_ai_infrastructure.md` - Full conversation export
- `2026-01-14_pydantic_graph_research.md` - This conversation

### 4. Architecture Docs (`docs/architecture/`)

**Purpose**: Core architecture decisions and patterns  
**Consumers**: Developers, local agents, documentation  
**Format**: Structured markdown

- `recursive_containers.md` - R=0 → R=1 → R>1 pattern
- `link_topology.md` - West → North → East, predecessors/successors
- `definition_system.md` - Atomic vs composite Definitions

### 5. Planning Phases (`docs/planning/phases/`)

**Purpose**: Break development into discrete phases  
**Consumers**: Project management, local agents (workflow selection)  
**Format**: Phase-specific markdown

- `phase_1_foundation.md` - Models + toolsets (COMPLETE)
- `phase_2_graph_integration.md` - pydantic-graph integration (NEXT)
- `phase_3_composite_defs.md` - I/O aggregation + UX topology
- `phase_4_multi_agent.md` - Agent-driven graph building

---

## Development Context Rule

Create `.agent/rules/development-context.md` (auto-loaded by local agents):

```markdown
# Factory Development Context

## Current Phase: Graph Integration (Phase 2)

### Active Research

- Location: `knowledge/research/pydantic_graph/`
- Topic: Integrating pydantic-graph (regular/beta) with Container/Link/Definition models

### Development Roadmaps

- Primary: `knowledge/development/graph_integration_roadmap.md`
- Supporting: `knowledge/development/composite_definitions.md`

### Architecture References

- Containers: `docs/architecture/recursive_containers.md`
- Links: `docs/architecture/link_topology.md`
- Definitions: `docs/architecture/definition_system.md`

### Recent Conversations

- Infrastructure setup: `docs/conversations/2026-01-13_local_ai_infrastructure.md`
- pydantic-graph research: `docs/conversations/2026-01-14_pydantic_graph_research.md`

### Models (Source of Truth)

- Location: `D:\agent-factory\models\`
- Container, Link, Definition, UserObject, UserWorkspaceContainer
```

---

## Workspace Guide Updates

Add to `workspace-guide.md`:

```markdown
## Research & Development Context

### Knowledge Locations

**Research Findings**: `knowledge/research/`

- pydantic-graph integration findings
- Library comparisons, code patterns

**Development Roadmaps**: `knowledge/development/`

- Phased implementation plans
- Algorithms, strategies

**Conversations**: `docs/conversations/`

- Archived IDE sessions with Antigravity
- Context for design decisions

**Architecture**: `docs/architecture/`

- Core patterns (recursive Containers, Link topology, Definitions)

**Planning**: `docs/planning/phases/`

- Phase 1: Foundation (COMPLETE)
- Phase 2: Graph Integration (ACTIVE)
- Phase 3: Composite Definitions
- Phase 4: Multi-Agent Workflows

### Current Development Phase

**Phase 2: Graph Integration**

**Objective**: Integrate pydantic-graph (regular or beta) with Collider models

**Key Files**:

- Research: `knowledge/research/pydantic_graph/findings.md`
- Roadmap: `knowledge/development/graph_integration_roadmap.md`
- Architecture: `docs/architecture/*`

**Next Steps**: See phase document for detailed tasks
```

---

## Implementation Steps

### Step 1: Create Directory Structure

```powershell
# Research archives
New-Item -Path "D:\agent-factory\knowledge\research\pydantic_graph" -ItemType Directory
New-Item -Path "D:\agent-factory\knowledge\development" -ItemType Directory

# Conversations
New-Item -Path "D:\agent-factory\docs\conversations" -ItemType Directory

# Architecture
New-Item -Path "D:\agent-factory\docs\architecture" -ItemType Directory

# Planning phases
New-Item -Path "D:\agent-factory\docs\planning\phases" -ItemType Directory
```

### Step 2: Populate Research Files

- Move Gemini 3 findings to `knowledge/research/pydantic_graph/findings.md`
- Extract specific topics (library comparison, mappings, patterns)

### Step 3: Create Development Roadmaps

- Write `graph_integration_roadmap.md` (phased tasks)
- Write `composite_definitions.md` (algorithm spec)
- Write `execution_strategy.md` (DeepAgent integration)

### Step 4: Archive Conversations

- Export this conversation → `docs/conversations/2026-01-14_pydantic_graph_research.md`
- Export previous conversation → `docs/conversations/2026-01-13_local_ai_infrastructure.md`

### Step 5: Document Architecture

- Write `recursive_containers.md` (R=0 → R>1 pattern)
- Write `link_topology.md` (West → North → East)
- Write `definition_system.md` (atomic/composite)

### Step 6: Create Phase Documents

- Phase 1: Foundation (mark complete)
- Phase 2: Graph Integration (mark active, list tasks)
- Phase 3: Composite Definitions (planned)
- Phase 4: Multi-Agent (planned)

### Step 7: Update Workspace Files

- Add development context to `workspace-guide.md`
- Create `.agent/rules/development-context.md`
- Update sync manifest to replicate to other workspaces

---

## Local Agent Behavior

With this structure:

- Local agents **auto-load** development context
- Can reference research findings: `load_knowledge("research/pydantic_graph/findings")`
- Can follow roadmaps: `follow_roadmap("graph_integration")`
- Can query architecture: `explain_pattern("recursive_containers")`

## IDE Code Assist Behavior

With conversations + knowledge:

- Code Assist has **full context** of design decisions
- Can reference archived conversations for rationale
- Can suggest code based on research patterns
- Understands current phase and next steps

---

## Benefits

✅ **Organized Knowledge**: Research findings in structured location  
✅ **Phased Development**: Clear milestones and tasks  
✅ **Context Persistence**: Conversations archived for future reference  
✅ **Agent Awareness**: Local agents know current phase and resources  
✅ **IDE Intelligence**: Code Assist has design decision context  
✅ **Collaboration**: Other developers can onboard via docs

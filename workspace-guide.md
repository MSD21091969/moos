# Agent Factory Workspace Guide

**AI Role**: Cloud AI (Antigravity IDE) - Design, architecture, meta-programming  
**Purpose**: Upstream parts producer for all workspaces  
**Version**: v0.4.0 (January 2026 - DeepAgent Integration)

---

## Current State (January 2026)

### Phase 4.5 Complete ✅

**pydantic-deepagents** integration verified with GCP Vertex AI:

- ✅ Agent creation (`create_deep_agent()`)
- ✅ Tool calling, Skills system, Subagent delegation
- ✅ FilesystemBackend, File uploads
- ✅ Vision/Multimodal with Gemini
- ✅ Full Stack Demo (FastAPI + Next.js + WebSockets)

**Active Folders:**

| Folder                    | Purpose                            |
| ------------------------- | ---------------------------------- |
| `models_v2/`              | Core architecture (19 files)       |
| `deepagent-test/`         | VStorm framework experiments       |
| `demos/full-stack-agent/` | FastAPI + Next.js real-time chat   |
| `knowledge/`              | Math + development docs            |
| `godel/`                  | Pilot API (observation collection) |

---

## Workspace Structure

```
D:\agent-factory\
├── models_v2\           # Definition-centric architecture (19 files)
│   ├── definition.py    # AtomicDefinition, CompositeDefinition
│   ├── graph.py         # Graph owns nodes/edges
│   ├── builder.py       # ColliderGraphBuilder API
│   └── graph_tensor.py  # GPU tensor operations
│
├── deepagent-test\      # NEW: VStorm framework testing
│   ├── README.md        # AI-optimized documentation
│   ├── FEATURE_COVERAGE.md # Gap analysis
│   ├── experiments\     # exp1-7 (GCP verified)
│   ├── skills\          # SKILL.md examples
│   └── archive\         # Legacy docs
│
├── demos\
│   ├── full-stack-agent\   # NEW: FastAPI + Next.js + WebSockets
│   │   ├── backend\        # pydantic-deep coordinator
│   │   └── frontend\       # Next.js 15 chat UI
│   └── graph-3d-demo.html  # Three.js visualization
│
├── knowledge\
│   ├── index.md         # AI entry point
│   ├── development\     # Progress, roadmap
│   └── mathematics\     # Category, scope, tensors
│
├── godel\               # Pilot API (port 8001)
│
└── .agent\workflows\    # Workflows
```

---

## Technology Stack

### Agent Framework (Phase 4.5)

| Component     | Technology                       | Location                           |
| ------------- | -------------------------------- | ---------------------------------- |
| Agent Runtime | `pydantic-deepagents`            | `deepagent-test/`                  |
| LLM Provider  | GCP Vertex AI (Gemini 2.5 Flash) | All agents                         |
| Backend       | FastAPI                          | `demos/full-stack-agent/backend/`  |
| Frontend      | Next.js 15 + TailwindCSS         | `demos/full-stack-agent/frontend/` |
| Communication | WebSockets                       | `/ws/chat`                         |
| Storage       | FilesystemBackend                | `./data/full-stack-storage/`       |

### Core Architecture (Phase 1-4)

| Object        | Role                    | File                |
| ------------- | ----------------------- | ------------------- |
| Definition    | Functor - I/O interface | `definition.py`     |
| Graph         | Owns nodes/edges        | `graph.py`          |
| GraphTensor   | GPU-ready matrix        | `graph_tensor.py`   |
| NodeEmbedding | 128-dim vectors         | `node_embedding.py` |

---

## Development Phases

### Completed

- [x] Phase 1-3: Foundation + Graph Builder
- [x] Phase 4: Tensor Layer (GPU operations, embeddings)
- [x] **Phase 4.5: DeepAgent Research & Verification**
  - 7 experiments (exp1-7) with GCP Gemini
  - Full Stack Studio (FastAPI + Next.js + WebSockets)
  - Collaborative Canvas (Drafts & Concurrency)
  - VStorm feature coverage analysis

### Next

- [ ] Phase 5: Agent Integration into Collider
  - TodoToolset → Graph execution plans
  - SessionManager → User isolation
  - GraphBackend → Collider persistence
- [ ] Phase 6: Visual UX (Three.js editor)

---

## Quick Commands

| Task                    | Command                                                                     |
| ----------------------- | --------------------------------------------------------------------------- |
| Run Full Stack Backend  | `cd demos/full-stack-agent/backend && uv run uvicorn app.main:app --reload` |
| Run Full Stack Frontend | `cd demos/full-stack-agent/frontend && npm run dev`                         |
| Test models_v2          | `python -c "from models_v2 import Graph, ColliderGraphBuilder"`             |
| Run Pilot API           | `uv run python godel/pilot_api.py`                                          |

---

## Documentation Index

| Location                             | Content                        |
| ------------------------------------ | ------------------------------ |
| `deepagent-test/README.md`           | VStorm framework + experiments |
| `deepagent-test/FEATURE_COVERAGE.md` | Feature gap analysis           |
| `knowledge/development/`             | Progress, roadmap              |
| `knowledge/mathematics/`             | Category theory, tensors       |
| `docs/architecture/`                 | models_v2, node, edge          |

---

## VStorm References

- [pydantic-deepagents](https://github.com/vstorm-co/pydantic-deepagents) - Agent creation framework
- [full-stack-fastapi-nextjs-llm-template](https://github.com/vstorm-co/full-stack-fastapi-nextjs-llm-template) - Production template

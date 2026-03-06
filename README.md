# mo:os

**Multi-Object Operating System** — a runtime kernel for compositional AI-human computation.

> Content IS the application.

---

## What is mo:os?

mo:os is an open-source operating system built on a single axiom: **everything is a Container**. Users, tools, models, applications, memory, UI surfaces, and the OS itself are all the same recursive data structure. State mutates through exactly four typed graph operations. The kernel is written in Go. Persistence is PostgreSQL + pgvector. The model layer is provider-agnostic. The math is category theory.

Traditional systems silo data into files and constrain logic inside applications. mo:os dissolves these boundaries. Data, logic, and context exist as nodes in a shared spatial graph. You don't open an app — you navigate a topology. The data structures themselves render the interface.

### The "OpenClaw" Playbook Principles

mo:os adopts the principles of successful open-source AI tooling:

- **Absolute Data Sovereignty:** Users host mo:os locally. It is a verifiable, structural graph database (PostgreSQL + JSONB). You control your AI memory and files.
- **Platform Agnosticism (The Functor):** mo:os abstracts the UI and compute providers via functorial projection to prevent vendor lock-in. **Providers are interchangeable. Your graph is your own.** The physical machine (Z440) acts as the Semantic Functor, preserving abstract categorical mappings to execution.
- **Frictionless Onboarding:** Future milestones include a 1-click install abstraction, hiding Docker/Go/Postgres complexity behind simple execution.

### The One Axiom

A **Container** is a typed node with:

- A **URN** (universal resource name) for global addressing
- A **kernel** (opaque payload — the content)
- An **interface** (typed input/output ports via JSON Schema)
- **Permissions** (ACL entries governing access)
- **Parent Pointer** (recursive nesting)
- **Wires** (typed edges connecting ports)

**Category-as-Container:** A category itself is stored as a container (`kind=category`), eliminating the split between JSON and DB, satisfying the DB_Is_Truth axiom, and making the superset ontology entirely graph-native.

---

## The Superset & System 3 Reasoning

### The Interface Problem

mo:os replaces fragile AI "skills" with the **Superset**: a schema of graph mutations. The LLM outputs morphisms against a local topology instead of calling arbitrary APIs. The Superset strictly defines foundational operations: `ADD`, `LINK`, `MUTATE`, `UNLINK`.

### System 3 Reasoning: LogicGraphs and Process-Verified GRPO

Large Language Models prioritize semantic fluency over logical entailment, leading to result-oriented hallucinations and insufficient premise deductions. To achieve authentic **System 3 reasoning**, mo:os does not rely on text-based chains of thought.

Instead, mo:os structures inference as a Directed Acyclic Graph (DAG) with multi-path branching (LogicGraphs).

1. **CAN_FORK:** The kernel forks the in-memory graph into CUDA-addressable memory (~10MB VRAM budget for 10K containers).
2. **gRPC Transport:** Explicit reasoning graphs (LogicGraphs) are transported over gRPC to formal solvers (Python execution, Prover9, Lean 4).
3. **Process-Verified Validation:** Solvers verify the structural validity and logical soundness of the graph nodes, returning a boolean `true`/`false` or a programmatic output. This absolute mathematical reward drives a **Group Relative Policy Optimization (GRPO)** pipeline, discarding LLM semantic evaluation entirely for factual logical steps.
4. **Collapse:** Low-scoring branches are pruned, and the verified, winning branch collapses its topological delta back to the Resting State (PostgreSQL).

---

## Roadmap & Execution (ACT 2026 Focus)

| Phase       | Focus                                                                                                                                                                                                                                    | Status       |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------ |
| **Phase A** | Specification, ontology wiring, container schema, and `kind` column flexibility (zero schema migration for new categories).                                                                                                              | Complete     |
| **Phase B** | Graph-Driven Bootstrap. Kernel startup queries `containers` table for available categories (`compute.*`, `model.*`) to resolve dispatch providers dynamically.                                                                           | Active       |
| **Phase C** | **Composability Safety (Step 10):** Pre-check interface port schema compatibility on `LINK` insertion. <br> **`CAN_HYDRATE` (Step 13):** Read template containers, clone topology into new URN namespace.                                | Planned      |
| **Phase D** | **`CAN_FORK` (Step 14):** Fork in-memory graph into VRAM, run parallel reasoning evaluation, and collapse. <br> **`CAN_FEDERATE` (Step 15):** Discovery via mDNS and ontology version negotiation before `LINK`.                         | Planned      |
| **Phase 5** | **System 3 / LogicGraph gRPC Execution.** Multi-path DAG reasoning evaluated by neuro-symbolic solvers over gRPC. Process-Verified GRPO pipeline replacing heuristic LLM evaluation. Vector Space Semantic Memory. MCP Interoperability. | Active Focus |

_(See `.agent/knowledge/03_implementation/implementation_details.md` for full implementation strategies)._

---

## Technical Stack

### Backend — Go 1.23+ & PostgreSQL 16+

- **Database:** `jackc/pgx/v5` (JSONB, recursive CTEs). PostgreSQL `kind` column uses no CHECK constraint, allowing arbitrary ontology expansion.
- **REST & Websocket:** Native `net/http` and `gorilla/websocket` for JSON-RPC bidirectional syncing.
- **Active State Cache:** Redis for event pubsub.

### Frontend — React 19 & XYFlow

The frontend contains **zero business logic**. It is purely a functorial projection—rendering the state of the graph Database without processing rules locally.

---

## Getting Started

### Prerequisites

- Go 1.23+
- Node.js 20+ with pnpm
- PostgreSQL 16+ with pgvector
- Redis 7+
- Python 3.12+ (for SDK and Solver endpoints)

### Run the Stack

```powershell
# Full stack
./workspaces/FFS1_ColliderDataSystems/start-moos-stack.ps1

# Or Backend locally
cd workspaces/FFS1_ColliderDataSystems/FFS2_ColliderBackends_MultiAgentChromeExtension/moos
go run ./cmd/kernel

# Frontend
cd workspaces/FFS1_ColliderDataSystems/FFS3_ColliderApplicationsFrontendServer
pnpm nx serve ffs6
```

### Contributing

- **Commits:** Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`)
- **Governance:** Treat `.agent/manifest.yaml` inheritance as authoritative wiring.
- **Open Source Ready:** Prioritize pure infrastructure. Strip internal FFS agent governance configs that might confuse new users before the open-source extraction.

---

_Providers are interchangeable. Your graph is your own._

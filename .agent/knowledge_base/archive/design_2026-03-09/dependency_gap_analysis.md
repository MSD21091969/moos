# Dependency Gap Analysis

**Date:** 2026-03-09  
**Status:** Inventory snapshot — Wave 0 kernel live, Chrome Extension greenfield  
**Depends on:** 20260309-sidepanel-plan.md (Phase plan), 20260309-hypergraph-approach.md

---

## Current vs. Required: Full Inventory

### Languages & Runtimes

| Item          | Category  | Status      | Required By                  | Notes                                     |
| ------------- | --------- | ----------- | ---------------------------- | ----------------------------------------- |
| Go 1.23+      | Runtime   | **Have**    | Kernel                       | `go.mod` declares 1.23.0                  |
| TypeScript    | Language  | **Missing** | Phase 2–4 (Chrome Extension) | React + XYFlow canvas                     |
| Node.js / npm | Runtime   | **Missing** | Phase 2–4                    | Build toolchain for extension             |
| PowerShell 5+ | Scripting | **Have**    | Installers                   | `bootstrap.ps1`, `seed-explorer-demo.ps1` |

---

### Go Dependencies (External)

| Item                      | Category         | Status   | Required By    | Notes                       |
| ------------------------- | ---------------- | -------- | -------------- | --------------------------- |
| `jackc/pgx/v5` v5.7.6     | Go module        | **Have** | Postgres store | Only external Go dependency |
| `stretchr/testify` v1.8.1 | Go module (test) | **Have** | All Go tests   | Assertions, require         |

**Transitive (already resolved):** pgpassfile, pgservicefile, puddle/v2, golang.org/x/crypto, golang.org/x/sync, golang.org/x/text, go-spew, go-difflib, yaml.v3

---

### Go Packages (Internal — to create)

| Item                         | Category  | Status      | Required By      | Notes                                    |
| ---------------------------- | --------- | ----------- | ---------------- | ---------------------------------------- |
| `internal/core/traversal.go` | Go source | **Missing** | Phase 1, step 6  | Pure `ReachableNodes`, `InducedSubgraph` |
| `cmd/agent/main.go`          | Go source | **Missing** | Phase 5, step 20 | Agent write-lens stub                    |

---

### JavaScript / TypeScript Dependencies

| Item                        | Category      | Status      | Required By      | Notes                                    |
| --------------------------- | ------------- | ----------- | ---------------- | ---------------------------------------- |
| `react`                     | JS framework  | **Missing** | Phase 2          | UI library                               |
| `react-dom`                 | JS framework  | **Missing** | Phase 2          | DOM renderer                             |
| `@xyflow/react` v12+        | JS library    | **Missing** | Phase 3          | Port-based graph canvas (was React Flow) |
| `zustand`                   | JS library    | **Missing** | Phase 2          | Lightweight state management             |
| `vite`                      | JS build tool | **Missing** | Phase 2          | Fast HMR, extension bundling             |
| `typescript`                | JS toolchain  | **Missing** | Phase 2          | Type checking                            |
| `@types/react`              | JS types      | **Missing** | Phase 2          | TypeScript definitions                   |
| `@types/react-dom`          | JS types      | **Missing** | Phase 2          | TypeScript definitions                   |
| `@types/chrome`             | JS types      | **Missing** | Phase 2          | Chrome Extension API types               |
| `@dagrejs/dagre` or `elkjs` | JS library    | **Missing** | Phase 3, step 11 | Auto-layout for graph canvas             |

---

### Chrome Extension Artifacts

| Item                              | Category   | Status      | Required By      | Notes                                |
| --------------------------------- | ---------- | ----------- | ---------------- | ------------------------------------ |
| `manifest.json` (Manifest V3)     | Config     | **Missing** | Phase 2, step 7  | Extension declaration, sidepanel API |
| `sidepanel.html`                  | HTML       | **Missing** | Phase 2, step 7  | Sidepanel entry point                |
| `background.js`                   | JS source  | **Missing** | Phase 2, step 7  | Service worker                       |
| `src/App.tsx`                     | TSX source | **Missing** | Phase 2, step 8  | Root React component                 |
| `src/api/kernel.ts`               | TS source  | **Missing** | Phase 2, step 8  | Kernel HTTP client                   |
| `src/store/graphStore.ts`         | TS source  | **Missing** | Phase 2, step 8  | Zustand graph state                  |
| `src/store/identity.ts`           | TS source  | **Missing** | Phase 6, step 24 | Actor URN in `chrome.storage`        |
| `src/nodes/GraphNode.tsx`         | TSX source | **Missing** | Phase 3, step 9  | Kind-driven custom XYFlow node       |
| `src/edges/GraphEdge.tsx`         | TSX source | **Missing** | Phase 3, step 10 | Port-labeled XYFlow edge             |
| `src/panels/DetailPanel.tsx`      | TSX source | **Missing** | Phase 3, step 12 | Node inspector                       |
| `src/panels/FilterBar.tsx`        | TSX source | **Missing** | Phase 3, step 13 | Kind + Stratum dropdown filters      |
| `src/panels/EditPayloadPanel.tsx` | TSX source | **Missing** | Phase 4, step 16 | Inline JSON payload editor           |
| `src/dialogs/AddNodeDialog.tsx`   | TSX source | **Missing** | Phase 4, step 14 | ADD morphism form                    |
| `src/dialogs/HydrateDialog.tsx`   | TSX source | **Missing** | Phase 4, step 18 | MaterializeRequest import            |
| `src/handlers/onConnect.ts`       | TS source  | **Missing** | Phase 4, step 15 | XYFlow `onConnect` → LINK            |

---

### Backend Endpoints (to add)

| Item                                                | Category   | Status      | Required By         | Notes                         |
| --------------------------------------------------- | ---------- | ----------- | ------------------- | ----------------------------- |
| `GET /state/scope/:actor`                           | HTTP route | **Missing** | Phase 1, step 5     | Scoped subcategory projection |
| `GET /state/nodes?kind=HyperEdge&participant={urn}` | HTTP route | **Missing** | Hypergraph approach | Incidence query               |

---

### Ontology / Registry Additions

| Item                                         | Category       | Status      | Required By    | Notes                         |
| -------------------------------------------- | -------------- | ----------- | -------------- | ----------------------------- |
| `Kind=Kernel` (OBJ14)                        | Ontology entry | **Missing** | Phase 0, F1    | Kernel node type unregistered |
| `Kind=Feature` (OBJ15) or `SystemCapability` | Ontology entry | **Missing** | Phase 0, F1    | Feature nodes unregistered    |
| `Kind=HyperEdge`                             | Ontology entry | **Missing** | Hypergraph D+C | First-class relationship node |
| `MOR17 exposes/binding`                      | Morphism type  | **Missing** | Phase 0, F2    | Kernel → ProtocolAdapter port |
| `MOR18 persists/store`                       | Morphism type  | **Missing** | F3 (Wave 1)    | Kernel → InfraService port    |

---

### Seed Graph Corrections

| Item                                   | Category      | Status      | Required By      | Notes                                |
| -------------------------------------- | ------------- | ----------- | ---------------- | ------------------------------------ |
| `ADD urn:moos:kernel:self`             | Seed morphism | **Missing** | Phase 0, F4      | Actor node must exist before signing |
| Reseed `http-api` as `ProtocolAdapter` | Seed morphism | **Missing** | Phase 0, F2      | Wrong Kind in current seed           |
| `ADD urn:moos:agent:primary`           | Seed morphism | **Missing** | Phase 5, step 19 | Agent as graph node                  |

---

### Infrastructure / Containerization

| Item                | Category      | Status      | Required By                   | Notes                      |
| ------------------- | ------------- | ----------- | ----------------------------- | -------------------------- |
| Dockerfile (kernel) | Container     | **Missing** | Production deploy             | No container config exists |
| docker-compose.yml  | Orchestration | **Missing** | Dev environment with Postgres | Optional convenience       |

---

### Documentation Corrections

| Item                           | Category       | Status      | Required By | Notes                                  |
| ------------------------------ | -------------- | ----------- | ----------- | -------------------------------------- |
| Fix "kernel IS a catamorphism" | Doc correction | **Missing** | F5          | Should say "implements a catamorphism" |
| Pin protocol definition        | Doc correction | **Missing** | F6          | Under-specified in CLAUDE.md           |

---

## Summary Counts

| Category               | Have | Missing | Total |
| ---------------------- | ---- | ------- | ----- |
| Languages / Runtimes   | 2    | 2       | 4     |
| Go dependencies        | 2    | 0       | 2     |
| Go source files (new)  | 0    | 2       | 2     |
| JS/TS dependencies     | 0    | 10      | 10    |
| Chrome Extension files | 0    | 16      | 16    |
| Backend endpoints      | 17+  | 2       | 19+   |
| Ontology entries       | 35   | 3       | 38    |
| Morphism types         | 16   | 2       | 18    |
| Seed corrections       | 0    | 3       | 3     |
| Infrastructure         | 0    | 2       | 2     |
| Doc fixes              | 0    | 2       | 2     |

---

## Bottom Line

The Go kernel is complete and self-contained with minimal deps (just `pgx`). The entire Chrome Extension surface (Phase 2–6) is greenfield — 2 new runtimes, 10 JS packages, 16 source files. Phase 0 foundation fixes need 3 ontology entries + 2 morphism types + 3 seed corrections before anything else proceeds.

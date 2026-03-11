# Plan: Collider Chrome Sidepanel — Categorical Graph Editor

## TL;DR

Build a **Chrome Extension sidepanel** that projects a user's scoped subgraph of the Collider hypergraph and allows full graph editing (ADD/LINK/MUTATE/UNLINK) via the moos kernel HTTP API. Canvas uses **React + XYFlow**. Access is topology-scoped (OWNS chains). Agent write-lens is symmetric to UI but pushes morphisms. Everything except the Go loop is an object/morphism in some category.

---

## Phase 0 — Foundation Fixes (blocks all else)

1. **Register Kind=Kernel and Kind=Feature** in `ontology.json` — add OBJ14/OBJ15 (or map to existing kinds). Without this, the kernel's own seed nodes violate registry constraints. *(Finding F1)*
   - File: `.agent/knowledge_base/superset/ontology.json`
   - Also update `registry_loader.go` if derivation logic needs adjustment

2. **Reseed http-api as ProtocolAdapter** — change `urn:moos:feature:http-api` from Kind=Feature to Kind=ProtocolAdapter (OBJ11) with `exposes→binding` ports. *(Finding F2)*
   - File: `platform/kernel/cmd/kernel/main.go` (`seedKernel()`)

3. **ADD actor node for urn:moos:kernel:self** — the kernel actor must exist as a node before it issues morphisms. First morphism in `seedKernel()` should be ADD of the actor. *(Finding F4)*
   - File: `platform/kernel/cmd/kernel/main.go`

4. **Verify User kind (OBJ01) is seedable** — `deriveRegistryFromOntology` must create a KindSpec for User so user nodes can be ADDed from the sidepanel.
   - File: `platform/kernel/internal/shell/registry_loader.go`

**Verification:** `go test ./...` passes. Kernel boots, self-seeds, `GET /state` shows actor node + corrected kinds.

---

## Phase 1 — Scoped Projection API (backend) *parallel with Phase 2*

5. **New endpoint: `GET /state/scope/:actor`** — returns the full subcategory reachable from an actor URN via OWNS traversal (BFS on `owns→child` wires). Given actor a, compute Slice(a) ⊆ C. *(depends on step 3)*
   - File: `platform/kernel/internal/httpapi/server.go` (new handler)
   - File: `platform/kernel/internal/shell/runtime.go` (new `ScopedSubgraph(urn)` method)
   - **Mock first:** return full graph (no filtering) so frontend develops in parallel

6. **Pure traversal helper** — `ReachableNodes(state, urn, portFilter) → set[URN]` + `InducedSubgraph(state, nodeSet) → GraphState`. Pure in `internal/core`, locked wrapper in `internal/shell`. *(parallel with step 5)*
   - File: `platform/kernel/internal/core/traversal.go` (new, pure)
   - File: `platform/kernel/internal/shell/runtime.go` (locked wrapper)

**Verification:** `curl /state/scope/urn:moos:kernel:self` returns kernel + 6 features + wires. Create user, OWNS children, verify scope returns only owned subgraph.

---

## Phase 2 — Chrome Extension Shell *parallel with Phase 1*

7. **Manifest V3 Chrome Extension** with sidepanel API — minimal shell that opens a React app in sidepanel.
   - New dir: `platform/chrome-extension/`
   - Files: `manifest.json`, `sidepanel.html`, `background.js`
   - Config: kernel URL in `chrome.storage.local` (default `http://localhost:8000`)

8. **React app scaffold** — Vite + React + TypeScript + XYFlow. Connects to kernel, fetches `/state/scope/:actor`, renders empty canvas. *(depends on step 7)*
   - New dir: `platform/chrome-extension/src/`
   - Key: `App.tsx`, `api/kernel.ts`, `store/graphStore.ts` (Zustand)
   - Dep: `@xyflow/react` v12+

**Verification:** Load unpacked extension → sidepanel opens → fetches kernel → console shows graph JSON.

---

## Phase 3 — XYFlow Graph Canvas (read projection) *depends on Phase 2*

9. **Kind → XYFlow custom node types** — 13 ontology Kinds → visual node components. Show Kind badge, short URN, stratum color (S2=teal, S3=blue, S4=orange).
   - File: `src/nodes/GraphNode.tsx` (generic, Kind-driven styling)

10. **Wire → XYFlow edges with port handles** — edges show source_port→target_port labels. Handles from KindSpec port definitions. *(parallel with step 9)*
    - File: `src/edges/GraphEdge.tsx`

11. **Auto-layout** — `@dagrejs/dagre` or `elkjs`. Manual drag also works (XYFlow stores positions). *(depends on 9-10)*

12. **Detail panel** — click node → Identity, Payload, Outgoing, Incoming. *(parallel with 11)*
    - File: `src/panels/DetailPanel.tsx`

13. **Registry-driven filters** — Kind + Stratum dropdowns from `GET /semantics/registry`. *(parallel with 11)*
    - File: `src/panels/FilterBar.tsx`

**Verification:** Sidepanel shows kernel graph as XYFlow nodes + edges. Colored by stratum. Click → detail. Filter works.

---

## Phase 4 — Write Morphisms from UI (graph editor) *depends on Phase 3*

14. **ADD: "New Node" dialog** — Kind selector (from registry), URN input, Stratum (default S2), payload JSON editor. Posts `POST /morphisms`.
    - File: `src/dialogs/AddNodeDialog.tsx`

15. **LINK: drag edge between ports** — XYFlow `onConnect`. Source handle = source_port, target handle = target_port. Posts LINK envelope. *(parallel with 14)*

16. **MUTATE: inline payload edit** — double-click node → editable JSON. Save → MUTATE with version CAS. *(parallel with 14)*

17. **UNLINK: edge context menu → delete** — right-click edge → UNLINK. *(parallel with 14)*

18. **Hydration shortcut** — "Import subgraph" button accepts MaterializeRequest JSON. Posts `POST /hydration/materialize`. *(parallel with 14)*

**Verification:** From sidepanel: ADD User node, LINK via OWNS, MUTATE payload, UNLINK wire. Verify via `GET /state`. Refresh → graph updates.

---

## Phase 5 — Agent Write-Lens (mock) *depends on Phase 0*

19. **Agent as graph node** — ADD `urn:moos:agent:primary` Kind=SystemTool (OBJ07) S2. LINK to kernel via `can_schedule→wl`. Agent IS a node in graph it mutates.
    - File: `platform/kernel/cmd/kernel/main.go` (add to seedKernel)

20. **Agent loop stub** — polls `GET /state`, applies hardcoded rules (e.g. "orphan node → create OWNS wire"). Posts `POST /programs`. **Mock: no LLM, rule-based only.**
    - File: `platform/kernel/cmd/kernel/main.go` (goroutine) or `cmd/agent/main.go`

21. **Model-as-function placeholder** — Kind=AgnosticModel (OBJ06) node. Agent "calls" by MUTATE with request, reads response. Mock: echo.

**Verification:** Kernel + agent stub boots. Agent auto-creates OWNS wires. Visible in sidepanel live.

---

## Phase 6 — Topology-Based Access *depends on Phase 1 step 6*

22. **Real OWNS traversal on `/state/scope/:actor`** — replace mock with BFS. Only reachable nodes returned.

23. **Group membership** — LINK User→Group via `member_of→group`. Group OWNS subgraph. User scope = own OWNS ∪ group OWNS.

24. **Actor identity in sidepanel** — extension stores actor URN in `chrome.storage.local`. All writes use it as `envelope.Actor`. Scope uses it for filtering.

**Verification:** User A (owns X), User B (owns Y). Sidepanel as A → sees X. Switch → sees Y. A joins Group G → sees X ∪ G's subgraph.

---

## Relevant Files

**Modify:**
- `.agent/knowledge_base/superset/ontology.json` — register Kernel, Feature kinds
- `platform/kernel/cmd/kernel/main.go` — fix seedKernel: actor node, ProtocolAdapter, agent seed
- `platform/kernel/internal/httpapi/server.go` — add `/state/scope/:actor`
- `platform/kernel/internal/shell/runtime.go` — add ScopedSubgraph(), ReachableNodes()
- `platform/kernel/internal/shell/registry_loader.go` — verify Kind derivation

**Create:**
- `platform/kernel/internal/core/traversal.go` — pure BFS/DFS traversal
- `platform/chrome-extension/` — entire Chrome Extension
  - `manifest.json`, `sidepanel.html`, `background.js`
  - `src/App.tsx`, `src/api/kernel.ts`, `src/store/graphStore.ts`, `src/store/identity.ts`
  - `src/nodes/GraphNode.tsx`, `src/edges/GraphEdge.tsx`
  - `src/panels/DetailPanel.tsx`, `src/panels/FilterBar.tsx`, `src/panels/EditPayloadPanel.tsx`
  - `src/dialogs/AddNodeDialog.tsx`, `src/dialogs/HydrateDialog.tsx`
  - `src/handlers/onConnect.ts`
- `platform/kernel/cmd/agent/main.go` — agent write-lens stub

---

## Verification (end-to-end)

1. `go test ./...` — all kernel tests pass after Phase 0
2. Kernel boots → `GET /state` shows corrected self-seed (actor node, ProtocolAdapter, registered Kinds)
3. Chrome Extension loads unpacked → sidepanel → XYFlow renders kernel subgraph
4. From sidepanel: ADD, LINK, MUTATE, UNLINK → all persist
5. Agent stub → auto-generates morphisms → visible in sidepanel
6. Scope test: two users see only their own subgraphs

---

## Decisions

- **Canvas: XYFlow (React Flow v12+)** — port-based editing, matches FUN02 spec, largest ecosystem
- **State: Zustand** — lightweight, pairs well with XYFlow
- **Build: Vite** — fast HMR for extension dev
- **Agent: goroutine in main (MVP)** — extract to separate binary later
- **No auth in MVP** — actor URN is self-declared. Real auth = Wave 2+
- **No "application" concept** — user's graph IS their workspace. Nodes ARE programs. Categories define what's possible.
- **Scope**: Extension + kernel fixes + scoped projection + write UI + agent stub
- **Excluded**: real LLM dispatch, S0→S1 validation, embedding functor, federation (MOR12), benchmark functor

# Contract-First Skills Runtime Alignment: Migration Plan

This document outlines the detailed, phased execution plan for aligning the Collider ecosystem's runtime contracts, ensuring stable integration of the new skills architecture before expanding runtime adapters (e.g., PI).

**Core Strategy:** Treat `collider-skills-runtime-integration.md` as the canonical target. Execute in backward-compatible phases across AgentRunner, DataServer, GraphToolServer, and NanoClawBridge.

---

## Phase 0: Contract Reality Lock

**Objective:** Resolve ownership, path, and transport ambiguities before implementation begins.

### 0.1 Canonical Ownership Decisions

- **Canonical context-delta transport:** gRPC `SubscribeContextDeltas`.
- **Canonical proto source-of-truth:** `workspaces/FFS1_ColliderDataSystems/FFS2_ColliderBackends_MultiAgentChromeExtension/proto/collider_graph.proto`.
- **Runtime session manager ownership:** `NanoClawBridge/src/session-manager.ts`.

### 0.2 Plan Path/Symbol Validation

- **Action:** Validate that every target in this plan maps to an existing file/symbol and a single owning service.
- **Action:** Remove/replace ambiguous targets (`session_manager.py`, generic `api.ts`) with concrete owners (`context-client.ts`, bridge/runtime-specific modules).

### 🛠️ Assess / Test / Eval (Phase 0)

1. **Ownership Matrix:** Produce a short matrix for each contract boundary: owner service, endpoint/proto, primary file, compatibility consumer.
2. **Path Integrity:** Verify every listed target path exists in the repo.

### ✅ Exit Criteria (Phase 0)

- Every target in this plan maps to a real file/symbol and single owner.
- Canonical delta transport and proto ownership are documented and accepted.

---

## Phase 1: Contract Freezing & Active Path Alignment

**Objective:** Lock down the canonical contracts in documentation and fix immediate drift in the active execution paths without changing underlying business logic.

### 1.1 Documentation Freeze

- **Target:** `D:\FFS0_Factory\.agent\knowledge\architecture\collider-skills-runtime-integration.md`
- **Action:** Explicitly define the definitive `discover-tools` payload shape, `context-delta` transport definitions (SSE vs WS routing), and execution port policies (resolving the AgentRunner vs GraphTool port default mismatch).

### 1.2 Align Active Graph/Registry Paths (Backend)

- **Targets:** `graph_tool_client.py`, `registry_api.py`, `execution.py`
- **Action:** Modify the Python clients and registry endpoints in `ColliderGraphToolServer` and `ColliderAgentRunner` to strictly adhere to the frozen contracts. Address the vector discovery parsing bug currently blocking clean execution.

### 1.3 Align Active WS/Event Frame Compatibility (Bridge ↔ FFS4)

- **Targets:** `NanoClawBridge/src/ws-bridge.ts`, `FFS3.../apps/ffs4/src/lib/nanoclaw-client.ts`
- **Action:** Normalize event frame compatibility so bridge-emitted frames are consumed without protocol translation drift in FFS4.

### 1.4 Align Active Subscriber Paths (Bridge)

- **Targets:** `context-subscriber.ts`
- **Action:** Ensure NanoClawBridge subscriber pathing and parsing aligns with canonical delta transport/compatibility behavior.

### 🛠️ Assess / Test / Eval (Phase 1)

1. **Start Infrastructure:** Use the workflow defined in `D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\.agent\workflows\dev-start.md` to spin up the DataServer (:8000), GraphToolServer (:8001), and AgentRunner (:8004).
2. **Programmatic Test:** Utilize the `api_client.py` skill (found in `FFS2.../.agent/skills/api_client.py`) to hit the tool registry endpoints.
3. **Contract Tests:** Run golden contract tests for discovery payload shape, execution endpoint reachability, context-delta route behavior, and WS frame compatibility.

### ✅ Exit Criteria (Phase 1)

- Discovery response shape is parsed successfully end-to-end.
- Execution endpoint prefix/port is reachable from bridge path.
- Context-delta route behavior matches documented contract.
- FFS4 receives and processes bridge event frames for text/tool/end events without ad hoc translation.

---

## Phase 2: Runtime Boundary Extraction (Anthropic Baseline Preserved)

**Objective:** Introduce a runtime adapter boundary without changing current baseline behavior.

### 2.1 Introduce `IAgentSession` in Bridge Runtime Layer

- **Targets:** `NanoClawBridge/src/session-manager.ts`, `NanoClawBridge/src/sdk/anthropic-agent.ts`
- **Action:** Abstract the current Anthropic execution loop behind `IAgentSession` while preserving Anthropic as the default active adapter.

### 2.2 Bind Real Context Identity in SDK Mode

- **Targets:** `NanoClawBridge/src/session-manager.ts`, `NanoClawBridge/src/grpc/context-client.ts`
- **Action:** Ensure bootstrap context calls carry real `nodeIds`/`appId` identity instead of placeholders.

### 🛠️ Assess / Test / Eval (Phase 2)

1. **Session Smoke Test:** POST ContextSet session to `http://localhost:8004/agent/session`.
2. **Behavior Parity:** Confirm Anthropic baseline output/event behavior is unchanged.

### ✅ Exit Criteria (Phase 2)

- `IAgentSession` boundary is merged and Anthropic remains default.
- SDK mode obtains non-empty bootstrap context from real identity inputs.

---

## Phase 3: Schema Normalization & Deterministic Ranking

**Objective:** Make Pydantic models contract-safe and implement the new namespace/version-aware skill resolution logic.

### 3.1 Schema Safety & Metadata

- **Targets:** `ColliderDataServer/src/schemas/nodes.py`, `ColliderDataServer/src/schemas/agent_bootstrap.py`, `ColliderGraphToolServer/src/schemas/registry.py`.
- **Action:** Replace all generic mutable literal defaults with `Field(default_factory=...)`. Add graph-aware fields (`namespace`, `version`, `scope`, `source_node_path`) to the `SkillDefinition` and `ToolDefinition` schemas.

### 3.2 Skill Merge & Ranking Implementation

- **Targets:** `runner.py` (AgentRunner) and `prompt-builder.ts` (NanoClawBridge).
- **Action:** Implement deterministic namespace/version collision merging. Create the logic to rank and select the top-N skills based strictly on dynamically allocated token budgets.

### 🛠️ Assess / Test / Eval (Phase 3)

1. **DB Sync Test:** Run the seeder tool from the root:
   ```bash
   uv run python -m sdk.seeder.cli --root D:/FFS0_Factory --app-id c57ab23a-4a57-4b28-a34c-9700320565ea
   ```
2. **Evaluation:** Check the SQLite Viewer (`sqlite_web collider.db` on :8003). Verify that the `NodeContainer` objects correctly hydrated the new `namespace` and `version` metadata fields without throwing schema validation errors.

### ✅ Exit Criteria (Phase 3)

- No mutable-literal defaults remain in targeted schemas.
- Namespace/version-aware merge is active and deterministic.
- Ranking injects capped top-N full skills (max 3) with token-budget observability.

---

## Phase 4: Protocol Extension & Compatibility Rollout

**Objective:** Safely extend the gRPC/RPC protocols to carry the new context and prepare the architecture for the PI runtime adapter.

### 4.1 Extend Protobufs & Serializers

- **Targets:** `proto/collider_graph.proto` (canonical), `context_service.py`, `context-client.ts`
- **Action:** Add new metadata fields to `.proto`, regenerate Python/TS artifacts from the canonical proto only, and maintain backward compatibility on outer session/WS APIs.

### 4.2 Compatibility Assurance

- **Action:** Validate dual-read compatibility for old/new optional fields across producers and consumers.

### 🛠️ Assess / Test / Eval (Phase 4)

1. **Proto Compilation:** Run the proto generation scripts and verify no build breaks occur in the Python or TypeScript workspaces.
2. **Unit Tests:** Run targeted tests for context serialization and shared UI/API libs:
   ```bash
   pnpm nx test shared-ui
   ```
3. **Compatibility Tests:** Validate old/new optional fields for context payloads in integration tests.

### ✅ Exit Criteria (Phase 4)

- Python and TS consumers are regenerated from one canonical proto.
- Old/new optional field compatibility tests pass.
- Session/WS outer contract remains stable.

---

## Phase 5: PI Shadow Validation & Governance Closure

**Objective:** Validate PI adapter parity in shadow mode and clean up architectural documentation drift.

### 5.1 UI & Extension E2E Testing

- **Action:** Test full boot-to-chat loop with Anthropic baseline and PI shadow side-by-side; avoid reliance on legacy filesystem context delivery.
- **Tools:** Use the Chrome Extension Sidepanel (WorkspaceBrowser) and the FFS6 IDE viewer.

### 5.2 Close Governance Drift

- **Targets:** `_index.md` files across `.agent` directories (Root, FFS1, FFS2, FFS3).
- **Action:** Remove obsolete structural references. Point developers cleanly to `collider-skills-runtime-integration.md` as canonical implementation spec.

### 🛠️ Assess / Test / Eval (Phase 5)

1. **Launch IDE Viewer:**
   ```bash
   pnpm nx serve ffs6
   ```
2. **UI Verification:** Select a node in the UI. Open the ContextSet chat window. Verify that the system prompt correctly ingested the deterministic top-N skills (visually inspecting the prompt debug payload if available) and that streaming text/tools work smoothly via the WebSocket.
3. **Parity Verification:** Run Anthropic vs PI shadow parity checks for text/tool/error/message_end event classes.
4. **Evaluation Sign-off:** FFS4 sidepanel extension communicates cleanly with RootAgent via FFS2 backends and rollback switch is tested.

### ✅ Exit Criteria (Phase 5)

- PI shadow parity passes against Anthropic baseline for required event classes.
- FFS4/FFS6 E2E boot-to-chat path remains stable.
- `.agent` governance/index drift is closed.

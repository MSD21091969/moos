# Collider Skills + Runtime Integration Draft

Version: v1.0.0-draft  
Date: 2026-02-23

## 1) Executive Summary

Collider should treat the recursive `NodeContainer` graph as the core execution ontology (the "engine") and treat skills as a thin, dynamic interface/state projection (the "harness surface").

### Chosen direction (validated)

- Runtime strategy: **C-first (PI runtime behind interface)**
- Skill source of truth: **DB canonical** (filesystem `.agent` as authoring/seed source)
- Skill precedence: **namespace + version aware** (not name-only leaf-wins)
- MCP scope now: **tools-only** (defer prompts/resources to later phase)

This preserves existing behavior, reduces vendor lock-in, and keeps blast radius controlled while enabling a scalable path for model/runtime flexibility.

---

## 2) Architecture Reality Snapshot (Current Code)

### Session + context flow

- Session creation lives in AgentRunner REST and root-session API.
- Context composition (including merge logic and optional vector augmentation) lives in AgentRunner.
- Bootstrap delivery exists in REST and gRPC modes.
- WebSocket bridge is active in NanoClawBridge and consumed by extension/frontends.

### Tool execution flow

`NanoClawBridge ToolExecutor -> DataServer execution endpoint -> GraphToolServer registry execution -> ToolRunner importlib`

### Core schema anchors

- Recursive container model: `NodeContainer` + `NodeKind`
- Skill model: `SkillDefinition`
- Application model: app and permission models in DataServer
- SDK mirror types: NanoClawBridge `types.ts`

### Existing interoperability

- MCP server is production-shaped for **tools**.
- Prompts/resources MCP primitives are **not yet implemented** in GraphToolServer.

---

## 3) Gaps / Contradictions Blocking “Done” State

1. **Vector discovery contract mismatch**
   - AgentRunner parser expects a different shape than GraphToolServer currently returns.
   - Impact: semantic tool discovery can silently degrade.

2. **Context delta route mismatch**
   - NanoClaw subscriber expects stream path/shape that does not cleanly match current DataServer route reality.
   - Impact: mid-session context updates are fragile or non-functional.

3. **Execution configuration drift**
   - Inconsistent service defaults / references in execution path.
   - Impact: hidden runtime failures under mixed deployments.

4. **Schema strictness debt**
   - Multiple mutable defaults in Pydantic models (`[]`, `{}` literals).
   - Impact: weak long-term contract safety and codegen parity risk.

5. **Runtime coupling debt**
   - Anthropic-specific message/tool loop assumptions are embedded deeply in session runtime.
   - Impact: PI adoption is harder without interface seams.

---

## 4) Option Comparison (A / B / C)

## Option A — Anthropic SDK + gRPC hardening

- Pros:
  - Closest to running code now
  - Lowest immediate disruption
- Cons:
  - Strong vendor coupling
  - Preserves shape drift unless contracts are formalized

## Option B — Native MCP skills/context (prompts/resources)

- Pros:
  - Highest interoperability
  - Protocol-native skills/resources model
- Cons:
  - Highest blast radius now
  - Requires substantial MCP server/client expansion

## Option C — PI runtime behind interface (chosen)

- Pros:
  - Lowest model/vendor lock-in
  - Aligns with harness-first strategy and your recursive graph intuition
  - Enables side-by-side runtime validation with shadow mode
- Cons:
  - Requires careful event-parity and adapter engineering

### Decision

Use **C as target runtime**, but **stabilize A contracts first** (event schema, composition schema, execution schema), then plug PI adapter behind the same session interface.

---

## 5) Skills Source-of-Truth and Governance Model

## Principle

Skills are not the graph; they are a **runtime view** of graph state and procedures.

## Three-layer SoT

1. **Authoring SoT (human)**: `.agent` files (skills/instructions/rules/docs)
2. **Canonical SoT (system)**: DB `NodeContainer.skills[]` and container graph
3. **Delivery SoT (runtime)**: computed `ContainerSkillView` per session/team

## Governance rules

- Filesystem edits require explicit seed sync into DB.
- DB remains canonical at runtime.
- Composition uses deterministic precedence policy:
  - namespace
  - semantic version
  - scope (session/local/ancestor/global)
  - tie-break by node depth / leaf proximity
- Preserve a global meta-skill (`collider-workspace`) as inherited navigation capability.

---

## 6) Container Model Clarification (Your DNA Hypothesis)

Your hypothesis is directionally correct and should be formalized:

- **Tools are executable container leaves**
- **Workflows are orchestrated tool graphs**
- **Applications are top-level orchestration containers over the same primitives**

So the design should enforce:

- one recursive container schema,
- one composition algorithm,
- multiple runtime projections (skills view, tool schemas view, workflow view),
- no duplicated semantic truths across file and DB planes.

In short: **Graph is truth, skills are interface, runtime is pluggable.**

---

## 7) Pydantic and Contract Recommendations

1. Replace mutable literals with `Field(default_factory=...)` everywhere in schema models.
2. Extend `SkillDefinition` to include (backward compatible):
   - `namespace`, `version`, `scope`, `source_node_id`, `source_node_path`
   - `depends_on`, `inputs`, `outputs`, `exposes_tools`
   - optional `compatibility`, `allowed_tools`, `metadata`, `license`
3. Add `ContainerSkillView` as computed runtime schema (not persisted canonical data).
4. Mirror contract in:
   - DataServer Pydantic
   - AgentRunner schemas + gRPC proto
   - NanoClawBridge TypeScript types

---

## 8) Runtime Abstraction Blueprint

Define a runtime-agnostic interface in NanoClawBridge:

- `createSession(context, model, config)`
- `sendMessage(sessionId, message)` -> async event stream
- `injectContext(sessionId, delta)`
- `terminateSession(sessionId)`

Implementations:

- `AnthropicSessionAdapter` (current behavior)
- `PISessionAdapter` (new)

Session manager chooses adapter by runtime flag (`anthropic`, `pi`, `pi-shadow`) while preserving the same WS event contract.

---

## 9) MCP Positioning (Now vs Later)

## Now (selected)

- Keep MCP as tools-only interoperability surface.
- Keep skills/context delivery in gRPC/JSON runtime path.

## Later (optional upgrade)

- Add MCP prompts/resources for skills/topology to support full protocol-native context pull.
- Do this only after runtime contracts are stable and tested.

---

## 10) External Standards / Context7 Validation Notes

The plan is aligned with:

- **Agent Skills spec**: requires strong frontmatter semantics (`name`, `description`), optional compatibility/metadata/allowed-tools fields.
- **Anthropic TS SDK**: supports robust streaming + tool-loop orchestration suitable for current adapter baseline.
- **MCP spec**: tools/prompts/resources are first-class; tools-only is a valid staged subset.
- **PI architecture**: provider-agnostic runtime + event-loop/extension style aligns with pluggable harness strategy.

---

## 11) Implementation File Map (High-value touchpoints)

### Runtime / bridge

- `workspaces/FFS1_ColliderDataSystems/FFS2_ColliderBackends_MultiAgentChromeExtension/NanoClawBridge/src/session-manager.ts`
- `workspaces/FFS1_ColliderDataSystems/FFS2_ColliderBackends_MultiAgentChromeExtension/NanoClawBridge/src/sdk/anthropic-agent.ts`
- `workspaces/FFS1_ColliderDataSystems/FFS2_ColliderBackends_MultiAgentChromeExtension/NanoClawBridge/src/sdk/tool-executor.ts`
- `workspaces/FFS1_ColliderDataSystems/FFS2_ColliderBackends_MultiAgentChromeExtension/NanoClawBridge/src/ws-bridge.ts`

### Composition / contracts

- `workspaces/FFS1_ColliderDataSystems/FFS2_ColliderBackends_MultiAgentChromeExtension/ColliderAgentRunner/src/agent/runner.py`
- `workspaces/FFS1_ColliderDataSystems/FFS2_ColliderBackends_MultiAgentChromeExtension/ColliderAgentRunner/src/grpc/context_service.py`
- `workspaces/FFS1_ColliderDataSystems/FFS2_ColliderBackends_MultiAgentChromeExtension/proto/collider_graph.proto`

### Schema / bootstrap

- `workspaces/FFS1_ColliderDataSystems/FFS2_ColliderBackends_MultiAgentChromeExtension/ColliderDataServer/src/schemas/nodes.py`
- `workspaces/FFS1_ColliderDataSystems/FFS2_ColliderBackends_MultiAgentChromeExtension/ColliderDataServer/src/core/agent_bootstrap.py`
- `workspaces/FFS1_ColliderDataSystems/FFS2_ColliderBackends_MultiAgentChromeExtension/ColliderDataServer/src/api/execution.py`

### MCP and registry

- `workspaces/FFS1_ColliderDataSystems/FFS2_ColliderBackends_MultiAgentChromeExtension/ColliderGraphToolServer/src/handlers/mcp_handler.py`
- `workspaces/FFS1_ColliderDataSystems/FFS2_ColliderBackends_MultiAgentChromeExtension/ColliderGraphToolServer/src/handlers/registry_api.py`

### Seeder pipeline

- `sdk/seeder/agent_walker.py`
- `sdk/seeder/node_upserter.py`

---

## 12) Open Decisions (Still Needed)

1. Do you want one-way `.agent` -> DB sync only, or optional bidirectional sync mode?
2. Should root/global skills be overrideable by descendants, or protected by policy flags?
3. Do we require strict skills spec validation at ingestion time (recommended), or permissive ingest + warning mode?
4. Is `pi-shadow` mandatory before switching any production sessions to PI runtime? (recommended yes)

---

## 13) Final Position

Collider should standardize on:

- **Recursive graph/container truth** as the stable core,
- **skills as a computed projection** for agent usability and team coordination,
- **runtime adapters** (Anthropic now, PI next) behind one stable event/interface contract,
- **deterministic skill governance** with namespace/version-aware composition.

This gives you the scalability you’re aiming for: graph-first logic, OOP-like container semantics, dataflow-friendly orchestration, and runtime independence.

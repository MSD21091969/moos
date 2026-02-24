# Contract-First Skills Runtime Alignment

This plan addresses the integration of the new agent skills runtime, prioritizing contract stabilization and backward compatibility before expanding runtime abstractions (e.g., PI adapter). It treats `collider-skills-runtime-integration.md` as the canonical target, viewing the draft and other docs as rationale/migration guidance.

## User Review Required

> [!IMPORTANT]
> Please review this implementation plan. It is a direct formalization of your 7-step strategy. Let me know if any specific files or paths need to be adjusted before we move to EXECUTION.

## Proposed Changes

### 1. Freeze Canonical Contracts

Update architecture docs to formalize contracts and resolve drift.

- **MODIFY** `[collider-skills-runtime-integration.md](file:///D:/FFS0_Factory/.agent/knowledge/architecture/collider-skills-runtime-integration.md)`: Freeze discover-tools payload, context-delta transport, execution endpoint/port, and runtime-flag policy.

### 2. Align Active Path Contracts

Fix mismatches in the current execution paths across the repos.

- **MODIFY** `graph_tool_client.py`
- **MODIFY** `registry_api.py`
- **MODIFY** `context-subscriber.ts`
- **MODIFY** `execution.py`

### 3. Normalize Schema Safety & Metadata

Implement schema safety (e.g., standardizing `default_factory`) and update skill metadata fields.

- **MODIFY** `nodes.py`
- **MODIFY** `agent_bootstrap.py`
- **MODIFY** `registry.py`

### 4. Implement Skill Merge & Ranking

Introduce deterministic namespace/version skill merging and budget-aware top-N ranking.

- **MODIFY** `runner.py`
- **MODIFY** `prompt-builder.ts`

### 5. Extend Protocol Shape & Serializers

Update gRPC definitions and serializers while maintaining session API backward compatibility.

- **MODIFY** `collider_graph.proto`
- **MODIFY** `context_service.py`
- **MODIFY** `api.ts`

### 6. Introduce Runtime Adapter Boundary

Set up `IAgentSession` interface, preserve the Anthropic baseline, and prepare PI adapter in shadow mode.

- **MODIFY** `session-manager.ts` (and underlying Python session managers in AgentRunner)

### 7. Close Governance Drift

Update index files to reflect the real architecture artifacts, improving discoverability.

- **MODIFY** Architecture `_index.md` files in FFS1 to remove obsolete references and list current canonical docs.

## Verification Plan

### Automated Tests

- Contract tests for discover payload and delta channels across AgentRunner, DataServer, GraphToolServer, and NanoClawBridge.
- Proto compatibility checks post-generation.

### Manual Verification

- End-to-end session bootstrap and chat smoke tests via FFS4 (Sidepanel) and extension panels.
- Verify session/WebSocket response shapes remain unchanged internally for the frontend consumers.

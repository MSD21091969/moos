# Test Strategy — Collider SDK + gRPC Integration

## Test Suites Created

### 1. AgentRunner gRPC Context Service (Python)

**File:** `ColliderAgentRunner/tests/grpc/test_context_service.py`
**Run:** `cd ColliderAgentRunner && uv run pytest tests/grpc/ -v`

Covers:
- `_skill_to_chunk()` — SkillDefinition dict → SkillChunk protobuf conversion
- `_tool_schema_to_chunk()` — Tool schema dict → ToolSchemaChunk conversion
- `_session_meta_to_chunk()` — Session meta dict → SessionMetaChunk conversion
- `GetBootstrap` RPC — returns well-formed BootstrapResponse with all fields
- `StreamContext` RPC — yields correct chunk count, sequential sequence numbers, skips empty sections
- Error handling — composition failures abort with INTERNAL status

### 2. NanoClawBridge SDK (TypeScript)

**File:** `NanoClawBridge/test/sdk/sdk.test.ts`
**Run:** `cd NanoClawBridge && npx vitest run`

Covers:
- `buildSystemPrompt()` — includes all context sections, skills, session meta; handles empty context
- `applyDeltaToContext()` — skill add/update/remove, system prompt delta, full replace, immutability
- `ToolExecutor` — schema storage, Anthropic-compatible tool generation, execution routing
- `ComposedContext` shape validation — all required fields, SkillDefinition shape, ToolSchema shape

---

## Recommended Additional Tests for Next Session

### Priority 1: Integration Tests (Start Here)

#### A. End-to-End Context Pipeline

Test the full flow: ContextSet → compose → gRPC stream → SDK session creation.

```python
# ColliderAgentRunner/tests/integration/test_context_pipeline.py
# Requires: DataServer running at :8000 with seeded test data

async def test_full_context_pipeline():
    """POST /agent/session → compose → gRPC GetBootstrap → verify all fields present."""

async def test_grpc_stream_delivers_all_chunks():
    """gRPC StreamContext → count chunks → verify types match composed context."""

async def test_context_delta_updates_session():
    """Modify a node → SSE delta fires → agent session prompt is updated."""
```

#### B. NanoClawBridge Session Lifecycle

```typescript
// NanoClawBridge/test/integration/session-lifecycle.test.ts
// Requires: AgentRunner gRPC server running at :50051

describe("SDK session lifecycle", () => {
  it("creates session from gRPC bootstrap");
  it("sends message and receives streaming events");
  it("injects context delta mid-session");
  it("terminates and cleans up resources");
});
```

#### C. Agent Teams

```typescript
// NanoClawBridge/test/sdk/team-manager.test.ts

describe("TeamManager", () => {
  it("creates team with leader + N members from N+1 nodes");
  it("leader and members have different context");
  it("sendTask routes to leader session");
  it("sendToMember routes to specific member");
  it("mailbox stores and retrieves messages");
  it("dissolveTeam cleans up all sessions");
});
```

### Priority 2: Contract Tests

#### D. gRPC Proto Contract

```python
# ColliderAgentRunner/tests/grpc/test_proto_contract.py

def test_bootstrap_response_has_all_fields():
    """Ensure BootstrapResponse has session_id, agents_md, soul_md, etc."""

def test_context_chunk_oneof_coverage():
    """Every oneof variant (skill, tool_schema, system_prompt, etc.) can be constructed."""

def test_skill_chunk_round_trip():
    """SkillDefinition dict → SkillChunk protobuf → back to dict preserves all fields."""
```

#### E. Prompt Builder Parity

```typescript
// NanoClawBridge/test/sdk/prompt-parity.test.ts
// Compare SDK-generated system prompt vs filesystem-generated CLAUDE.md

describe("prompt parity", () => {
  it("SDK system prompt contains same sections as CLAUDE.md workspace file");
  it("skill sections match SKILL.md content");
  it("tool instructions match tools_md section");
});
```

### Priority 3: Component Tests

#### F. FFS4 Frontend Components

```typescript
// FFS4/src/__tests__/stores.test.ts
// Uses vitest + @testing-library/react

describe("graphStore", () => {
  it("sets and retrieves nodes/edges");
  it("handles empty state");
});

describe("contextStore", () => {
  it("toggles node selection");
  it("resets state cleanly");
});

describe("sessionStore", () => {
  it("adds messages in order");
  it("streaming text delta accumulates correctly");
  it("finalizeLastAssistant marks streaming complete");
});
```

#### G. Chrome Extension Iframe Bridge

```typescript
// ColliderMultiAgentsChromeExtension/test/iframe-bridge.test.ts

describe("iframe bridge", () => {
  it("ignores messages from wrong origin");
  it("forwards DOM_QUERY to content script");
  it("relays response back to iframe");
  it("stores CONTEXT_READY in session storage");
});
```

#### H. Workspace Manager Tool

```python
# ColliderGraphToolServer/tests/tools/test_workspace_manager.py

async def test_permission_enforcement():
    """app_user cannot perform 'open' or 'close' actions."""

async def test_superadmin_has_all_permissions():
    """superadmin can perform all 6 actions."""

async def test_navigate_requires_target():
    """navigate without target returns error."""

async def test_graceful_offline_handling():
    """If ffs6 is not running, returns offline status instead of crashing."""
```

### Priority 4: E2E Smoke Tests

#### I. Full Stack Smoke Test

```bash
#!/bin/bash
# scripts/smoke-test.sh
# Starts all services, seeds DB, runs a session, verifies output

# 1. Start DataServer, GraphToolServer, AgentRunner (with gRPC)
# 2. Start NanoClawBridge (SDK mode)
# 3. Seed test data
# 4. POST /agent/session with test node IDs
# 5. Connect WebSocket, send "Hello"
# 6. Verify text_delta events received
# 7. Verify no errors in logs
# 8. Shutdown all services
```

#### J. Context Hot-Reload Test

```python
# tests/e2e/test_hot_reload.py

async def test_node_update_triggers_context_delta():
    """
    1. Create agent session
    2. Update a node's skill via DataServer API
    3. Verify SSE delta fires
    4. Verify agent's next response reflects the updated skill
    """
```

---

## Test Infrastructure Recommendations

### Python (pytest)

```toml
# pyproject.toml additions
[tool.pytest.ini_options]
markers = [
    "unit: fast, no external deps",
    "integration: requires running services",
    "e2e: full stack smoke tests",
]
```

Run by tier:
```bash
uv run pytest -m unit          # Fast, CI-safe
uv run pytest -m integration   # Needs services running
uv run pytest -m e2e           # Full stack
```

### TypeScript (vitest)

```typescript
// vitest.config.ts
export default {
  test: {
    include: ["test/**/*.test.ts"],
    coverage: { reporter: ["text", "lcov"], thresholds: { lines: 80 } },
  },
};
```

### Coverage Targets

| Module               | Target | Current           |
| -------------------- | ------ | ----------------- |
| prompt-builder.ts    | 90%    | test exists       |
| tool-executor.ts     | 85%    | test exists       |
| team-manager.ts      | 85%    | needs test        |
| anthropic-agent.ts   | 70%    | needs mock SDK    |
| context-client.ts    | 75%    | needs integration |
| context_service.py   | 85%    | test exists       |
| workspace_manager.py | 80%    | needs test        |

### CI Pipeline (Recommended)

```yaml
# .github/workflows/test.yml
stages:
  - unit-python:    pytest -m unit (fast, no deps)
  - unit-ts:        vitest run (fast, no deps)
  - proto-compile:  uv run python -m proto.compile_protos
  - tsc-check:      npx tsc --noEmit (NanoClawBridge)
  - vite-build:     npx vite build (FFS4)
  - integration:    start services → pytest -m integration + vitest integration
```

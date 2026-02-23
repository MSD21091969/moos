# Collider Skills Architecture — PI Runtime Mode

> Defining how Collider's recursive NodeContainer model integrates with the PI
> open-source agent harness as a fully customizable, model-agnostic runtime,
> replacing the Anthropic SDK dependency without MCP or Claude Code.

Version: v1.0.0-pi — 2026-02-23

---

## 1. The Core Premise: Why PI?

### 1.1 What the Other Two Options Leave Unresolved

**Option A (SDK/gRPC)** ties the runtime to `@anthropic-ai/sdk`:
- `AnthropicAgent` in `NanoClawBridge/src/sdk/anthropic-agent.ts` imports Anthropic event types and content blocks directly.
- The tool-call loop mirrors Anthropic's `tool_use` / `tool_result` message format end-to-end.
- Model selection is constrained by what Anthropic's SDK supports.
- Every mid-session context update must be tunneled through a custom gRPC → SDK splice that the SDK was not designed for.

**Option B (Native MCP)** introduces a new dependency surface:
- Requires the `ColliderGraphToolServer` MCP handler to expose `prompts/list` and `resources/list` — primitives not yet implemented.
- Forces client code to behave as an MCP client, adding protocol negotiation overhead.
- Decouples control from the session orchestration layer in ways that complicate streaming event parity for the WebSocket bridge.

**Option C — PI Runtime** takes a different position: the agent harness is an
**engineering artifact you own**, not a vendor product you integrate. PI
(open-source TypeScript agent harness by Mario Zechner) provides a 200-token
base prompt, four primitive tools, and a composable extension system. Everything
else — context delivery, skill injection, tool routing, team orchestration, and
security policy — is built once, owned fully, and versioned with the Collider
codebase.

This is the preferred integration pattern for Collider because:
- The `NodeContainer` graph already provides everything the harness needs.
- Context is already being composed by `AgentRunner` over gRPC — PI consumes that output without protocol changes.
- Tools already execute via DataServer REST — PI calls that endpoint directly.
- No new protocol surface is added. The WS bridge, session manager, and team manager in `NanoClawBridge` keep their contracts unchanged.

### 1.2 SkillsBench Alignment

The SkillsBench findings (arXiv:2602.12670, Feb 2026) remain the design
constraint for all three options:

| Finding | Implication for PI mode |
| --- | --- |
| 2-3 focused skills = +18.6pp | PI extension injects only the top-N ranked skills per session, not all composed skills. |
| Comprehensive skills hurt (-2.9pp) | PI base prompt stays minimal (~200 tokens). Skills are appended selectively by the extension, not baked in. |
| Curated skills = +16.2pp | Skills authored in `NodeContainer.skills[]` and curated by the seeder — PI does not self-generate them. |
| Domains with poor pretraining benefit most | Collider's custom tool/workflow domain is exactly the target zone for curated procedural skills. |

### 1.3 What PI Gives Collider

| Capability | PI mechanism | Collider use |
| --- | --- | --- |
| Minimal base prompt | 200-token default, no opinion | Room for Collider workspace context without fighting the base prompt |
| Extension system | TypeScript composable units | Each Collider session type (workspace, team, root-agent) is a stacked extension set |
| Hooks | `beforeTool`, `afterTool`, `beforeBash`, `onComplete` lifecycle points | Tool allowlist, secret redaction, audit logging, approval gates |
| Widgets | Persistent terminal UI blocks | Session identity, skill index, active node path |
| Model agnosticism | Any model via provider config | Gemini 2.5 Flash (active), Anthropic fallback, others without SDK changes |
| No MCP dependency | PI calls tools via bash or HTTP directly | DataServer REST endpoint is the tool execution backend; no protocol layer needed |
| Open source, pinnable | Full TypeScript, semver pinned | No forced upgrades, full auditability, forkable |

---

## 2. Three-Layer Model (PI Runtime Adjusted)

```text
Layer 3: INTERFACE        PI Runtime Loop (model-agnostic turn execution)
          │                Collider extensions stacked: context, skills, tools, policy
          │ extensions composed per session type at session init
          │
Layer 2: CONTAINER        gRPC Bootstrap → ComposedContext → PI extension state
          │                Skills ranked and injected; tools mapped to REST calls
          │ composed by AgentRunner.compose_context_set() (unchanged)
          │
Layer 1: GRAPH            The Node Tree (source of truth, unchanged)
                           NodeContainer in SQLite: tools[], skills[], workflows[]
                           Navigated via DataServer REST :8000
```

### Layer 1 — Graph (unchanged)

The database remains the source of truth for all three options. Node tree
navigation and bootstrap are identical:

```text
GET :8000/api/v1/agent/bootstrap/{node_id}?depth=N   → AgentBootstrap
GET :8000/api/v1/apps/{id}/nodes/{node_id}/ancestors  → ancestor chain
POST :8000/api/v1/execution/tool/{name}               → tool execution result
```

PI runtime does not navigate the graph directly. Context is pre-composed by
`AgentRunner` before the PI session starts.

### Layer 2 — Container (gRPC bootstrap → PI extension state)

`AgentRunner` continues to run `compose_context_set()` and expose the result
via `gRPC GetBootstrap` at `:50051`. The PI session manager (replacing
`AnthropicAgent`) calls this RPC at session start and stores the result as
extension-accessible state:

```typescript
// NanoClawBridge/src/sdk/pi-adapter.ts (NEW)
const bootstrap = await grpcClient.getBootstrap(sessionRequest);

const piSession = await PIRuntime.create({
  extensions: [
    colliderContextExtension(bootstrap),   // injects skill index + node identity
    colliderToolsExtension(bootstrap),     // maps tool schemas to REST calls
    colliderPolicyExtension(policyConfig), // hooks: allowlist, redaction, audit
    colliderWidgetExtension(bootstrap),    // persistent session widget
  ],
  model: resolveModel(config),            // Gemini 2.5 Flash or configured provider
});
```

The `BootstrapResponse` fields map into PI extension state — no new schemas
required at the gRPC layer for the first milestone.

### Layer 3 — Interface (PI runtime loop)

PI executes an agent turn loop natively. The Collider adapter wraps the loop to
emit the same WebSocket event frames the `ws-bridge.ts` already consumes:

```text
PI turn start
  → beforeTool hook (policy: allowlist check, secret scan)
  → model generates response with tool calls
  → PI calls tool via colliderToolsExtension → POST :8000/execution/tool/{name}
  → afterTool hook (audit log entry)
  → text delta events emitted → ws-bridge forwards to client
PI turn complete → message_end event emitted
```

The WS bridge, session manager, and FFS4 frontend are untouched.

---

## 3. Extension Architecture — The Collider PI Extension Stack

PI extensions are TypeScript modules. They compose by stacking. Each Collider
session type gets its own named extension combination:

```typescript
// NanoClawBridge/src/pi/extensions/index.ts
export const EXTENSION_SETS = {
  // Standard workspace agent session
  workspace: [
    colliderContextExtension,
    colliderToolsExtension,
    colliderPolicyExtension,
    colliderWidgetExtension,
  ],

  // Root agent — full subtree, all 15 tools, full node identity
  root: [
    colliderContextExtension,
    colliderToolsExtension,
    colliderPolicyExtension,
    colliderWidgetExtension,
    colliderRootAgentExtension,   // adds root-specific skill + identity
  ],

  // Team leader — merged context + team-coordinator skill
  teamLeader: [
    colliderContextExtension,
    colliderToolsExtension,
    colliderPolicyExtension,
    colliderTeamLeaderExtension,  // team-coordinator skill + mailbox dispatch
  ],

  // Team member — isolated node context
  teamMember: [
    colliderContextExtension,     // scoped to single node only
    colliderToolsExtension,
    colliderPolicyExtension,
    colliderTeamMemberExtension,  // mailbox receive + structured result format
  ],
};
```

Extensions are loaded at session creation based on the `session_type` field in
the session request. Switching session types does not require code changes —
only the extension set selection changes.

### 3.1 colliderContextExtension

Reads `BootstrapResponse` from gRPC and builds the PI system prompt addendum:

```typescript
// NanoClawBridge/src/pi/extensions/collider-context.ts
export function colliderContextExtension(bootstrap: BootstrapResponse): PIExtension {
  return {
    name: "collider-context",
    systemPromptAddendum: buildWorkspaceContext(bootstrap),  // structured workspace state
    widget: buildNodeWidget(bootstrap),                      // persistent node identity widget
  };
}
```

`buildWorkspaceContext()` renders the structured format proposed in
`skills-architecture.md` Section 7, into the PI system prompt addendum:

```text
# Workspace Context

## Position in Graph
- Node: factory/ffs2/agent-runner
- Ancestors: factory → factory/ffs1 → factory/ffs2
- Kind: workspace | Depth: 3

## Active Skills (2)
### collider-workspace [navigation | global]
Navigate Collider's recursive workspace container model.
- Exposes: bootstrap_context, discover_tools, execute_workflow

### grpc-context-delivery [procedural | local]
gRPC context streaming pipeline for agent sessions.
- Inputs: ContextSet, node_ids → Outputs: BootstrapResponse

## Available Tools (5)
stream_context | get_bootstrap | discover_tools | execute_tool | execute_workflow

## Session
Role: superadmin | App: c57ab23a-... | Composed from: factory/ffs2, factory/ffs2/agent-runner
```

**Skill selection policy**: the extension applies a deterministic ranker over
`bootstrap.skills[]` and injects only the top 2-3 by relevance (node scope >
description keyword match > prior tool usage). Full `markdown_body` is included
for injected skills. Remaining skills appear as name + description only.

### 3.2 colliderToolsExtension

PI's four default tools are `read`, `write`, `edit`, `bash`. Collider adds
Collider-native tools by registering custom tool handlers that route to the
DataServer REST execution endpoint:

```typescript
// NanoClawBridge/src/pi/extensions/collider-tools.ts
export function colliderToolsExtension(bootstrap: BootstrapResponse): PIExtension {
  const colliderTools = bootstrap.tool_schemas.map((schema) => ({
    name: schema.name,
    description: schema.description,
    parameters: schema.params_schema,
    handler: async (args: unknown) => {
      const result = await fetch(`http://localhost:8000/api/v1/execution/tool/${schema.name}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: sessionToken },
        body: JSON.stringify({ arguments: args, session_id: sessionId }),
      });
      return result.json();
    },
  }));
  return { name: "collider-tools", tools: colliderTools };
}
```

This replaces the Anthropic-specific `getApiTools()` shape in
`tool-executor.ts` with a PI-native tool registration. The underlying REST call
to `:8000/execution/tool/{name}` is identical — only the call framing changes.

### 3.3 colliderPolicyExtension

PI hooks provide lifecycle control. This extension enforces Collider's security
policy without a separate mode or permission system:

```typescript
// NanoClawBridge/src/pi/extensions/collider-policy.ts
const TOOL_ALLOWLIST = ["execute_tool", "execute_workflow", "discover_tools",
                         "get_bootstrap", "stream_context", "read", "write", "edit"];
const BASH_DENYLIST  = [/rm\s+-rf/, /DROP\s+TABLE/i, /curl.*api_keys/];
const SECRET_PATTERN = /sk-[a-zA-Z0-9]{32,}/g;

export function colliderPolicyExtension(config: PolicyConfig): PIExtension {
  return {
    name: "collider-policy",
    hooks: {
      beforeTool: async (tool, args) => {
        if (!TOOL_ALLOWLIST.includes(tool)) throw new PolicyViolation(tool);
        return redactSecrets(args, SECRET_PATTERN);
      },
      beforeBash: async (cmd) => {
        for (const pattern of BASH_DENYLIST) {
          if (pattern.test(cmd)) throw new PolicyViolation(cmd);
        }
        return cmd;
      },
      afterTool: async (tool, result, ctx) => {
        await auditLog.append({ tool, session: ctx.sessionId, ts: Date.now() });
        return result;
      },
    },
  };
}
```

Privileged tools (e.g., node `delete`, app `create`) require an approval gate
hook that emits a `requires_approval` WS event before executing.

### 3.4 colliderWidgetExtension

A persistent widget showing the active workspace identity and skill count:

```typescript
// NanoClawBridge/src/pi/extensions/collider-widget.ts
export function colliderWidgetExtension(bootstrap: BootstrapResponse): PIExtension {
  return {
    name: "collider-widget",
    widget: {
      content: `[${bootstrap.session_meta.node_path}] ${bootstrap.skills.length} skills | ${bootstrap.tool_schemas.length} tools`,
      position: "footer",
      updateOn: ["tool_complete", "context_delta"],
    },
  };
}
```

---

## 4. Context Delivery (gRPC Bootstrap, No Changes Required)

PI mode reuses the gRPC context pipeline from Option A with no modifications:

```text
Chrome Extension / FFS4
  → POST :8004/agent/session (role, node_ids, vector_query, session_type)
  → AgentRunner: compose_context_set() → BootstrapResponse
  → PISessionManager: gRPC GetBootstrap(:50051)
  → PI runtime created with stacked Collider extensions
  → session_id + ws_url returned to caller
  → Client connects WebSocket → turns loop via pi-adapter.ts
```

**SSE context deltas**: the existing `ContextSubscriber` in
`NanoClawBridge/src/sse/context-subscriber.ts` can call `piSession.updateContext(delta)`
on each incoming delta, which triggers re-injection of the modified system
prompt addendum at the next turn boundary. No runtime restart required.

---

## 5. Team Strategy — External Orchestration

PI has no native subagent primitives. The `TeamManager` in
`NanoClawBridge/src/sdk/team-manager.ts` already implements external
orchestration. Under PI mode it is unchanged in contract — only the underlying
session object changes from `AnthropicAgent` to `PISession`:

```text
TeamManager.createTeam(nodeIds):
  → leader = PISession(EXTENSION_SETS.teamLeader, bootstrap(all nodes))
  → members = nodeIds.map(id => PISession(EXTENSION_SETS.teamMember, bootstrap(id)))
  → mailbox routes: leader.sendTask(memberId, task) → member input queue
  → member result → mailbox → leader context delta → next leader turn
```

**Team-coordinator auto-skill** is injected by `colliderTeamLeaderExtension`
into the leader's system prompt addendum. The PI extension generates it from the
live team member list at session creation time.

**Agent chains (pipelines)**: PI naturally supports sequential agent chains by
spawning multiple `PISession` instances and piping one session's output as the
next session's input message. Implemented in
`NanoClawBridge/src/pi/pipeline-runner.ts` (NEW) and exposed as
`POST :18789/agent/pipeline` for multi-step automated workflows.

---

## 6. Model Provider Integration

PI is model-agnostic. The provider is configured via the existing
`COLLIDER_AGENT_PROVIDER` environment variable, resolved at PI session creation:

```typescript
// NanoClawBridge/src/pi/model-resolver.ts
export function resolveModel(config: AgentConfig): PIModelConfig {
  switch (config.provider) {
    case "gemini":
      return { provider: "google", model: config.model ?? "gemini-2.5-flash", apiKey: process.env.GEMINI_API_KEY };
    case "anthropic":
      return { provider: "anthropic", model: config.model ?? "claude-sonnet-4-6", apiKey: process.env.ANTHROPIC_API_KEY };
    case "ollama":
      return { provider: "ollama", model: config.model ?? "llama3", baseUrl: "http://localhost:11434" };
    default:
      throw new Error(`Unknown provider: ${config.provider}`);
  }
}
```

Switching models or providers is a config change, not a code change. This
resolves the current single-provider coupling in `anthropic-agent.ts`.

---

## 7. WebSocket Bridge Compatibility

The `ws-bridge.ts` and FFS4 frontend are untouched. The PI adapter emits the
same internal event shapes the bridge already handles:

| Bridge event | PI source |
| --- | --- |
| `text_delta` | PI streaming token callback |
| `tool_start` | `beforeTool` hook entry |
| `tool_result` | `afterTool` hook exit |
| `message_end` | PI turn completion callback |
| `error` | PI error boundary catch |
| `requires_approval` | Privileged tool gate hook |
| `context_delta_applied` | `updateContext()` completion |

No changes required in:
- `NanoClawBridge/src/ws-bridge.ts`
- `NanoClawBridge/src/session-manager.ts` (session object type becomes `PISession | AnthropicSession` union)
- `NanoClawBridge/src/sdk/tool-executor.ts` (REST call logic unchanged; only registered differently)
- All FFS4 frontend WS consumers (`nanoclaw-client.ts`, `sessionStore`, UI components)

---

## 8. Feature Flag and Rollout

A single environment variable gates the PI runtime:

```env
# NanoClawBridge .env
COLLIDER_AGENT_RUNTIME=anthropic   # default (unchanged behavior)
COLLIDER_AGENT_RUNTIME=pi          # PI runtime for new sessions
COLLIDER_AGENT_RUNTIME=pi-shadow   # PI runs in parallel, results logged but not returned
```

`session-manager.ts` selects the runtime at session creation:

```typescript
const runtime = config.agentRuntime === "pi"
  ? new PISessionManager(grpcClient, config)
  : new AnthropicSessionManager(grpcClient, config);
```

Both implement the same `IAgentSession` interface. Switching is instantaneous
with no migration, no DB changes, and no client changes. The Anthropic path
remains fully functional in parallel.

`pi-shadow` mode enables production validation: both runtimes process the same
input, PI results are written to the audit log and compared, but only the
Anthropic result is returned to the client.

---

## 9. Compatibility Matrix

| Component | PI mode impact | Change required |
| --- | --- | --- |
| `ColliderDataServer` (`:8000`) | None — tool execution REST endpoint unchanged | No |
| `ColliderGraphToolServer` (`:8001`) | None — no MCP dependency in PI mode | No |
| `ColliderVectorDbServer` (`:8002`) | None — semantic discovery used identically | No |
| `ColliderAgentRunner` (`:8004 / :50051`) | None — gRPC bootstrap reused unchanged | No |
| `proto/collider_graph.proto` | None for milestone 1; graph-aware fields optional later | No (milestone 1) |
| `NanoClawBridge/src/sdk/anthropic-agent.ts` | Replaced by `pi-adapter.ts` behind feature flag | New file, no edit |
| `NanoClawBridge/src/session-manager.ts` | Union type for session object; runtime selected by flag | Minor edit |
| `NanoClawBridge/src/sdk/tool-executor.ts` | REST call logic preserved; registration path changes | Minor edit |
| `NanoClawBridge/src/ws-bridge.ts` | No change | No |
| `NanoClawBridge/src/sdk/team-manager.ts` | Session type becomes interface union | Trivial edit |
| FFS4 frontend (`:4201`) | No change | No |
| Chrome Extension | No change | No |
| `sdk/seeder/` | No change | No |
| `nodes.py` schema | No change for PI milestone 1 | No |

---

## 10. Implementation Roadmap

### Phase 0: Spike and Contract Definition

**Effort: 1–2 days**

| File | Action |
| --- | --- |
| `NanoClawBridge/src/pi/` | Create directory structure |
| `NanoClawBridge/src/pi/types.ts` | Define `PISession`, `IAgentSession`, `PIExtension`, `PIModelConfig` |
| `NanoClawBridge/src/pi/pi-adapter.ts` | Skeleton: `createSession()`, `sendMessage()`, `injectContext()`, `terminateSession()` |
| `NanoClawBridge/src/session-manager.ts` | Add `IAgentSession` interface; union runtime selection behind flag |

Exit gate: `IAgentSession` interface agreed; both runtimes compile cleanly.

### Phase 1: Context Extension

**Effort: 2–3 days**

| File | Action |
| --- | --- |
| `NanoClawBridge/src/pi/extensions/collider-context.ts` | `colliderContextExtension` — gRPC bootstrap → structured system prompt addendum + skill ranker |
| `NanoClawBridge/src/pi/extensions/collider-widget.ts` | `colliderWidgetExtension` — persistent session identity widget |
| `NanoClawBridge/src/pi/model-resolver.ts` | Provider resolution: gemini/anthropic/ollama |

Exit gate: PI session creates, base prompt includes structured workspace context, widget visible.

### Phase 2: Tool Execution Extension

**Effort: 2–3 days**

| File | Action |
| --- | --- |
| `NanoClawBridge/src/pi/extensions/collider-tools.ts` | `colliderToolsExtension` — maps `tool_schemas` to PI-native tool handlers calling DataServer REST |
| `NanoClawBridge/src/sdk/tool-executor.ts` | Refactor execution path to accept both Anthropic-style and PI-style tool call envelopes |

Exit gate: PI session successfully executes a registered Collider tool via DataServer REST and returns result to the agent turn.

### Phase 3: Policy Extension + WS Bridge Parity

**Effort: 3–4 days**

| File | Action |
| --- | --- |
| `NanoClawBridge/src/pi/extensions/collider-policy.ts` | `colliderPolicyExtension` — tool allowlist, bash denylist, secret redaction, audit log, approval gate hook |
| `NanoClawBridge/src/pi/pi-adapter.ts` | Emit WS events (`text_delta`, `tool_start`, `tool_result`, `message_end`, `error`) in parity with Anthropic adapter |
| `NanoClawBridge/src/ws-bridge.ts` | Verify: no changes needed |

Exit gate: Shadow mode `pi-shadow` runs parity comparison; event streams match on 3 representative sessions.

### Phase 4: Team Extensions

**Effort: 3–4 days**

| File | Action |
| --- | --- |
| `NanoClawBridge/src/pi/extensions/collider-team-leader.ts` | `colliderTeamLeaderExtension` — team-coordinator auto-skill, mailbox dispatch |
| `NanoClawBridge/src/pi/extensions/collider-team-member.ts` | `colliderTeamMemberExtension` — mailbox receive, result format schema |
| `NanoClawBridge/src/sdk/team-manager.ts` | Session object becomes `IAgentSession` union |
| `NanoClawBridge/src/pi/pipeline-runner.ts` | **NEW** — sequential PI agent chain runner |

Exit gate: Team session creates with leader + 2 members; task delegation and result collection verified.

### Phase 5: Shadow Traffic + Staged Rollout

**Effort: 2–3 days**

| Action | Criteria |
| --- | --- |
| `COLLIDER_AGENT_RUNTIME=pi-shadow` on dev environment | Event parity ≥ 99% on logged sessions |
| Log quality metrics: task completion, tool error rate, token usage delta vs Anthropic | Within 10% of baseline |
| Gate to `pi` as default for new sessions | Zero critical policy bypasses in abuse test suite |
| Anthropic path retained as `COLLIDER_AGENT_RUNTIME=anthropic` | Available indefinitely |

**Total estimated effort: 2–3 weeks (one engineer), 10–14 days (two engineers)**

---

## 11. Verification Plan

Mapped to `TEST_STRATEGY.md` tiers:

### Priority 1 — Integration (Phase 0 exit gate)

```typescript
// NanoClawBridge/test/pi/pi-session-lifecycle.test.ts
describe("PI session lifecycle", () => {
  it("creates session from gRPC bootstrap with collider extensions stacked");
  it("sends message and receives text_delta events in same shape as Anthropic adapter");
  it("executes a collider tool via DataServer REST and returns result in turn");
  it("injects context delta mid-session without restart");
  it("terminates and cleans up resources");
});
```

### Priority 2 — Contract (event parity)

```typescript
// NanoClawBridge/test/pi/event-parity.test.ts
describe("PI vs Anthropic event parity", () => {
  it("text_delta events have identical shape");
  it("tool_start includes tool name and args");
  it("tool_result includes result and tool name");
  it("message_end fires after last text delta");
  it("error event includes code and message");
});
```

### Priority 3 — Component (extensions unit tests)

```typescript
// NanoClawBridge/test/pi/extensions/
describe("colliderContextExtension", () => {
  it("ranks skills and injects top 2 with full markdown_body");
  it("remaining skills appear as name + description only");
  it("structured workspace context includes graph position, tools table, session meta");
});

describe("colliderToolsExtension", () => {
  it("registers one PI tool per bootstrap tool_schema");
  it("tool handler calls DataServer REST with correct name and args");
  it("returns tool result to agent turn");
});

describe("colliderPolicyExtension", () => {
  it("blocks a tool not in allowlist and throws PolicyViolation");
  it("redacts API key patterns from tool args before execution");
  it("denylisted bash command throws PolicyViolation before execution");
  it("afterTool hook writes an audit log entry");
});

describe("colliderTeamLeaderExtension", () => {
  it("injects team-coordinator skill with member list");
  it("mailbox dispatch routes task to correct member session");
});
```

### Priority 4 — E2E Smoke

```bash
# scripts/smoke-test-pi.sh
# 1. Set COLLIDER_AGENT_RUNTIME=pi
# 2. Start AgentRunner (gRPC), DataServer, NanoClawBridge
# 3. POST /agent/session with test node IDs
# 4. Connect WebSocket, send "list available tools"
# 5. Verify text_delta and message_end events received
# 6. Execute one registered tool via agent prompt
# 7. Verify tool_start + tool_result + message_end sequence
# 8. Shutdown
```

---

## Appendix A: Decision Log

### Q: Why embed PI in NanoClawBridge rather than replace it?

**A: Blast radius minimization.** NanoClawBridge's WebSocket contract, session
manager, team manager, and tool executor are all working. Replacing only the
runtime adapter (`AnthropicAgent` → `PISession`) behind an interface leaves
every other component unchanged and the Anthropic path fully operational in
parallel.

### Q: Why no MCP in PI mode?

**A: PI does not have native MCP support, and Collider does not need it here.**
Tools execute via DataServer REST (`:8000/execution/tool/{name}`). The
GraphToolServer MCP endpoint (`:8001/mcp/sse`) remains available for IDE
clients (Copilot, Claude Code) connecting directly — that use case is
unaffected. Adding MCP client behavior to PI would require custom extension code
equivalent to the REST calls already in place, with no benefit.

### Q: How do skills get into the PI session without a static SKILL.md?

**A: Via `colliderContextExtension`.** The extension receives the full
`BootstrapResponse` from gRPC, applies the skill ranker, and injects selected
skills as part of the PI system prompt addendum. The `NodeContainer.skills[]`
in SQLite is the source of truth. No files are written to disk for PI mode.
The workspace writer path (`USE_SDK_AGENT=false`) remains available for the
Claude CLI fallback only.

### Q: Where does state live mid-session?

**A: In the PI extension state and the system prompt addendum.** The PI session
addendum IS the state — it reflects the composed graph context at session
creation. SSE deltas update the addendum via `piSession.updateContext(delta)`
at turn boundaries. No separate state store is required.

### Q: How does this interact with the planned graph-aware skill fields (Option A Phase 1)?

**A: Additive and compatible.** When `nodes.py` gains `SkillKind`, `SkillScope`,
and provenance fields, `colliderContextExtension` can immediately use them to
render richer structured context without any PI extension API change. Option A's
data model work benefits all three architectures.

### Q: Is PI suitable for production?

**A: Yes, with the policy extension.** PI defaults to YOLO mode with no
permission gates. The `colliderPolicyExtension` adds the mandatory controls
(allowlist, denylist, secret redaction, audit log, approval gate) that make it
production-safe in the Collider multi-user context. The shadow traffic phase
(`pi-shadow`) provides empirical confidence before cutover.

---

_Architecture document for the Collider ecosystem. References: PI agent harness
(github.com/badlogic/pi), SkillsBench (arXiv:2602.12670v1), Collider
skills-architecture.md v1.0.0, skills-architecture-alternative.md v1.0.0-alt._

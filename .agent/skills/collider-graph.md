# collider-graph

> **Note**: This skill is being superseded by the `collider-workspace` meta-skill.
> See the full architecture: `.agent/knowledge/architecture/skills-architecture.md`

## Application → Workflow → Tool — the Collider execution pattern

## The Pattern

```text
Application  (NodeContainer tree)
  ↓  bootstrap
Workflow     (SubgraphManifest — ordered steps)
  ↓  execute
Tool         (GraphStepEntry — code_ref → result)
```

### Application

A Collider Application is a tree of NodeContainers. Each node carries:

- `instructions` (agents_md) — who this agent is
- `rules` (soul_md) — constraints and guardrails
- `knowledge` (tools_md) — reference documentation
- `skills` — reusable playbooks
- `tools` — registered GraphStepEntry references

Bootstrap a node to get its full composed context:

```text
GET :8000/api/v1/agent/bootstrap/{node_id}?depth=N
→ { agents_md, soul_md, tools_md, skills[], tool_schemas[] }
```

Navigate the tree:

```text
GET :8000/api/v1/apps/{app_id}/nodes/                          → full list
GET :8000/api/v1/apps/{app_id}/nodes/{node_id}/ancestors       → ancestry chain
GET :8000/api/v1/apps/{app_id}/nodes/{node_id}/children        → direct children
```

### Workflow

A workflow is a `SubgraphManifest` — an ordered list of tool names (steps).
Registered in GraphToolServer and executable as a single call.

Discover workflows:

```text
GET :8001/api/v1/registry/workflows/{workflow_name}
→ { workflow_name, steps: ["tool_a", "tool_b", ...], entry_point }
```

Execute workflow (all steps sequentially, each step's output feeds into next):

```text
POST :8001/api/v1/registry/workflows/{workflow_name}/execute
Body: { inputs: {} }
→ { success, steps: [{name, result}], final_result }
```

Execute via MCP (preferred for NanoClaw):

```text
MCP server at http://localhost:8001/mcp/sse
```

### Tool

A tool is a `GraphStepEntry` with a `code_ref` pointing to a Python function.
The ToolRunner imports and executes it dynamically.

Discover tools (semantic search):

```text
POST :8001/api/v1/registry/tools/discover
Body: { query: "...", visibility_filter: ["global", "group"] }
→ { tools: [{ tool_name, params_schema, code_ref, visibility }] }
```

Execute via MCP (NanoClaw's primary path — configured in .mcp.json):

```text
MCP SSE: http://localhost:8001/mcp/sse
```

Execute via REST (if MCP unavailable):

```text
POST :8000/execution/tool/{tool_name}
Headers: Authorization: Bearer <JWT>
Body: { ...inputs }
```

## NanoClaw Integration Points

| Layer              | Interface                               | Port  |
| ------------------ | --------------------------------------- | ----- |
| Context bootstrap  | `GET /api/v1/agent/bootstrap/{node_id}` | :8000 |
| Tool execution     | MCP SSE                                 | :8001 |
| Workflow execution | MCP SSE                                 | :8001 |
| Tool discovery     | `POST /api/v1/registry/tools/discover`  | :8001 |

## Session Lifecycle

```text
1. Chrome ext  → POST :8004/agent/session  (ContextSet → bootstrap → system_prompt)
               ← { session_id, preview, nanoclaw_ws_url: "ws://127.0.0.1:18789" }

2. Chrome ext  → WebSocket ws://127.0.0.1:18789  (direct to NanoClawBridge)
               → send: { type: "request", method: "agent.request", params: { message: "..." } }
               ← recv: { type: "event", event: "text_delta", data: "..." } ... { kind: "message_end" }

3. NanoClawBridge → spawns Claude Code CLI (reads CLAUDE.md + .mcp.json + skills/)
                  → Claude Code → MCP SSE :8001  (tool execution)
```

## App 2XZ Reference

- App ID: `c57ab23a-4a57-4b28-a34c-9700320565ea`
- Root node: `9848b323-5e65-4179-a1d6-5b99be9f8b87`
- Auth: Sam / Sam (superadmin)

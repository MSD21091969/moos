# Collider Skills Architecture — Native MCP Alternative

> Defining how Collider's recursive NodeContainer model maps to Anthropic's Agent Skills paradigm using the native Model Context Protocol (MCP) instead of a custom gRPC streaming architecture.

Version: v1.0.0-alt — 2026-02-23

---

## 1. The Core Alternative: Why Native MCP?

The original `skills-architecture.md` proposed a custom gRPC pipeline (`ColliderContext`/`StreamContext`) and a custom JSON chunk format (`SkillChunk`) to stream skills into an agent's prompt. 

While valid, it reinvents exactly what the **Model Context Protocol (MCP)** was built to solve. The Collider ecosystem already exposes an MCP server (`ColliderGraphToolServer` at `http://localhost:8001/mcp/sse`). 

**The Alternative Proposal:** Instead of a bespoke gRPC pipeline mapping skills to prompt fragments in `NanoClawBridge`, we expose the composed `ContextSet` directly as a dynamic **MCP Server**. 

- **Skills become MCP Prompts/Resources:** Procedural knowledge is exposed via `prompts/list` or `resources/list`. Agents "pull" what they need when they need it, solving the context window bloat problem natively.
- **Tools become MCP Tools:** The node's executable actions are exposed via `tools/list`.
- **Navigation becomes MCP Prompts:** The `collider-workspace` meta-skill is just a global MCP prompt.

---

## 2. Three-Layer Model (MCP Adjusted)

```text
Layer 3: INTERFACE        Standard MCP Client (AgentRunner / Claude Code / Cursor)
          │                (Connects via SSE to the localized ContextSet server)
          │
Layer 2: CONTAINER        Dynamic MCP Server Instances
          │                (Exposes node's skills as Prompts/Resources via MCP)
          │ 
Layer 1: GRAPH            The Node Tree (Source of Truth)
                           (NodeContainer in SQLite with tools/skills)
```

### Layer 1 — Graph (unchanged)
The database remains the source of truth. Nodes have a `NodeContainer` that stores procedural knowledge, tools, and workflows.

### Layer 2 — Container (Dynamic MCP Exposure)
Instead of `compose_context_set()` building a massive string to shove into a system prompt, the `ColliderAgentRunner` spins up (or multiplexes) an MCP server specifically scoped to the requested `node_ids`. 

### Layer 3 — Interface (Standardized)
Because we use native MCP, *any* MCP-compliant client (Collider's AgentRunner, Anthropic's Claude desktop app, Cursor, etc.) can connect to a workspace and instantly inherit its context and skills. We achieve true interoperability.

---

## 3. Data Model — Mapping to MCP Primitives

We don't need a highly customized `SkillDefinition` with 15 fields. We map NodeContainer concepts directly to MCP primitives:

| Collider Concept | MCP Concept | Behavior |
| --- | --- | --- |
| Node Tool | **MCP Tool** | Exposed via `tools/list`. Executed via `tools/call`. |
| Procedural Skill | **MCP Prompt** | Exposed via `prompts/list`. The agent requests it via `prompts/get` when encountering a task matching the prompt's description. |
| Graph Topology | **MCP Resource** | The ancestor/child tree is exposed as a structured URI like `collider://graph/{node_id}/ancestors`. |
| Meta-Skill | **MCP Prompt** | `collider-workspace` is a globally available prompt that explains the graph representation. |

---

## 4. Context Extraction Strategy (RAG vs Push)

The original architecture relied on **Pushing** up to ~2000 tokens of skills into the system prompt. 
The MCP alternative relies on **Pulling** (or Just-In-Time retrieval).

### The SkillsBench Validation
SkillsBench demonstrated that *focused* skills outperform comprehensive ones. 
If a node has 20 skills, pushing all 20 degrades performance. 
In the MCP model, the Agent is given *only* the descriptions of available Prompts (Skills). 
When the Agent plans its task, it calls the MCP server to retrieve the full procedural markdown for only the 2-3 skills it actually needs for that specific turn.

### The Team Manager (Multi-Agent) Flow
- **Leader Agent:** Connects to the root compose MCP server. Sees all available prompts/tools.
- **Member Agent:** Is given a connection to an MCP sub-server scoped strict to its assigned node. It has absolute isolation natively enforced by the protocol.

---

## 5. Implementation Roadmap (MCP Alternative)

### Phase 1: ContextSet as an MCP Server
**Effort: 2 days**
- Hook `ColliderDataServer` into the existing `ColliderGraphToolServer` MCP router.
- Create an endpoint `GET :8001/mcp/sse?node_ids=A,B,C` that multiplexes a virtual MCP server scoped to those nodes.
- Implement `tools/list` utilizing the leaf-wins traversal for the selected nodes.

### Phase 2: Skills to Prompts
**Effort: 1-2 days**
- Map the markdown content of `NodeContainer.skills` into the MCP `prompts/list` and `prompts/get` handlers.
- The `description` of the skill becomes the MCP Prompt description, which the LLM uses to decide when to fetch it.

### Phase 3: Agent Integration
**Effort: 1 day**
- Modify `NanoClawBridge` to act as a standard MCP Client. 
- During session initialization, it connects to the SSE URL, fetches available tools and prompt descriptions, and seeds the initial system prompt.

### Phase 4: Topology as Resources
**Effort: 1 day**
- Implement `resources/list` and `resources/read` to expose the graph topology (ancestors, children) dynamically.

## 6. Summary of Benefits over gRPC
1. **Less Custom Code:** Relies on the open-source standardized `mcp` libraries rather than custom protobuf definitions and streaming loops.
2. **Interoperability:** Any MCP-compliant IDE or Agent can now "mount" a Collider workspace natively.
3. **Context Efficiency:** Agents pull full skill textures on-demand via Prompts, keeping the system prompt lean.

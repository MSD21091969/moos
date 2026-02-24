# Collider Skills + Runtime Integration: Full Project Document

> **Purpose**: Comprehensive analysis, research synthesis, and implementation blueprint for integrating Anthropic's 2026 Agent Skills paradigm with Collider's recursive NodeContainer graph, using the PI open-source runtime as the preferred agent harness. This document hydrates FFS0 `.agent/` knowledge for phased implementation across downstream workspaces.

> **Implementation Status (2026-02-24)**: Phases 5-9 have been implemented in NanoClawBridge with validation gates passing. Treat this document as canonical strategy + design rationale. For execution evidence and current operational thresholds, use:
> - `D:/FFS0_Factory/.agent/knowledge/architecture/phase5_mvp_execution_checklist.md`
> - `D:/FFS0_Factory/.agent/knowledge/architecture/phase9_shadow_validation_snapshot.md`

---

## 1. Goals

### 1.1 Primary Goals

1. **Unify graph and skills**: Make the recursive `NodeContainer` graph the single source of truth for agent capabilities. Skills become computed views of graph state — never stored duplicates.

2. **Runtime independence**: Decouple the agent session lifecycle from any single vendor SDK. Support Anthropic, PI, and future runtimes behind one interface contract (`IAgentSession`).

3. **Structured context delivery**: Replace flat markdown system prompts with graph-aware structured workspace state that gives agents spatial awareness, skill provenance, dataflow visibility, and tool inventories.

4. **SkillsBench compliance**: Follow empirical findings — inject 2-3 focused, curated skills per session. Never flood the context with comprehensive documentation.

5. **Harness-first engineering**: Build for deletion. Every piece of scaffolding should be removable when the model no longer needs it. Simpler harnesses with smarter models beat complex harnesses every time.

### 1.2 Secondary Goals

6. **Preserve existing behavior**: The Anthropic SDK path remains fully operational behind a feature flag. Zero disruption to current users.

7. **Namespace-aware skill governance**: Skills carry `namespace`, `version`, `scope`, and `source_node_path` for deterministic composition and conflict resolution.

8. **Model-agnostic operation**: Support Gemini, Anthropic, Ollama, and future providers without code changes — only configuration.

9. **Team orchestration parity**: Multi-agent teams (leader + members + mailbox) work identically across runtimes.

10. **Contract stability**: Formalize event schemas, composition schemas, and execution schemas so the bridge layer (`NanoClawBridge`) becomes a thin, stable relay.

### 1.3 Non-Goals (Explicitly Excluded)

- Full MCP prompts/resources implementation (deferred to later phase)
- Bidirectional `.agent/` <-> DB sync (one-way seed only for now)
- Self-generating skills (SkillsBench shows -1.3pp — skills must be human-curated)
- Replacing the DataServer REST execution endpoint (tools still execute via `:8000`)

---

## 2. Research Findings

### 2.1 The Harness Engineering Paradigm (2026)

The industry has converged on a critical insight: **the model is not the bottleneck — the harness is**.

**Key sources and findings:**

- **Anthropic's guide on effective harnesses** recommends a two-agent pattern (initializer + coding agent), progress files for state bridging, JSON over Markdown for feature tracking, and mandatory end-to-end testing before marking features complete. The gap between context windows is closed through documented artifacts, not context compaction alone.

- **OpenAI's Codex harness** uses a three-layered architecture: orchestrator (plans), executor (handles tasks), recovery layer (catches failures). Their key insight: harness engineering is about building tooling around the model to optimize task performance, token efficiency, and latency.

- **Manus rebuilt their framework 5 times** in 6 months. Their biggest gains came from REMOVING features. Key lessons:
  - **KV-cache hit rate** is the most important production metric (100:1 input/output token ratio)
  - **Task recitation**: Constantly rewrite the todo list to push objectives into the model's recent attention span
  - **Error preservation**: Leave failed actions in context so the agent learns from mistakes (don't erase)
  - **Filesystem as external memory**: Treat the filesystem as unlimited context; agent reads/writes files on demand
  - **Tool stability**: Don't dynamically add/remove tools (breaks KV-cache). Mask availability instead.

- **The Warcel study** showed that removing 80% of specialized tools and giving the agent bash + file access improved accuracy from 80% to 100%, was 3.5x faster, and used 40% fewer tokens. The engineer concluded: "Maybe the best agent architecture is almost no architecture at all."

- **The Bitter Lesson applied**: Approaches that scale with computational power always beat approaches relying on human-engineered domain knowledge. As models get smarter, your harness should get **simpler**, not more complex.

**Analogy for the vice-coder**: Think of smartphones. Early on, the processor was the whole story. But at some point processors got fast enough that the difference stopped mattering. What mattered was the OS, the camera software, the ecosystem. That's where AI is now — **the harness is the operating system**.

### 2.2 SkillsBench Empirical Data (arXiv:2602.12670)

86 tasks, 11 domains, 7 agent-model configurations, 7,308 trajectories. The first systematic benchmark for agent skills.

| Finding                                        | Number  | Collider Implication                                                 |
| ---------------------------------------------- | ------- | -------------------------------------------------------------------- |
| Curated skills average improvement             | +16.2pp | Human-authored procedural guidance is the highest-value augmentation |
| 2-3 focused skills sweet spot                  | +18.6pp | Inject only top 2-3 ranked skills per session                        |
| 4+ skills diminishing returns                  | +5.9pp  | Don't flood — more context != better                                 |
| Comprehensive skills hurt                      | -2.9pp  | Keep skills compact and procedural, not encyclopedic                 |
| Self-generated skills                          | -1.3pp  | Models can't author the knowledge they benefit from consuming        |
| Healthcare domain improvement                  | +51.9pp | Custom/novel domains benefit most (Collider's domain is novel)       |
| Software Engineering improvement               | +4.5pp  | Well-known domains benefit least (models already know coding)        |
| Smaller model + skills >= larger model without | Parity  | Skills are an equalizer across model tiers                           |

**Critical insight for Collider**: Your custom tool/workflow/workspace domain is exactly the kind of novel domain where curated skills provide the most uplift. Software engineering skills add only +4.5pp because models already know how to code. But teaching an agent how to navigate Collider's recursive container graph — that's a domain with poor pretraining coverage where skills will have **massive** impact.

### 2.3 Agent Skills Open Standard (agentskills.io)

The specification defines:

- **SKILL.md**: A directory containing a YAML frontmatter file + markdown body
- **Required fields**: `name` (slug format, max 64 chars), `description` (max 1024 chars)
- **Optional fields**: `license`, `compatibility`, `metadata` (key-value map), `allowed-tools`
- **Progressive disclosure**: Metadata loaded at startup (~100 tokens), full SKILL.md on activation (<5000 tokens recommended), reference files on demand
- **Directory structure**: `skill-name/SKILL.md` + optional `scripts/`, `references/`, `assets/`

**Where the spec falls short for Collider:**
- No concept of graph provenance (which node does this skill come from?)
- No concept of skill scope (local vs inherited vs composed vs global)
- No dataflow declarations (inputs, outputs, dependencies)
- No namespace/version support
- No concept of skill composition from multiple sources
- Designed for flat filesystems, not recursive graph structures

**Our approach**: Collider's `SkillDefinition` is a **superset** of the Agent Skills standard. The graph-aware fields (`kind`, `scope`, `source_node_path`, `inputs`, `outputs`, `depends_on`, `exposes_tools`, `namespace`, `version`) are Collider-specific extensions. Any skill can be exported as standard-compliant SKILL.md by omitting the extension fields.

### 2.4 Claude Code Agent Teams Architecture

Anthropic's experimental agent teams feature:

- **Lead + teammates**: One session coordinates, others work independently
- **Shared task list**: Tasks have states (pending/in-progress/completed) with dependencies
- **Mailbox**: Direct inter-agent messaging (not just report-back)
- **Context isolation**: Each teammate has own context window, loads project CLAUDE.md + skills
- **Self-coordination**: Teammates can claim tasks and communicate without lead mediation
- **Hooks**: `TeammateIdle` and `TaskCompleted` hooks for quality gates
- **Token cost**: Significantly higher than single session (each teammate is separate instance)

**Mapping to Collider teams:**
- Lead = merged context from all composed nodes (full ContextSet)
- Member = isolated context from single assigned node
- Mailbox = already implemented in `TeamManager`
- Shared task list = can be implemented as a PI extension widget
- Skill-based routing = leader uses `exposes_tools` field to route tasks to the right member

### 2.5 PI Agent Harness Architecture

PI (by Mario Zechner) provides:

- **Monorepo packages**: `pi-ai` (multi-provider LLM API), `pi-agent-core` (runtime + tool calling + state), `pi-coding-agent` (CLI), `pi-tui` (terminal UI), `pi-web-ui` (web components)
- **200-token base prompt** — minimal, unopinionated
- **4 primitive tools**: read, write, edit, bash
- **Composable extensions**: TypeScript modules that stack (system prompt addendum, widgets, hooks, tools, keybindings, themes)
- **25+ hook points**: `beforeTool`, `afterTool`, `beforeBash`, `onComplete`, `onInput`, `onAgentEnd`, `onToolCall`, `onSession`, etc.
- **Model agnostic**: Any model via provider config (OpenAI, Anthropic, Google, Ollama, etc.)
- **No MCP**: Tools call REST or bash directly
- **No native subagent support**: Must be built via extensions (already designed in `skills-architecture-pi.md`)
- **YOLO mode by default**: No permission prompts unless you build them in

### 2.6 NanoClaw Reference Pattern

NanoClaw (by qwibitai) demonstrates:

- **Container isolation**: Agents execute in Docker/Apple Container (not app-level permission checks)
- **Single-process orchestration**: One Node.js process handles everything
- **Skill-based customization**: Users add capabilities by creating `.claude/skills/add-X/SKILL.md` files rather than modifying core code
- **AI-native approach**: Relies on Claude Code for setup/debugging rather than config files
- **Agent Swarms**: Multi-agent collaboration via team spawning
- **Per-group context isolation**: Each conversation group gets its own `CLAUDE.md` memory

**Relevance to Collider**: NanoClaw validates the pattern of skills as the extension mechanism, and container isolation as the security model. Collider's per-node context isolation (each team member sees only their node's skills/tools) is the graph-native equivalent.

### 2.7 PydanticAI Graph Patterns

Recent PydanticAI developments validate Collider's approach:

- **Agent = container** with system prompt, tools, structured result, and LLM
- **Pydantic-graph library** powers agent state machines through typed node graphs
- **Recursive Pydantic models** are a first-class pattern for tree/graph data structures
- **Dependency injection** provides type-safe agent behavior customization
- **Multi-agent patterns**: Task delegation via specialized sub-agents with isolated context

**Validation**: Collider's `NodeContainer` recursive model using Pydantic is architecturally aligned with where the PydanticAI ecosystem is heading.

---

## 3. Strategies

### 3.1 Core Strategy: "Stabilize A, Build C"

**Phase 1**: Stabilize the existing Anthropic SDK path (Option A) by formalizing contracts — event schemas, composition schemas, execution schemas. Fix the gaps identified in the draft document (vector discovery mismatch, context delta route mismatch, execution config drift, schema strictness debt).

**Phase 2**: Build the PI runtime (Option C) behind the same interface contracts. Both runtimes implement `IAgentSession`. Feature flag selects which one runs.

**Rationale**: You can't build a new house on a cracked foundation. The contract mismatches identified in your draft (Section 3) would afflict the PI adapter too. Fix them once, benefit both runtimes.

### 3.2 Skill Strategy: "Graph is Truth, Skills are Interface, Runtime is Pluggable"

Three-layer source of truth:

1. **Authoring SoT (human)**: `.agent/` files — instructions, rules, skills, tools. The developer's workspace.
2. **Canonical SoT (system)**: DB `NodeContainer.skills[]` and container graph. The seeder syncs authoring SoT into this.
3. **Delivery SoT (runtime)**: Computed `ContainerSkillView[]` per session. Never stored — generated on the fly by `compose_context_set()`.

**Skill selection policy**: At session time, the context extension applies a deterministic ranker:
1. Filter: only `model_invocable: true` skills
2. Score: node scope weight (local > inherited > global) + description keyword match + tool coverage relevance
3. Inject: top 2-3 with full `markdown_body`
4. Summarize: remaining skills as name + description only
5. Always include: `collider-workspace` global navigation skill
6. Token budget: ~2000 tokens total for all skill content

### 3.3 Harness Strategy: "Build for Deletion"

Every piece of the PI extension stack should be something you can remove when the model no longer needs it:

- `colliderPolicyExtension` — remove when models self-enforce safety
- `colliderWidgetExtension` — remove when you don't need terminal UI
- `colliderToolsExtension` — simplify if models learn to call REST directly
- `colliderContextExtension` — the last to go (context delivery is always needed)

**Test this principle**: Can you remove any single extension and still have a working (if degraded) session? If yes, the architecture is right. If no, coupling is too tight.

### 3.4 Context Engineering Strategy (from Manus Lessons)

Apply Manus's proven patterns to Collider:

1. **KV-cache optimization**: Keep tool definitions stable across turns. Don't dynamically add/remove tools — mask availability instead via the `model_invocable` flag.

2. **Task recitation**: The `collider-workspace` skill should include a "current objective" section that gets refreshed at each turn boundary. This pushes the goal into the model's recent attention.

3. **Error preservation**: Don't strip failed tool results from history. Leave them in context so the agent can learn from mistakes within the session.

4. **Filesystem as memory**: For long-running sessions (>50 tool calls), the PI extension should write intermediate results to a progress file and read it back on each turn — exactly like Anthropic recommends.

5. **JSON over Markdown for state**: The workspace context section should use structured format (tables, typed fields) rather than prose. Models are less likely to inappropriately modify structured data.

### 3.5 Team Strategy: "External Orchestration, Node-Scoped Isolation"

The `TeamManager` pattern already in NanoClawBridge is correct:
- Leader gets merged context from all composed nodes
- Members get isolated context from their assigned node only
- Communication via mailbox (direct messaging, not shared context)
- Task list with dependency tracking

**Enhancement for PI**: Add agent chains (pipelines) — sequential PI sessions where one session's output pipes into the next session's input. Implemented in `pipeline-runner.ts`.

---

## 4. Challenges

### 4.1 Contract Stability (Most Critical)

**Problem**: The existing codebase has several contract mismatches:
- Vector discovery: AgentRunner parser expects a different shape than GraphToolServer returns
- Context delta: NanoClaw SSE subscriber expects stream path/shape that doesn't match DataServer reality
- Execution config: Inconsistent service defaults in execution path
- Schema strictness: Mutable defaults (`[]`, `{}` literals) in Pydantic models

**Impact**: These mismatches create silent failures. If you build PI on top of broken contracts, you inherit the breakage.

**Solution strategy**: Fix contracts first (Strategy 3.1 "Stabilize A"). Formalize schemas with strict Pydantic validation. Add integration tests that verify contract shapes across service boundaries.

### 4.2 Skill Ranking Quality

**Problem**: With a deep node tree (e.g., `factory/ffs1/ffs2/agent-runner`), composition might produce 10-20 skills. SkillsBench says only 2-3 should get full injection. A bad ranker picks the wrong skills.

**Impact**: Wrong skills in the system prompt means the agent has guidance for tasks it's not doing and lacks guidance for tasks it is.

**Solution strategy**: Start with a simple, deterministic heuristic:
1. Local scope always outranks inherited
2. Skills whose `exposes_tools` overlap with the session's `tool_schemas` rank higher
3. Skills whose description keywords match the user's first message rank higher
4. Alphabetical tiebreak (predictable, debuggable)

Later: Add usage telemetry and refine with empirical data (which skills correlate with successful task completion).

### 4.3 PI Maturity and Maintenance Risk

**Problem**: PI is maintained by one person (Mario Zechner). The extension API could change. No native subagent or MCP support.

**Impact**: Breaking changes in PI could require adapter updates. Feature gaps must be filled by Collider extensions.

**Solution strategy**:
- Pin the PI version in `package.json` (semver lock)
- Fork if necessary (MIT license, full TypeScript source)
- Build all Collider-specific features as extensions (not patches to PI core)
- Keep the Anthropic path fully operational as fallback
- Use `pi-shadow` mode to validate before switching any production traffic

### 4.4 Event Parity Between Runtimes

**Problem**: The WS bridge (`ws-bridge.ts`) and all frontend consumers expect specific event shapes (`text_delta`, `tool_start`, `tool_result`, `message_end`, `error`). PI's streaming callbacks have a different internal format.

**Impact**: If PI adapter events don't match Anthropic adapter events exactly, the frontend breaks.

**Solution strategy**: Define `AgentEvent` as the canonical contract (already exists in `event-parser.ts`). Both adapters must emit events in this exact shape. Add a parity test suite that feeds the same input to both adapters and asserts identical event streams.

### 4.5 Token Budget Enforcement

**Problem**: The ~2000 token skill budget is a soft guideline. If `buildWorkspaceContext()` exceeds it, the system prompt bloats and model performance degrades (per SkillsBench: comprehensive skills hurt by -2.9pp).

**Impact**: Subtle quality degradation that's hard to detect without benchmarking.

**Solution strategy**: Implement a hard token budget in the prompt builder:
1. Count tokens for each section (using tiktoken or a simple heuristic: 1 token ~ 4 chars)
2. If total exceeds budget, truncate remaining skills to name+description
3. Never drop `collider-workspace` (global navigation)
4. Log a warning when truncation occurs
5. Add telemetry: track actual token counts per session for optimization

### 4.6 gRPC Proto Versioning

**Problem**: Adding fields 20-28 to `SkillChunk` in the proto is backward compatible (proto3 defaults), but all consumers (context service, seeder, prompt builder, context client) must understand the new fields.

**Impact**: Partial deployment (some services updated, some not) could cause silent field drops.

**Solution strategy**: Phase the rollout:
1. Add fields to proto and regenerate — all services still work (new fields default to empty)
2. Update Python side (DataServer schemas, AgentRunner composition) to populate new fields
3. Update TypeScript side (context-client, types, prompt-builder) to consume new fields
4. Each phase is independently testable

### 4.7 Namespace + Version Aware Composition (Your Draft Section 5)

**Problem**: Current leaf-wins is name-only (`{skill.name -> definition}`). Your draft proposes namespace + version aware precedence.

**Impact**: Without namespaces, two unrelated nodes could accidentally define a skill with the same name, and leaf-wins would silently drop one.

**Solution strategy**: Extend the merge key to `{namespace}:{name}` where namespace defaults to the source node path. Version is metadata, not merge key — latest version wins within the same namespace:name pair. This is additive to the current leaf-wins logic.

---

## 5. Solutions (Detailed)

### 5.1 The IAgentSession Interface

The runtime-agnostic contract that both adapters implement:

```typescript
interface IAgentSession {
  readonly sessionId: string;
  readonly status: "idle" | "running" | "error";

  createSession(config: SdkSessionConfig): Promise<void>;
  sendMessage(message: string): AsyncGenerator<AgentEvent>;
  injectContext(delta: ContextDelta): Promise<void>;
  terminateSession(): Promise<void>;
  getHistory(): ConversationMessage[];
}
```

`SessionManager` chooses the implementation based on `COLLIDER_AGENT_RUNTIME` env var. All downstream consumers (`ws-bridge`, `team-manager`, `db`) interact only with `IAgentSession`.

### 5.2 The PI Extension Stack (Detailed Design)

**colliderContextExtension** — The most important extension. It:
1. Receives `BootstrapResponse` from gRPC `GetBootstrap()`
2. Applies the skill ranker (Section 3.2)
3. Renders structured workspace state as system prompt addendum
4. Provides a persistent widget showing node identity
5. Handles `updateContext(delta)` calls from SSE subscriber

**colliderToolsExtension** — Maps `tool_schemas[]` to PI-native tool handlers:
1. For each schema, register a PI tool with the same name, description, and JSON Schema parameters
2. Each handler does `HTTP POST :8000/api/v1/execution/tool/{name}` with the tool arguments
3. Returns the response as a string (PI expects string results from tools)

**colliderPolicyExtension** — Lifecycle hooks for security:
1. `beforeTool`: Check tool allowlist, redact secrets from arguments
2. `beforeBash`: Check bash denylist (patterns like `rm -rf`, `DROP TABLE`)
3. `afterTool`: Write audit log entry
4. Privileged tools: Emit `requires_approval` event and wait for user confirmation

**colliderTeamLeaderExtension** — For team lead sessions:
1. Injects `team-coordinator` auto-skill describing the team structure
2. Provides `sendTask(memberId, task)` and `broadcast(message)` tools
3. Handles mailbox routing

**colliderTeamMemberExtension** — For team member sessions:
1. Provides `reportResult(content)` tool for sending results back to leader
2. Scoped to single node's skills and tools only

### 5.3 Enhanced SkillDefinition (Backward Compatible)

New fields added to the existing Pydantic model in `nodes.py`:

```
kind: SkillKind         # procedural | navigation | workflow | composite
scope: SkillScope       # local | inherited | composed | global (set at composition time)
namespace: str | None   # Defaults to source_node_path
version: str            # Semver, defaults to "1.0.0"
source_node_path: str   # "factory/ffs2/agent-runner"
source_node_id: str     # UUID of originating node
inputs: list[str]       # Semantic tags: ["ContextSet", "node_ids"]
outputs: list[str]      # Semantic tags: ["BootstrapResponse", "system_prompt"]
depends_on: list[str]   # Other skill names this requires
exposes_tools: list[str]# Tool names available through this skill
child_skills: list[str] # Skills from child nodes (for composite kind)
```

All new fields have defaults — existing container data continues to work unchanged.

### 5.4 The collider-workspace Global Meta-Skill

A single curated skill that teaches every Collider agent how to navigate the recursive graph. Lives at FFS0 root node, auto-inherited by all sessions. Content (~200 lines):

1. **The Pattern**: NodeContainer is the same type at all scales. `kind` discriminates: workspace (context), tool (execution), workflow (orchestration).
2. **Bootstrap**: `GET :8000/api/v1/agent/bootstrap/{node_id}?depth=N` — leaf-wins merge.
3. **Discovery**: `POST :8001/api/v1/registry/tools/discover` — semantic search via ChromaDB.
4. **Execution**: REST `POST :8000/api/v1/execution/tool/{name}` — the universal tool endpoint.
5. **Navigation**: Ancestor chain, children, full tree traversal.

This skill is NOT comprehensive documentation. It's procedural — "here's how to DO things in Collider."

### 5.5 Contract Stabilization Fixes

Before PI integration, fix the four gaps from the draft:

1. **Vector discovery shape**: Align AgentRunner parser with GraphToolServer response format. Add a contract test.
2. **Context delta route**: Fix SSE subscriber path to match DataServer stream endpoint. Add integration test.
3. **Execution config**: Consolidate service defaults into one config source (`.env` + `servers.yaml`).
4. **Schema strictness**: Replace mutable literals with `Field(default_factory=list)` / `Field(default_factory=dict)` in all Pydantic models.

---

## 6. Difficulties & Risk Mitigation

### 6.1 Difficulty: You're Building an OS, Not an App

The harness metaphor (harness = operating system, model = CPU, agent = application) means you're in systems programming territory. Context management, process isolation (team members), resource scheduling (token budgets), and inter-process communication (mailbox) are all OS-level concerns.

**Mitigation**: Keep the OS thin. PI's 200-token base prompt is the right philosophy. Let the model be smart; let the harness be simple. Every line of harness code is technical debt that must be maintained as models evolve.

### 6.2 Difficulty: Dual Runtime Maintenance

Running both Anthropic and PI runtimes means maintaining two code paths.

**Mitigation**: The `IAgentSession` interface keeps the dual paths thin. Both adapters are ~400 lines each. The shared infrastructure (gRPC client, SSE subscriber, tool executor REST calls, WS bridge, DB) is 90% of the codebase and stays unified.

### 6.3 Difficulty: Skill Authoring UX

Today, skills are authored as `.agent/skills/*.md` files and seeded into the DB. But the new graph-aware fields (`kind`, `scope`, `inputs`, `outputs`, `depends_on`, `exposes_tools`) are hard to author by hand.

**Mitigation**:
- Most fields are computed at composition time (scope, source_node_path, source_node_id)
- `kind` defaults to `procedural` (the common case)
- `inputs/outputs/depends_on/exposes_tools` are optional metadata — start without them, add as value is proven
- The Chrome Extension WorkspaceBrowser could eventually provide a skill editor UI

### 6.4 Difficulty: Testing Agent Behavior

How do you test that an agent WITH skills performs better than WITHOUT? SkillsBench exists, but it tests generic tasks, not Collider-specific workflows.

**Mitigation**: Build a Collider-specific evaluation suite:
- 5-10 representative tasks ("create a node under FFS2", "discover tools for graph navigation", "execute a workflow")
- Run each task with and without skills
- Measure: task completion rate, token usage, tool call accuracy
- Automate as a CI job (using PI programmatic mode)

### 6.5 Difficulty: The "Lost-in-the-Middle" Problem

Manus found that after ~50 tool calls, the model loses track of its objectives. Important instructions from the beginning of the context get buried under intermediate results.

**Mitigation**: Apply Manus's "task recitation" pattern:
- The `colliderContextExtension` prepends a "Current Objective" section to the system prompt addendum
- This section is refreshed at each turn boundary
- The global `collider-workspace` skill sits at the end of the skills section (recent attention bias)
- Use PI's `compact` mechanism when context grows beyond 80% of the window

---

## 7. Implementation Phases (Detailed Roadmap)

### Phase 0: Contract Stabilization (3-5 days)

**Goal**: Fix the four contract mismatches before building anything new.

| Task                                                       | File(s)                                             | Effort   |
| ---------------------------------------------------------- | --------------------------------------------------- | -------- |
| Fix vector discovery shape mismatch                        | `runner.py`, GraphToolServer registry API           | 1 day    |
| Fix context delta SSE route                                | `context-subscriber.ts`, DataServer stream endpoint | 1 day    |
| Consolidate execution config defaults                      | `.env` files, `servers.yaml`, AgentRunner settings  | 0.5 day  |
| Replace mutable literals with `Field(default_factory=...)` | `nodes.py`, `agent_bootstrap.py`, `context_set.py`  | 0.5 day  |
| Add contract integration tests                             | New test files in each service                      | 1-2 days |

**Exit gate**: All contract tests pass. Vector discovery returns correct shapes. SSE deltas flow end-to-end.

### Phase 1: Enhanced Data Models (1-2 days)

**Goal**: Add graph-aware fields to SkillDefinition and create ContainerSkillView.

| Task                                                          | File(s)                               | Effort  |
| ------------------------------------------------------------- | ------------------------------------- | ------- |
| Add `SkillKind`, `SkillScope` enums                           | `nodes.py`                            | 0.5 day |
| Add graph-aware fields to `SkillDefinition`                   | `nodes.py`                            | 0.5 day |
| Update `AgentSkillEntry` with new fields                      | `agent_bootstrap.py`                  | 0.5 day |
| Create `ContainerSkillView`, `ToolSummary`, `WorkflowSummary` | `skill_view.py` (NEW in AgentRunner)  | 0.5 day |
| Update seeder to populate new fields                          | `agent_walker.py`, `node_upserter.py` | 0.5 day |

**Exit gate**: Seeder produces containers with graph-aware skill fields. Bootstrap response includes new fields (defaulting to empty for existing data).

### Phase 2: Composition Pipeline Enhancement (2-3 days)

**Goal**: `compose_context_set()` builds `ContainerSkillView[]` with scope tracking and provenance.

| Task                                                     | File(s)                | Effort  |
| -------------------------------------------------------- | ---------------------- | ------- |
| Update composition to set `scope` and `source_node_path` | `runner.py`            | 1 day   |
| Add namespace-aware merge key (`namespace:name`)         | `runner.py`            | 0.5 day |
| Extend proto `SkillChunk` with fields 20-28              | `collider_graph.proto` | 0.5 day |
| Update `_skill_to_chunk()` to serialize new fields       | `context_service.py`   | 0.5 day |
| Update gRPC context client to parse new fields           | `context-client.ts`    | 0.5 day |

**Exit gate**: gRPC `GetBootstrap` returns skills with scope, kind, source_node_path, and exposes_tools populated.

### Phase 3: collider-workspace Meta-Skill (0.5 day)

**Goal**: Create the global navigation skill and update the seeder to support subdirectory skills.

| Task                                        | File(s)                                           | Effort   |
| ------------------------------------------- | ------------------------------------------------- | -------- |
| Create `collider-workspace/SKILL.md`        | `.agent/skills/collider-workspace/SKILL.md` (NEW) | 0.25 day |
| Support subdirectory skill format in seeder | `agent_walker.py`                                 | 0.25 day |

**Exit gate**: Running the seeder creates a `collider-workspace` skill at the root node. It appears in all bootstrapped sessions.

### Phase 4: IAgentSession Interface + Feature Flag (1-2 days)

**Goal**: Extract the runtime-agnostic interface from the existing Anthropic adapter.

| Task                                                              | File(s)                                | Effort  |
| ----------------------------------------------------------------- | -------------------------------------- | ------- |
| Define `IAgentSession` interface                                  | `NanoClawBridge/src/pi/types.ts` (NEW) | 0.5 day |
| Refactor `AnthropicAgent` to implement `IAgentSession`            | `anthropic-agent.ts`                   | 0.5 day |
| Add `COLLIDER_AGENT_RUNTIME` feature flag to `session-manager.ts` | `session-manager.ts`                   | 0.5 day |
| Create PI adapter skeleton                                        | `pi-adapter.ts` (NEW)                  | 0.5 day |

**Exit gate**: Both runtimes compile. Feature flag selects between them. Anthropic path unchanged.

### Phase 5: PI Context + Tools Extensions (4-6 days)

**Goal**: PI sessions can receive context from gRPC and execute Collider tools.

| Task                             | File(s)                                   | Effort   |
| -------------------------------- | ----------------------------------------- | -------- |
| Build `colliderContextExtension` | `pi/extensions/collider-context.ts` (NEW) | 2 days   |
| Build `colliderToolsExtension`   | `pi/extensions/collider-tools.ts` (NEW)   | 1-2 days |
| Build `model-resolver.ts`        | `pi/model-resolver.ts` (NEW)              | 0.5 day  |
| Build `colliderWidgetExtension`  | `pi/extensions/collider-widget.ts` (NEW)  | 0.5 day  |

**Exit gate**: PI session creates, receives structured workspace context, executes a Collider tool via REST.

### Phase 6: PI Policy + Event Parity (3-4 days)

**Goal**: PI sessions are secure and emit events matching Anthropic adapter shape.

| Task                               | File(s)                                  | Effort   |
| ---------------------------------- | ---------------------------------------- | -------- |
| Build `colliderPolicyExtension`    | `pi/extensions/collider-policy.ts` (NEW) | 2 days   |
| Implement WS event emission parity | `pi-adapter.ts`                          | 1-2 days |
| Write event parity test suite      | `test/pi/event-parity.test.ts` (NEW)     | 1 day    |

**Exit gate**: `pi-shadow` mode runs. Event streams match on 3 representative sessions.

### Phase 7: PI Team Extensions (3-4 days)

**Goal**: Multi-agent teams work with PI runtime.

| Task                                               | File(s)                                       | Effort   |
| -------------------------------------------------- | --------------------------------------------- | -------- |
| Build `colliderTeamLeaderExtension`                | `pi/extensions/collider-team-leader.ts` (NEW) | 1-2 days |
| Build `colliderTeamMemberExtension`                | `pi/extensions/collider-team-member.ts` (NEW) | 1 day    |
| Build `pipeline-runner.ts`                         | `pi/pipeline-runner.ts` (NEW)                 | 1 day    |
| Update `team-manager.ts` for `IAgentSession` union | `team-manager.ts`                             | 0.5 day  |

**Exit gate**: Team with leader + 2 members verified.

### Phase 8: Prompt Builder Upgrade (1-2 days)

**Goal**: Structured workspace state replaces flat markdown.

| Task                                                     | File(s)             | Effort  |
| -------------------------------------------------------- | ------------------- | ------- |
| Add graph-aware fields to TS `SkillDefinition`           | `types.ts`          | 0.5 day |
| Replace `formatSkills()` with `formatWorkspaceContext()` | `prompt-builder.ts` | 1 day   |
| Add token budget enforcement                             | `prompt-builder.ts` | 0.5 day |

**Exit gate**: System prompt contains structured workspace context.

### Phase 9: Shadow Traffic + Validation (2-3 days)

| Criteria             | Target                           |
| -------------------- | -------------------------------- |
| Event parity         | >=99%                            |
| Task completion rate | Within 10% of Anthropic baseline |
| Tool error rate      | Within 5%                        |
| Token usage delta    | Within 15%                       |
| Policy bypasses      | Zero critical                    |

**Total: ~5-7 weeks (one engineer), ~3-4 weeks (two engineers)**

---

## 8. Answers to Open Decisions

### Q1: One-way `.agent` -> DB sync only, or bidirectional?

**Answer: One-way only for now.** DB is runtime truth. Export explicitly if needed.

### Q2: Should root/global skills be overrideable?

**Answer: Yes, with optional `protected: true` flag.** Leaf-wins is the default. `collider-workspace` sets `protected: true`.

### Q3: Strict validation at ingestion?

**Answer: Strict at seeder time.** `--permissive` flag for development.

### Q4: Is `pi-shadow` mandatory?

**Answer: Yes.** At least 20 sessions before switching any traffic.

---

## 9. Verification Plan

### Unit Tests
Each schema model, extension, and adapter method gets tests.

### Integration Tests

| Test                              | Services                     | Assertion                                 |
| --------------------------------- | ---------------------------- | ----------------------------------------- |
| Bootstrap with graph-aware skills | DataServer + AgentRunner     | Skills have scope, kind, source_node_path |
| Composition with ancestors        | DataServer + AgentRunner     | Ancestor = inherited, local = local       |
| PI session tool execution         | NanoClawBridge + DataServer  | Tool returns correct result               |
| Team creation with PI             | NanoClawBridge + AgentRunner | Leader = merged, members = isolated       |

### E2E Smoke Test
```bash
uv run python -m sdk.seeder.cli --root D:/FFS0_Factory --app-id c57ab23a-...
# Start services, create session, connect WS, verify events
# Repeat with COLLIDER_AGENT_RUNTIME=pi
```

---

## 10. Key References

### Research
- [SkillsBench (arXiv:2602.12670)](https://arxiv.org/abs/2602.12670)
- [Manus Context Engineering](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus)
- [Anthropic: Effective Harnesses](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- [OpenAI: Harness Engineering](https://openai.com/index/harness-engineering/)
- [Phil Schmid: Agent Harness 2026](https://www.philschmid.de/agent-harness-2026)

### Standards
- [Agent Skills Specification](https://agentskills.io/specification)
- [Claude Code Agent Teams](https://code.claude.com/docs/en/agent-teams)

### Tools
- [PI Agent Harness](https://github.com/badlogic/pi-mono)
- [NanoClaw](https://github.com/qwibitai/nanoclaw)
- [PydanticAI](https://github.com/pydantic/pydantic-ai)

### Collider Architecture Docs
- `skills-architecture.md` — Option A (SDK/gRPC)
- `skills-architecture-alternative.md` — Option B (Native MCP)
- `skills-architecture-pi.md` — Option C (PI Runtime)
- `collider-skills-runtime-integration-draft.md` — Strategic decisions

---

## 11. Summary

**Graph is truth. Skills are interface. Runtime is pluggable.**

The NodeContainer recursive model already holds everything an agent needs. Skills are thin, computed views that help agents understand what a workspace IS, CAN DO, and should PRODUCE. The PI runtime gives full control over the harness while keeping the model-agnostic philosophy. The Anthropic SDK path remains as a parallel option.

Implementation is phased over 9 phases. Each phase has clear exit gates. Contract stabilization comes first, then data models, then PI integration, then validation.

The architecture is designed for deletion. As models get smarter, the harness gets simpler. Every extension can be removed when the model no longer needs it. This is the Bitter Lesson applied to agent infrastructure.

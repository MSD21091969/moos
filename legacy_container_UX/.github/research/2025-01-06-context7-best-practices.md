# Context7 Research: Best Practices for Composite Container Patterns

**Date:** 2025-01-06  
**Stack:** React + Zustand + ReactFlow (Frontend) | FastAPI + Pydantic (Backend)  
**Architecture:** Universal Object Model V4.1 with ResourceLink composite patterns

---

## Executive Summary

Our architecture uses **composite container patterns** where:
- **Containers** (Session, Agent, Tool) hold ResourceLinks to other objects
- **Dependencies** are expressed via `input_mappings` (data wiring)
- **State persistence** uses Zustand + localStorage
- **Visual state** is stored in `ResourceLink.metadata` (x, y, color)

This research covers best practices from Zustand, ReactFlow, Pydantic-AI, and LangGraph that directly apply to our patterns.

---

## 1. Zustand State Persistence (Our Stack)

### Key Findings

**Deep Merge for Nested State** — Critical for `ResourceLink.metadata`:
```typescript
// PROBLEM: Shallow merge loses nested fields
// localStorage has { position: { y: 100 } } but no x
// Shallow merge results in { position: { y: 100 } } — x lost!

// SOLUTION: Use deep merge
import createDeepMerge from '@fastify/deepmerge'
const deepMerge = createDeepMerge({ all: true })

export const useWorkspaceStore = create<WorkspaceState>()(
  persist(
    (set) => ({ /* state */ }),
    {
      name: 'workspace-storage',
      merge: (persisted, current) => deepMerge(current, persisted) as never,
    },
  ),
)
```

**Partialize for Performance** — Only persist what matters:
```typescript
persist(
  (set, get) => ({ /* state */ }),
  {
    partialize: (state) => ({
      sessions: state.sessions,
      resources: state.resources,
      viewport: state.viewport,
      // Exclude: selectedNodeIds, dragState, etc.
    }),
  },
)
```

**Version Migration** — Handle schema evolution:
```typescript
persist(
  (set, get) => ({ /* state */ }),
  {
    version: 2, // Increment when schema changes
    migrate: (persisted, version) => {
      if (version === 1) {
        // V1 → V2: Move position from node to ResourceLink.metadata
        persisted.resources = persisted.resources.map(r => ({
          ...r,
          metadata: { ...r.metadata, x: r.x, y: r.y }
        }))
      }
      return persisted
    },
  },
)
```

**Hydration Awareness** — Handle SSR/reload timing:
```typescript
const useHydration = () => {
  const [hydrated, setHydrated] = useState(false)
  useEffect(() => {
    const unsub = useWorkspaceStore.persist.onFinishHydration(() => 
      setHydrated(true)
    )
    setHydrated(useWorkspaceStore.persist.hasHydrated())
    return unsub
  }, [])
  return hydrated
}
```

### Relevance to Our Issues
- **Position persistence after F5** → Deep merge ensures `metadata.x` and `metadata.y` survive
- **Session count mismatch** → Partialize prevents stale state pollution
- **Demo mode hydration** → Check `hasHydrated()` before rendering

---

## 2. ReactFlow State & Custom Nodes (Our Stack)

### Key Findings

**Custom Node Types Must Be Stable**:
```typescript
// ❌ WRONG: Defined inside component — causes re-renders
function Canvas() {
  const nodeTypes = { session: SessionNode } // Re-created every render!
  return <ReactFlow nodeTypes={nodeTypes} />
}

// ✅ CORRECT: Defined outside component
const nodeTypes = { session: SessionNode, agent: AgentNode, tool: ToolNode }
function Canvas() {
  return <ReactFlow nodeTypes={nodeTypes} />
}
```

**Position Updates via `onNodesChange`**:
```typescript
const onNodesChange = useCallback((changes) => {
  // Filter for position changes only
  const positionChanges = changes.filter(c => c.type === 'position')
  if (positionChanges.length > 0) {
    // Update ResourceLink.metadata in Zustand
    positionChanges.forEach(change => {
      updateResourceLinkMetadata(change.id, {
        x: change.position?.x,
        y: change.position?.y,
      })
    })
  }
  // Let ReactFlow handle internal state
  setNodes((nds) => applyNodeChanges(changes, nds))
}, [])
```

**Context Menu Positioning** (Our issue today):
```typescript
const onNodeContextMenu = useCallback((event, node) => {
  event.preventDefault()
  const pane = ref.current.getBoundingClientRect()
  setMenu({
    id: node.id,
    // Prevent off-screen positioning
    top: event.clientY < pane.height - 200 && event.clientY,
    left: event.clientX < pane.width - 200 && event.clientX,
    right: event.clientX >= pane.width - 200 && pane.width - event.clientX,
    bottom: event.clientY >= pane.height - 200 && pane.height - event.clientY,
  })
}, [])
```

**Viewport Persistence**:
```typescript
// Store viewport in Zustand
const onMoveEnd = useCallback((event, viewport) => {
  // Debounce this to avoid excessive writes
  setViewport({ x: viewport.x, y: viewport.y, zoom: viewport.zoom })
}, [])

// Restore on mount
const { x, y, zoom } = useWorkspaceStore(s => s.viewport)
<ReactFlow defaultViewport={{ x, y, zoom }} onMoveEnd={onMoveEnd} />
```

### Relevance to Our Issues
- **Drag persistence** → `onNodesChange` → Zustand → localStorage
- **Context menu mode awareness** → Check `activeContainerId` before showing options
- **Zoom/pan after F5** → `defaultViewport` from persisted state

---

## 3. Pydantic-AI Dependency Injection (Backend Pattern Reference)

### Key Findings

**Dependencies as Dataclass** — Our `ResourceLink.preset_params` follows this:
```python
@dataclass
class MyDeps:
    api_key: str
    http_client: httpx.AsyncClient

agent = Agent('openai:gpt-5', deps_type=MyDeps)

@agent.tool
async def get_data(ctx: RunContext[MyDeps]) -> str:
    # Access deps via ctx.deps
    return await ctx.deps.http_client.get(...)
```

**Agent Delegation with Usage Tracking** — Our nested containers follow this:
```python
# Parent agent delegates to child agent
@parent_agent.tool
async def delegate_to_child(ctx: RunContext[Deps], task: str) -> str:
    result = await child_agent.run(
        task,
        deps=ctx.deps,      # Pass dependencies down
        usage=ctx.usage,    # Track usage across hierarchy
    )
    return result.output
```

**Conditional Tool Inclusion** — Maps to our tier-gated depth:
```python
async def only_if_pro_tier(ctx: RunContext[User], tool_def: ToolDefinition):
    if ctx.deps.tier in ('PRO', 'ENTERPRISE'):
        return tool_def
    return None  # Tool not available for FREE tier

@agent.tool(prepare=only_if_pro_tier)
def deep_analysis(ctx: RunContext[User]) -> str:
    # Only PRO/ENT users can use this
    pass
```

### Relevance to Our Architecture
- **ResourceLink.preset_params** → Agent/Tool configuration (like `deps`)
- **ResourceLink.input_mappings** → Data wiring between containers (like `ctx.deps`)
- **Tier-gated depth** → Conditional tool/container availability

---

## 4. LangGraph State & Workflows (Architecture Reference)

### Key Findings

**StateGraph with TypedDict** — Matches our container state model:
```python
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

class ContainerState(TypedDict):
    resources: Annotated[list, add_resources]  # Reducer for ResourceLinks
    messages: Annotated[list, add_messages]
    depth: int
    parent_id: str | None

graph = StateGraph(ContainerState)
```

**Conditional Edges** — Our navigation patterns:
```python
def should_dive_or_ascend(state: ContainerState) -> str:
    if state['action'] == 'dive' and state['depth'] < MAX_DEPTH:
        return 'dive_node'
    elif state['action'] == 'ascend' and state['parent_id']:
        return 'ascend_node'
    return END

graph.add_conditional_edges('router', should_dive_or_ascend)
```

**Supervisor Pattern** — Our Session orchestrating Agents/Tools:
```python
def supervisor(state: State) -> Command[Literal["agent_1", "agent_2", END]]:
    # Determine which agent to route to
    response = model.invoke(state["messages"])
    return Command(goto=response["next_agent"])

graph.add_node("supervisor", supervisor)  # Session
graph.add_node("agent_1", agent_1)        # Agent ResourceLink
graph.add_node("agent_2", agent_2)        # Another Agent
graph.add_edge(START, "supervisor")
```

**Parallel Execution** — Fan-out to multiple ResourceLinks:
```python
# Send tasks to multiple workers in parallel
def assign_workers(state: State):
    return [Send("worker", {"task": t}) for t in state["tasks"]]

graph.add_conditional_edges("orchestrator", assign_workers)
```

### Relevance to Our Architecture
- **StateGraph** → Our container hierarchy with depth tracking
- **Conditional edges** → Dive/ascend navigation based on ACL and tier
- **Supervisor pattern** → Session as orchestrator of Agents/Tools
- **Send API** → Parallel execution of multiple ResourceLinks

---

## 5. Composite Container Best Practices Summary

### Data Flow Pattern
```
Session (L2)
├── Agent (L3) ──────────────────┐
│   ├── preset_params: {...}     │
│   ├── input_mappings: {        │
│   │     "context": "$session.context"  ← Data wiring
│   │   }                        │
│   └── Tool (L4)                │
│       └── input_mappings: {    │
│             "data": "$agent.output"    ← Chain dependency
│           }                    │
└── Source (L3)                  │
    └── (Terminal - no children) │
```

### Key Principles

1. **Depth as State** — Track depth in both backend (Firestore) and frontend (Zustand)
2. **ResourceLink as Edge** — Think of ResourceLinks as edges in a graph, not just references
3. **Metadata for Visual State** — Keep x, y, color in `metadata`, not in separate collections
4. **input_mappings for Data Flow** — Express dependencies declaratively, resolve at runtime
5. **Tier-Gated Operations** — Check user tier before allowing dive, add, or modify at depth

### Anti-Patterns to Avoid

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| Shallow merge on hydration | Loses nested `metadata` fields | Use `@fastify/deepmerge` |
| nodeTypes inside component | Causes infinite re-renders | Define outside component |
| Direct position in node.data | Duplicates state, sync issues | Store in `ResourceLink.metadata` |
| Polling for state sync | Wasteful, race conditions | Use `onNodesChange` callback |
| Hard-coded depth limits | Not tier-aware | Dynamic limit from user.tier |

---

## 6. Implementation Checklist

### Already Implemented ✅
- [x] Zustand persist middleware with localStorage
- [x] Custom node types for Session, Agent, Tool, Source
- [x] ResourceLink model with metadata field
- [x] Depth tracking in containers
- [x] Tier-gated depth limits (FREE: L2, PRO/ENT: L4)

### Should Verify/Add 🔍
- [ ] Deep merge on hydration (check if using `@fastify/deepmerge`)
- [ ] nodeTypes defined outside component
- [ ] Position changes flow: ReactFlow → Zustand → localStorage
- [ ] Viewport persistence with debounce
- [ ] Context menu respects `activeContainerId` for mode

### Future Considerations 📋
- [ ] input_mappings resolver for runtime data wiring
- [ ] Parallel ResourceLink execution (fan-out pattern)
- [ ] Conditional edges for tier-gated navigation
- [ ] Migration strategy for schema version bumps

---

## References

- **Zustand Persist**: https://github.com/pmndrs/zustand/blob/main/docs/integrations/persisting-store-data.md
- **ReactFlow Custom Nodes**: https://reactflow.dev/learn/customization/custom-nodes
- **ReactFlow State Management**: https://reactflow.dev/learn/advanced-use/state-management
- **Pydantic-AI Dependencies**: https://github.com/pydantic/pydantic-ai/blob/main/docs/dependencies.md
- **LangGraph Multi-Agent**: https://github.com/langchain-ai/langgraph/blob/main/docs/docs/concepts/multi_agent.md
- **Microsoft Agent Framework**: https://github.com/microsoft/agent-framework

---

**Next Action:** Review implementation checklist and verify deep merge is enabled in workspace-store.ts

# ChatAgent Context: ColliderSpace Front-to-Back Reference

Purpose: concise tables for ChatAgent grounding across UX (ReactFlow), Zustand state, HTTP API (OpenAPI), backend services/models, plus a short flow diagram.

**Last Updated:** 2025-12-07 (Terminology Alignment + Collider Bridge Protocol)

---

## 3-Layer Terminology Mapping

**CRITICAL:** ChatAgent must use **Screen/UX vocabulary** when describing what user sees. Backend terminology is for API calls only.

| Screen/UX (User Sees) | Frontend/Zustand (Code) | Backend API (HTTP) |
| --- | --- | --- |
| **sticky note** / **sticky** | `ContainerVisualState` (containerType='session') | `Session` |
| **agent card** | `ContainerVisualState` (containerType='agent') | `AgentInstance` |
| **tool card** | `ContainerVisualState` (containerType='tool') | `ToolInstance` |
| **data source** | `ContainerVisualState` (containerType='source') | `SourceInstance` |
| **canvas** | `nodes[]` (ReactFlow) | N/A |
| **workspace** | `containers[]` + `nodes[]` | `UserSession` |
| **item on canvas** | `CustomNode` | `ResourceLink` |
| **connection / wire** | `CustomEdge` | `ResourceLink.input_mappings` |
| **inside / open** | `loadContainer(id)` | GET `/sessions/{id}/resources` |
| **back / up** | `loadContainer(null)` | breadcrumb navigation |

### ChatAgent Speaking Rules
- ✅ "You have **5 sticky notes** on the canvas"
- ✅ "Inside **Trip to Santorini**, I see 1 agent and 2 tools"
- ✅ "Let me **open** the Data Analyst agent"
- ❌ "You have 5 containers in the workspace" (backend speak)
- ❌ "Loading session resources..." (implementation detail)

### User Preferences (Future)
| User | Display Name | Agent Name | Vocabulary |
| --- | --- | --- | --- |
| enterprise@test.com | Sam | HAL | sticky notes / stickies |

---

## Collider Bridge (DEV Only)
| Item | Values / Rules |
| --- | --- |
| Purpose | Bidirectional Copilot ↔ Host communication for live testing |
| Activation | `import.meta.env.DEV` only (disabled in production) |
| Window object | `window.__colliderBridge: { inbox, outbox, ready, version }` |
| Files | `lib/chat/collider-bridge.ts` (types), `lib/chat/collider-bridge-executor.ts` (handlers) |
| Polling | 500ms when `ready === true` |
| Console tags | `[BRIDGE→HOST]` (processing), `[BRIDGE_RESULT]` (result with ✅/❌) |

### Bridge Commands
| Command | Params | Returns |
| --- | --- | --- |
| `ping` | — | `{ pong: true, timestamp }` |
| `navigate_into` | `nodeId` | `{ url, pathname }` |
| `navigate_back` | — | `{ url }` |
| `open_context_menu` | `nodeId` | `{ menuVisible }` |
| `click_menu_item` | `text` | `{ clicked, text }` |
| `assert_url` | `pattern`, `exact?` | `{ url, passed }` or throws |
| `assert_breadcrumb` | `contains?`, `notContains?` | `{ breadcrumbText, passed }` or throws |
| `assert_node_visible` | `nodeId` | `{ visible, nodeId }` or throws |
| `assert_menu_item` | `text`, `visible?`, `disabled?` | `{ found, disabled, passed }` or throws |
| `assert_nodes_count` | `count?`, `min?`, `max?` | `{ count, passed }` or throws |
| `capture_state` | — | `{ activeSessionId, nodesCount, breadcrumbs, url, ... }` |
| `get_nodes` | — | `[{ id, type, label }, ...]` |
| `wait` | `ms` | `{ waited: ms }` |

### Copilot Usage (browser_evaluate)
```javascript
// Inject command
window.__colliderBridge.inbox.push({
  id: 'test_1', command: 'navigate_into',
  params: { nodeId: 'session-2' }, timestamp: Date.now()
});

// Read results
const results = window.__colliderBridge.outbox.filter(r => !r._read);
results.forEach(r => r._read = true);
```

### Result Format
```typescript
{ id, command, success, data?, error?, duration, snapshots?, timestamp }
```
On failure, `snapshots` includes `{ activeSessionId, nodesCount, breadcrumbs, url }` for debugging.

---

## UOM Rules (ARCHITECTURE_V4)
| Item | Values / Rules |
| --- | --- |
| Containers | UserSession (root), Session, Agent, Tool |
| Terminal nodes | Source (data endpoint), User (ACL reference), Introspection (socket) |
| Non-containers | User (ACL), Introspection (socket) |
| ResourceLink `resource_type` | session \| agent \| tool \| source \| user \| introspection |
| Depth & tiers | FREE: max depth 1 (L2); PRO/ENT: max depth 3 (L4). If new_depth == max+1 → only SOURCE allowed; >max+1 rejected. |
| Containment | UserSession → Sessions only; Source/User cannot contain resources/containers. |
| Terminal rule | Source and User are terminal - cannot navigate into, cannot have children. |
| ACL | Edit: owner/editor; Delete: owner (except owner USER links); View: viewers+. |

## Terminal Node Behavior (Frontend)
| Node Type | Context Menu | Double-Click | Can Add Children |
| --- | --- | --- | --- |
| Session | Open, Edit, Duplicate, Delete | ✅ Navigate into | ✅ Agent, Tool, Source |
| Agent | Open, Edit, Duplicate, Delete | ✅ Navigate into | ✅ Tool, Source |
| Tool | Open, Edit, Duplicate, Delete | ✅ Navigate into | ✅ Source only |
| Source | Edit Source, Delete | ❌ No action (terminal) | ❌ Terminal |
| User | Disabled "User (System-Defined)" | ❌ No action (terminal) | ❌ Terminal (ACL via parent) |

## Backend Endpoints (OpenAPI)
| Path | Verb | Purpose | Key params/payload | Depth/Tier/ACL Notes |
| --- | --- | --- | --- | --- |
| `/health`, `/ready` | GET | Liveness/readiness | — | Ops/Cloud Run |
| `/usersessions` | POST | Create root usersession | metadata, ACL | Owner; depth 0 |
| `/usersessions/{id}` | GET | Get usersession | id | Owner |
| `/usersessions/{id}/resources` | GET | List USER+SESSION links | id | Owner |
| `/sessions` | POST | Create Session | metadata, ACL, parent_id?, ttl/status | Depth validate; auto link to parent |
| `/sessions` | GET | List sessions | status, tags, owner | Tier/ACL filtered |
| `/sessions/{id}` | GET/PATCH/DELETE | CRUD session | patch metadata/status/ttl | Delete owner-only; ACL |
| `/sessions/{id}/resources` | GET | List links in session | — | Editor+ |
| `/sessions/{id}/resources` | POST | Add link to session | ResourceLink body | Only SOURCE at max+1 |
| `/sessions/{id}/resources/{link_id}` | PATCH/DELETE | Update/remove link | — | Editor+/owner delete |
| `/containers/{type}` | POST | Create agent/tool/source instance | type ∈ agent\|tool\|source; body includes parent_id | Depth/containment; Source terminal; auto link to parent |
| `/containers/{type}/{id}` | GET/PATCH/DELETE | CRUD container | — | Delete owner-only; ACL |
| `/containers/{type}/{id}/resources` | GET | List child links | — | Editor+ |
| `/containers/{type}/{id}/resources` | POST | Add link in container | ResourceLink body | Only SOURCE at max+1; Source cannot host |
| `/containers/{type}/{id}/resources/{link_id}` | DELETE | Remove link | — | Editor+ |
| `/resource-links` | POST | Add ResourceLink (generic) | link body | Same validations |
| `/resource-links/{link_id}` | PATCH/DELETE | Update/remove link | — | Editor+/owner |
| `/resources/tools` | GET | Discover tools | tier/search/tags | Registry + user/session |
| `/resources/agents` | GET | Discover agents | tier/search/tags | Registry + user/session |
| `/definitions/{agents|tools|sources}` | GET/POST | List/Create definitions | filters tier/tags/search | Admin/system+user |
| `/definitions/{agents|tools|sources}/{id}` | GET | Get definition | id | — |
| `/query/resources` | POST | Find resources | filter (type, tags, tier), scope (SESSION, SUBTREE) | Tier filtered |
| `/query/traverse` | POST | Traverse graph | start_id, path, max_depth | Tier depth limits (Free=1, Pro=3) |
| `/query/batch` | POST | Batch operations | operation (DELETE), items (parent_id, link_id) | ACL verified per item |

## Backend Models (Pydantic Reference)

### Core Containers & Links
```python
class ResourceType(str, Enum):
    SESSION = "session"
    AGENT = "agent"
    TOOL = "tool"
    SOURCE = "source"
    USER = "user"
    INTROSPECTION = "introspection"

class ResourceLink(BaseModel):
    """Universal connector for session/container resources."""
    link_id: str | None = Field(None, description="{type}_{resource_id}_{suffix}")
    resource_id: str = Field(..., description="Definition ID or Direct ID")
    resource_type: ResourceType
    instance_id: str | None = Field(None, description="Container instance ID")
    
    # Context & Config
    description: str | None
    role: str | None
    preset_params: dict[str, Any] = Field(default_factory=dict)
    input_mappings: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)  # UI: x, y, color
    
    # Audit
    added_at: datetime
    added_by: str
    enabled: bool = True

class ContainerBase(BaseModel):
    """Base for Agent, Tool, Source, Session instances."""
    instance_id: str
    parent_id: str | None
    depth: int  # 0=UserSession, 1-4=nested
    acl: dict[str, str | list[str]]  # {owner, editors, viewers}
    created_by: str

class SessionMetadata(BaseModel):
    title: str
    description: str | None
    tags: list[str]
    session_type: SessionType
    ttl_hours: int
    domain: str | None
    scenario: str | None
    is_container: bool
    child_node_ids: list[str]
    visual_metadata: dict
    theme_color: str | None
```

### Query & Batch Operations
```python
class QueryScope(str, Enum):
    WORKSPACE = "workspace"
    SESSION = "session"
    CHILDREN = "children"
    SUBTREE = "subtree"

class ResourceIdentifier(BaseModel):
    parent_id: str
    parent_type: str
    link_id: str

class BatchOperationType(str, Enum):
    DELETE = "delete"

class BatchOperationRequest(BaseModel):
    operation: BatchOperationType
    items: List[ResourceIdentifier]

class GraphTraversalQuery(BaseModel):
    start_node_id: str
    path: str | None
    max_depth: int
    direction: Literal["down", "up"]
```

### Definitions (Templates)
```python
class ObjectDefinition(BaseModel):
    """Base for Agent/Tool/Source Definitions."""
    id: str
    title: str
    description: str | None
    min_tier: Literal["FREE", "PRO", "ENTERPRISE"]
    acl: dict
    tags: list[str]
    category: str | None
    enabled: bool

class InputSpec(BaseModel):
    type: str
    required: bool
    default: Any | None
    description: str | None
    validation: dict
```

## Backend Constraints (services/models)
| Concern | Rules / Behavior |
| --- | --- |
| Depth map | FREE maxDepth=1 (L2); PRO/ENT maxDepth=3 (L4); only SOURCE at max+1; >max+1 blocked. |
| Containment | UserSession → Sessions only; Source/User cannot contain anything. |
| Terminal | Source and User are terminal - `TerminalNodeError` raised if violated. |
| ACL | Edit: owner/editor; Delete: owner (except owner USER links - system-defined); View: viewers+. |
| IDs | `sess_`, `agent_`, `tool_`, `source_`, `rsrc_` (ResourceLink). |
| Side effects | Creating session/container auto-adds ResourceLink to parent; session creation updates parent.child_sessions; resources stored as subcollections. |
| Registry filters | Requires tier, may require admin, allowed_user_ids, enabled flag; merges system + user/session definitions. |
| Firestore layout | Collections: `usersessions`, `sessions`, `agent_definitions`, `tool_definitions`, `source_definitions`, `agent_instances`, `tool_instances`, `source_instances`; subcollection `resources` under containers/sessions. |
| Source rule | Only SOURCE allowed at max+1 depth; Source cannot host resources. |
| User rule | USER links with role="owner" cannot be deleted (system-defined). |
| Exceptions | `TerminalNodeError` (terminal node violation), `InvalidContainmentError` (containment violation), `DepthLimitError` (tier limit). |

## Frontend: ReactFlow / Canvas
| Aspect | Behavior |
| --- | --- |
| Node types | Session, Agent, Tool, Object/Source nodes; filtered per active session. |
| Session scoping | ReactFlow view shows nodes/edges for `activeSessionId`; switches restore viewport. |
| Viewport persistence | Stored per session in `viewports`; restored on session switch. |
| Selection/layout | `setSelectedNodes`, marquee, drag locks; `applyAutoLayout` recalculates layout. |
| Canvas observer | Reads nodes/edges, selection, viewport, interactions to feed ChatAgent context. |
| Menus | Context menus opened via window event emits. |

## Frontend: Zustand Store (`workspaceStore.ts`)
| State / Cache | Notes |
| --- | --- |
| `workspace`, `sessions` map | Root and session metadata |
| Resources | `workspaceResources`, `sessionResources`, `containerResources` |
| Definitions | `agentDefinitions`, `toolDefinitions`, `sourceDefinitions` (TTL) |
| Discovery | `discoveredAgents`, `discoveredTools` (TTL) |
| UI | `viewports` per session, `selectedNodeIds`, `marquee`, `dragLocks`, `stagedOperations`, `pendingOperations` |
| Navigation | `activeSessionId`, `breadcrumbs`, `activeContainer` |

| Action | API Mapping / Effect |
| --- | --- |
| `loadWorkspaceResources` | GET `/usersessions/{id}/resources` |
| `loadSessionResources(id)` | GET `/sessions/{id}/resources` |
| `navigateAndLoad(resourceId)` | Infer type → fetch details (session or container) → set breadcrumbs/active → list resources |
| `addResourceToWorkspace` | POST ResourceLink to usersession |
| `addResourceToSession(id, link)` | POST `/sessions/{id}/resources`; refresh caches |
| `addResourceToContainer(type,id,link)` | POST `/containers/{type}/{id}/resources`; refresh |
| `updateContainer(type,id,patch)` | PATCH `/containers/{type}/{id}`; sync node |
| `updateResource(...)` | PATCH ResourceLink (session/container); optimistic update |
| `findResources(scope, query)` | POST `/query/resources` |
| `batchDeleteResources(items)` | POST `/query/batch` (DELETE) |
| Layout/selection | `setSelectedNodes`, `applyAutoLayout`, viewport save/restore |
| Navigation | `setActiveSession`, breadcrumbs push/pop |

## Frontend: API Client (`frontend/src/lib/api/client.ts`)
| Method | Endpoint |
| --- | --- |
| `getWorkspaceResources(id)` | `/usersessions/{id}/resources` |
| `getSession(id)` / `getSessionResources(id)` | `/sessions/{id}`, `/sessions/{id}/resources` |
| `createSession`, `updateSession` | `/sessions` POST, `/sessions/{id}` PATCH |
| `addResourceToSession`, `removeSessionResource` | `/sessions/{id}/resources`, `/sessions/{id}/resources/{linkId}` |
| `getContainer`, `getContainerResources` | `/containers/{type}/{id}`, `/containers/{type}/{id}/resources` |
| `createContainer`, `updateContainer` | `/containers/{type}` POST, `/containers/{type}/{id}` PATCH |
| `addResourceToContainer`, `removeResourceFromContainer` | `/containers/{type}/{id}/resources`, `/containers/{type}/{id}/resources/{linkId}` |
| Discovery | `/resources/agents`, `/resources/tools` |
| Definitions | `/definitions/{agents|tools|sources}` |
| Query | `queryResources`, `executeBatchOperation` |
| Helpers | `inferResourceType(id)`, `isContainer(type)`; auth via `auth_token` |

## ChatAgent UX Flows
| Intent | Router Action | Store/API | UI Effect |
| --- | --- | --- | --- |
| Create session | `workspace:create_session` | `createSession` → `/sessions` | New session node; viewport focus |
| Add tool/agent | `workspace:add_tool/agent` | `createContainer` or add ResourceLink | Node added/linked |
| Select nodes | `select_nodes` | `setSelectedNodes` | Highlights selection |
| Layout graph | `layout_graph` | `applyAutoLayout` | Recomputed layout |
| Switch session | `switch_session` | `setActiveSession` + load resources | Canvas scoped to session |
| Delete link/node | `delete_resource` | Remove ResourceLink (session/container) | Node/link removed |
| Observe canvas | `observe_canvas` | Reads store state | Feeds LLM context |
| Toggle voice/AI mode | UI toggle | Store flags; voice via Gemini | Mode switch |
| Open menu | Window event emit | — | Context menu opens |

## ChatAgent Tools (AI Toolkit)
| Tool Name | Purpose | Inputs | Backend Mapping |
| --- | --- | --- | --- |
| `find_resources` | Find resources in scope | `scope_id`, `resource_types`, `tags` | POST `/query/resources` |
| `traverse_graph` | Walk graph from node | `start_id`, `path`, `max_depth` | POST `/query/traverse` |
| `batch_delete_resources` | Delete multiple resources | `items` (parent_id, link_id) | POST `/query/batch` |

## Flow (text diagram)
Prompt → ChatAgent (LLM/toolcall) → Operation Router → workspaceStore action(s) → API client → FastAPI → store cache update → ReactFlow re-render → canvas observer refreshes context for next turn.

## Legend
- IDs: `sess_` (Session), `agent_`, `tool_`, `source_`, `rsrc_` (ResourceLink)
- Cache buckets: definitions (`agentDefinitions`, `toolDefinitions`, `sourceDefinitions`), discovery (`discoveredAgents`, `discoveredTools`), resources (`workspaceResources`, `sessionResources`, `containerResources`), per-session `viewports`

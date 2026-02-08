# My Tiny Data Collider - Architecture & Design

**Version:** 5.2.2
**Last Updated:** 2025-12-15
**Status:** Active

---

## 1. System Overview

**My Tiny Data Collider** is a recursive, container-based AI orchestration platform. It allows users to visually organize AI agents, tools, and data sources into nested contexts (**containers**; “Session” is one container type) to build complex workflows.

### Core Philosophy: "Everything is a Container"
The architecture is built on the **Universal Object Model (UOM)**, where every entity follows a consistent structural pattern. This symmetry simplifies both the backend logic and the frontend user experience.

### 1.1 Reality Check: Phase 1 Demo vs. Real Backend

Phase 1 (“UX/Demo”) is intentionally optimized for fast UI iteration and observability, but it can diverge from the true backend contract.

**Authoritative sources of truth (in order):**
1. **Backend validation + persistence rules** (e.g., `base_container_service.py`, `container_registry.py`).
2. **OpenAPI schema + generated frontend types** (when synced from the backend).
3. **Frontend behavior when connected to the real backend** (Phase 2).
4. **Frontend demo/mock data & mock API** (Phase 1) — useful for UX, but not authoritative for correctness.

**Implication:** if Phase 1 UX feels “wrong”, it may be:
- a frontend bug
- a spec/documentation mismatch
- or a mock-data/mock-API artifact (missing validation, inconsistent IDs, impossible graphs)

**Rule:** do not force the frontend to “behave correctly” against unreliable mock inputs. First confirm what the backend will actually validate and emit.

---

---

## 2. Universal Object Model (UOM)

### 2.1 The Container Hierarchy

The system is a tree of containers with strict containment rules enforced by `base_container_service.py`:

```python
ALLOWED_CHILDREN = {
    ContainerType.USERSESSION: {ContainerType.SESSION},
    ContainerType.SESSION: {ContainerType.SESSION, ContainerType.AGENT, ContainerType.TOOL, ContainerType.SOURCE},
    ContainerType.AGENT: {ContainerType.TOOL, ContainerType.SOURCE},
    ContainerType.TOOL: {ContainerType.SOURCE},
    ContainerType.SOURCE: set(),  # Terminal
}
```

**Spec decision point (active):** whether **SESSION** is allowed inside **AGENT/TOOL** as a “context container”.
- If yes: update `ALLOWED_CHILDREN`, UI gating, and tests together.
- If no: ensure demo/mock UX does not expose actions that create impossible graphs.
- Track the decision and evidence in `BUG_LIST.md` (Phase 1).

#### Container Types:

**L0: UserSession** (depth=0)
- **Created:** Once on first sign-in via `usersession_{user_id}`
- **Can contain:** SESSION only (via ResourceLinks)
- **Special:** USER ResourceLinks for ACL (not container instances, direct ID references)
- **Cannot contain:** AGENT, TOOL, SOURCE at workspace root
- **Purpose:** Global view of owned + shared sessions

**L1+: Session** (depth=1-3 for PRO/ENT, depth=1 for FREE)
- **Visual:** "Sticky Note" on canvas
- **Can contain:** SESSION (nested), AGENT, TOOL, SOURCE
- **Circular Dependency Prevention:** Cannot add existing SESSION as child if it creates cycle
- **No definition_id:** Sessions are "naked" containers (not templated)

**L2+: Agent** (depth=2-4)
- **Visual:** "Agent Card"
- **Can contain:** TOOL, SOURCE
- **Requires:** `definition_id` pointing to `/agent_definitions/{id}`
- **Instance:** Created from AgentDefinition template
- **Note:** Agents are always inside a Session (L1), so they start at L2 (Depth 2).

**L2+: Tool** (depth=2-4)
- **Visual:** "Tool Card"
- **Can contain:** SOURCE only
- **Requires:** `definition_id` pointing to `/tool_definitions/{id}`
- **Instance:** Created from ToolDefinition template

**Terminal: Source** (depth=2-5)
- **Visual:** Data source icon
- **Can contain:** Nothing (terminal node)
- **Requires:** `definition_id` pointing to `/source_definitions/{id}`
- **Purpose:** Data input configuration only

**Terminal: User** (not a container)
- **Purpose:** ACL member stub (ResourceLink with `role: owner|editor|viewer`)
- **No instance_id:** Uses direct user ID reference

### 2.2 Depth & Tier Limits

Enforced by `base_container_service.py` via `TIER_MAX_DEPTH`:

```python
TIER_MAX_DEPTH = {
    Tier.FREE: 1,        # depth 0-1 allowed (UserSession -> Session)
    Tier.PRO: 3,         # depth 0-3 allowed  
    Tier.ENTERPRISE: 3   # depth 0-3 allowed
}
```

| Tier | Max Container Depth | SOURCE Extension | Example Path |
|---|---|---|---|
| **FREE** | depth ≤ 1 | depth=2 for SOURCE only | UserSession(0) → Session(1) → Source(2) ✅ |
| **FREE** | depth ≤ 1 | depth=2 for AGENT/TOOL ❌ | UserSession(0) → Session(1) → Agent(2) ❌ |
| **PRO/ENT** | depth ≤ 3 | depth=4 for SOURCE only | UserSession(0) → Session(1) → Agent(2) → Tool(3) → Source(4) ✅ |

**Rule:** `child.depth = parent.depth + 1`
**Validation:** `if new_depth > max_depth + 1: DepthLimitError`
**SOURCE Exception:** At `max_depth + 1`, only SOURCE container type allowed

### 2.3 Three-Layer Architecture

The UOM separates **definitions** (templates) from **instances** (runtime containers) from **orchestration** (links).

#### Layer 1: Model Definitions (Templates)
**Firestore Collections:**
- `/agent_definitions/{definition_id}`
- `/tool_definitions/{definition_id}`  
- `/source_definitions/{definition_id}`

**Purpose:** Blueprints defining capabilities, I/O schemas, and tier gates

**Types:**
- **System Definitions:** Created by platform admin, available per tier (FREE/PRO/ENT)
- **Custom Definitions:** Created by PRO/ENT users, ACL-controlled

**Current Status:** ⚠️ **NO DEFINITIONS EXIST YET**
- Neither system nor custom definitions have been seeded
- Backend collections are empty
- This blocks all agent/tool/source creation
- Frontend has demo definitions in `demo-data.ts` but backend needs seed data

**Backend Code:**
- Models: `src/models/definitions.py` (AgentDefinition, ToolDefinition, SourceDefinition)
- Service: `src/services/definition_service.py`
- Routes: `src/api/routes/definitions.py`

#### Layer 2: Container Instances (Runtime)
**Firestore Collections:**
- `/usersessions/{instance_id}` (depth=0)
- `/sessions/{instance_id}` (depth=1+, no definition_id)
- `/agents/{instance_id}` (depth=1+, requires definition_id)
- `/tools/{instance_id}` (depth=1+, requires definition_id)
- `/sources/{instance_id}` (depth=1+, requires definition_id)

**Purpose:** Runtime containers with state, config overrides, ACL, hierarchy (parent_id, depth)

**Backend Code:**
- Models: `src/models/containers.py` (UserSession, AgentInstance, ToolInstance, SourceInstance)
- Service: `src/services/container_service.py`
- Registry: `src/services/container_registry.py`

#### Layer 3: ResourceLinks (Orchestration)
**Firestore Subcollections:**
- `/usersessions/{id}/resources/{link_id}`
- `/sessions/{id}/resources/{link_id}`
- `/agents/{id}/resources/{link_id}`
- `/tools/{id}/resources/{link_id}`

**Purpose:** Connect instances into parent containers, configure data flow

**Fields:**
- `resource_type`: session | agent | tool | source | user
- `resource_id`: Definition ID (for agent/tool/source) or direct ID (for user/session)
- `instance_id`: Container instance ID (null for user links)
- `preset_params`: Override definition defaults for THIS usage
- `input_mappings`: Connect grid edges to input slots
- `metadata`: Visual properties (x, y, color)

**Two Modes:**
1. **"Create New"** (from definition):
   - Creates fresh container instance with `definition_id`
   - Creates ResourceLink with both `resource_id` (def ID) and `instance_id` (new container)
   - User selects from available definitions

2. **"Add Existing"** (owned/shared instance):
   - Links to existing container instance via `instance_id`
   - Creates ResourceLink referencing existing container
   - User selects from containers they own or have been shared
   - **NOT "create instance from definition"** - the instance already exists

**Backend Code:**
- Model: `src/models/links.py` (ResourceLink)
- Methods: `container_registry.add_resource()`, `container_registry.list_resources()`

### 2.4 Object Taxonomy

| Layer | Type | Has `/resources/` | Can Contain | Firestore Path |
|---|---|---|---|---|
| **1 (Template)** | AgentDefinition | N/A | N/A | `/agent_definitions/{id}` |
| **1 (Template)** | ToolDefinition | N/A | N/A | `/tool_definitions/{id}` |
| **1 (Template)** | SourceDefinition | N/A | N/A | `/source_definitions/{id}` |
| **2 (Instance)** | UserSession | ✅ | SESSION | `/usersessions/{id}` |
| **2 (Instance)** | Session | ✅ | SESSION, AGENT, TOOL, SOURCE | `/sessions/{id}` |
| **2 (Instance)** | AgentInstance | ✅ | TOOL, SOURCE | `/agents/{id}` |
| **2 (Instance)** | ToolInstance | ✅ | SOURCE | `/tools/{id}` |
| **2 (Instance)** | SourceInstance | ❌ | ∅ (Terminal) | `/sources/{id}` |
| **3 (Link)** | ResourceLink | N/A | N/A | `/{parent_type}/{parent_id}/resources/{link_id}` |

---

## 3. Frontend Architecture

**Stack:** React 18, Vite, TypeScript, Zustand, ReactFlow 12.

**API client:** `frontend/src/lib/api.ts` (V5-only). The legacy V4 client has been removed to reduce drift.

### 3.1 Unified Grid Model (Link-Centric UI)
The frontend implements a "Link-First" architecture. The Grid does not render "Containers" directly; it renders **ResourceLinks**.
- A **ResourceLink** places a Container on the Grid (X, Y, Color).
- A **ResourceLink** configures the Container for this specific context (Params, Input Mappings).
- The **Container Instance** holds the execution state (Logs, Status) and identity.

**Visual Mapping:**
| UX Term (User Sees) | Frontend Component | Backend Model |
|---|---|---|
| **Grid Item** | `ContainerNode` | `ResourceLink` (Position + Config) + `Container` (State) |
| **Wire/Connection** | `CustomEdge` | `ResourceLink.input_mappings` |
| **Canvas** | `ReactFlow` Instance | `ResourceLink[]` of the Active Container |

### 3.2 State Management (Zustand)
The `useWorkspaceStore` is the single source of truth for the frontend.
*   **`containers`**: Flat list of all loaded container metadata.
*   **`nodes` / `edges`**: ReactFlow presentation state derived from `ResourceLink[]`.
*   **`activeContainerId`**: The current "view" (which container we are inside).
*   **`breadcrumbs`**: Navigation history stack.

### 3.3 Interaction Patterns
*   **Context-Aware Menus:** Menu content is a pure function of `(Context, Selection, ActiveContainer)`.
    *   **Grid Context (Right-Click on Canvas):**
        *   *Input:* `activeContainerId` (Parent).
        *   *Options:* "Add New..." (Session, Agent, Tool), "Add Existing..." (Library/Orphans), "Paste".
    *   **Object Context (Right-Click on ResourceLink):**
        *   *Input:* The specific `ResourceLink` + `Container` instance (or User Object).
        *   *Options (Container):* Open, Edit Params, Unlink (Remove), Destroy (Delete).
        *   *Options (User):* Manage Permissions, Remove Access.
    *   **Selection Context:**
        *   Multi-select enables bulk operations (e.g., "Group into Session").

*   **Navigation:** Double-clicking a container "dives" into it (`loadContainer`), fetching its `ResourceLink` list.
*   **Drag & Drop:**
    *   *Allowed:* Dropping a Tool into an Agent, or a Source into a Tool.
    *   *Blocked:* Dropping anything into a Source (Terminal).

### 3.4 Observability & UX Recording (Phase 1)

Phase 1 work is optimized for **fast, text-based UX capture** (no screenshots required) by attaching to a real Edge session via CDP.

**Runtime defaults (Demo):**
- **Vite demo port:** `5174` (`frontend: npm run dev:demo`)
- **CDP port:** `9222` (Edge launched with `--remote-debugging-port=9222`)
- **Workspace route:** `http://localhost:5174/workspace`

**Primary workflow (Option B):**
- Script: `frontend/scripts/mcp/record-ux.ts`
- Output folder: `frontend/test-results/mcp/`
- Files:
  - `ux-<timestamp>.jsonl` (event stream)
  - `ux-<timestamp>.summary.md` (run summary + counts)

The recorder captures:
- Console messages (including injected observer tags like `[CLICK]`, `[NAV]`, `[STATE]`)
- Navigation events
- Page errors
- Periodic minimal Zustand snapshots (throttled + change-detected)

**Supporting scripts (one-shot):**
- `frontend/scripts/mcp/inject-observer.ts` (injects observer)
- `frontend/scripts/mcp/poll-state.ts` (captures a point-in-time snapshot)

**Store introspection:**
For debugging, the Zustand store hook is exposed on `window.__workspaceStore` (and `window.__ZUSTAND_STORE__`). Scripts read state via `getState()`.

**VS Code tasks:**
- `🚀 Phase 1 (Demo) + 🎥 UX Recorder` is the “golden path” for repeatable UX reproduction + capture.

---

## 4. Backend Architecture

**Stack:** FastAPI, PydanticAI, Firestore (NoSQL).

### 4.1 API Design (V5)
The API mirrors the 3-layer UOM structure.

**Definitions (Layer 1):**
- `GET /api/definitions/{type}` - List available definitions (system + custom, tier + ACL filtered)
- `POST /api/definitions/{type}` - Create custom definition (PRO/ENT only)
- `GET /api/definitions/{type}/{id}` - Get definition by ID
- `PATCH /api/definitions/{type}/{id}` - Update custom definition
- `DELETE /api/definitions/{type}/{id}` - Delete custom definition

**Container Instances (Layer 2):**
- `GET /api/v5/workspace` - Fetch root UserSession
- `GET /api/v5/containers/{type}` - List containers of type (ACL-filtered)
- `POST /api/v5/containers/{type}` - Create container instance
- `GET /api/v5/containers/{type}/{id}` - Get container by ID
- `PUT /api/v5/containers/{type}/{id}` - Update container
- `DELETE /api/v5/containers/{type}/{id}` - Delete container

**ResourceLinks (Layer 3):**
- `GET /api/v5/containers/{type}/{id}/resources` - List child resources
- `POST /api/v5/containers/{type}/{id}/resources` - Add resource link
- `PATCH /api/v5/containers/{type}/{id}/resources/{link_id}` - Update link (position, metadata)
- `DELETE /api/v5/containers/{type}/{id}/resources/{link_id}` - Remove resource link

**Events:**
- `GET /api/v5/events/containers` (SSE) - Real-time container change notifications

### 4.2 Data Model (ResourceLink)
The `ResourceLink` is the fundamental connector in Layer 3. It is not just a pointer; it carries the **Functional Configuration** for the container in this specific context.

**Key Responsibilities:**
1.  **Topology:** Defines the parent-child relationship (Strict Tree).
2.  **Configuration:** `preset_params` override the Definition's defaults for this specific usage.
3.  **Data Flow:** `input_mappings` define how data flows into this container from others in the same context.
4.  **Visualization:** `metadata` stores the X/Y position and color on the parent's grid.

```python
class ResourceLink(BaseModel):
    link_id: str              # Unique within parent's /resources/
    resource_type: str        # session | agent | tool | source | user
    resource_id: str          # Definition ID or Direct ID
    instance_id: str | None   # Container instance ID (null for user)
    role: str | None          # For USER: owner/editor/viewer
    preset_params: dict       # Override definition defaults
    input_mappings: dict      # Data flow edges
    metadata: dict            # Visual state (x, y, color)
    enabled: bool
    added_at: datetime
    added_by: str
```

**Identity Pattern:**
- `resource_id`: Definition ID (agent_def_xxx, tool_def_xxx) OR Direct ID (user_xxx, session_xxx)
- `instance_id`: Points to container document in Layer 2
  - For agent/tool/source: Can be **fresh** (newly created) or **existing** (owned/shared reference)
  - For session: Same as `resource_id` (sessions have instance_id = session_id)
  - For user: Null (no container instance, direct ACL reference)

**Create New vs Add Existing:**
- **Create New**: `POST /containers/{type}` → creates instance with `definition_id`, then adds ResourceLink
- **Add Existing**: `POST /containers/{parent_type}/{parent_id}/resources` → creates ResourceLink to existing `instance_id`

### 4.3 Security & Validation
*   **Containment Rules:** Backend validates via `ALLOWED_CHILDREN` dict in `base_container_service.py`
*   **Depth Limits:** Tier-gated via `TIER_MAX_DEPTH` enforcement before creation
*   **Circular Dependencies:** `would_create_cycle()` check prevents session nesting cycles
*   **Terminal Nodes:** SOURCE containers reject child additions (empty ALLOWED_CHILDREN set)
*   **Owner Immutability:** USER ResourceLink with `role: 'owner'` cannot be deleted
*   **ACL Enforcement:** All operations check `user_can_access()`, `user_can_edit()`, `user_is_owner()`

### 4.4 Known Issues & TODOs

\u26a0\ufe0f **CRITICAL: Missing System Definitions**
- No seed data for `/agent_definitions/`, `/tool_definitions/`, `/source_definitions/`
- Without definitions, users cannot create agent/tool/source containers
- Frontend has demo definitions in `demo-data.ts` but backend needs proper seed script
- **TODO:** Create `backend/scripts/development/seed_system_definitions.py`

**Other TODOs:**
- ContainerRegistry event emission for real-time SSE updates
- Custom definition creation UI (PRO/ENT feature)
- Definition versioning and migration
- **Standalone Container Creation:** Decouple instantiation from linking. Currently, creation is architecturally coupled to resource linking, which effectively enforces a parent and depth immediately. We need to support creating "orphaned" containers (e.g., for a Library) to populate the "Add Existing" pool.

---

## 5. Integration Patterns

### 5.1 Microsoft 365 + Google Cloud Storage
*   **Flow:** External API -> Backend -> GCS (Signed URL) -> Office Online Viewer.
*   **Security:** GCS buckets are private. Access is granted via short-lived V4 Signed URLs.
*   **Viewer:** The frontend constructs the Office Online Viewer URL: `https://view.officeapps.live.com/op/view.aspx?src={signed_url}`.

---

## 6. UX/UI Design System

### 6.1 The Grid & Nodes
*   **Canvas:** Infinite grid (ReactFlow).
*   **Nodes:** Custom HTML/CSS nodes rendered via React Portals.
*   **Edges:** SVG bezier curves representing data flow (`input_mappings`).

### 6.2 Menus
*   **Context Menu:** Right-click on nodes or canvas. Dynamic based on selection type.
*   **Collapsed Menus:** To save space, complex node controls (like Agent prompt overrides) are hidden in "Edit" modals or collapsible sections within the card.

---

## 7. ChatAgent Context

The ChatAgent (AI Assistant) shares this context to understand user intent.

*   **"Open [Name]"** -> `loadContainer(id)`
*   **"Go back"** -> `navigateBack()`
*   **"What is on the canvas?"** -> Inspect `nodes[]` and `containers[]`.

**Speaking Rule:** The Agent uses UX terms ("Sticky Note", "Card") rather than backend terms ("Session", "Container") when talking to the user.

---

## 8. Registry, Caching & Event-Based Sync Architecture

### 8.1 Container Registry (`ContainerRegistry`)

**Single Source of Truth:** `backend/src/services/container_registry.py`

The `ContainerRegistry` wraps Firestore with a Redis cache layer and emits real-time events for all mutations.

**Key Features:**
- **Unified CRUD:** All container operations (register, get, update, unregister, add/remove resources)
- **Redis Cache:** 3600s TTL for container data, children lists, ACL query results
- **Event Emission:** In-memory `asyncio.Queue` (max 100) + Redis sorted set (max 1000 events) for catch-up
- **ACL Filtering:** Runs 3 separate Firestore queries per type (owner, editors, viewers), caches results per user+type

**Cache Keys:**
```python
container:{type}:{id}        # Container data
children:{id}                # Children list for a container
containers:{user_id}:{type}  # ACL-filtered containers per user+type
events:global                # Redis sorted set for event catch-up
```

**Event Model (`ContainerChanged`):**
```python
{
  "event_id": "evt_abc123",
  "timestamp": 1234567890.123,
  "container_type": "session",
  "container_id": "sess_xyz",
  "action": "created|updated|deleted|resource_added|resource_removed|acl_changed",
  "user_id": "user_123",
  "parent_id": "parent_abc",
  "data": {  # Action-specific payload
    "resource": ResourceLink,  # For resource_added
    "link_id": "link_xyz",      # For resource_removed
    "updates": {...},           # For updated
    "acl": {...}                # For acl_changed
  }
}
```

**ACL Query Strategy:**
- **Old System:** Single wide Firestore query for all containers → O(n) scan → slow, expensive
- **New System:** 3 targeted queries per type with caching:
  1. `owner == user_id` (indexed, fast)
  2. `editors array_contains user_id` (indexed, fast)
  3. `viewers array_contains user_id` (indexed, fast)
- **Result:** Cached for 3600s per user+type → drastically reduced query volume

**Cache Invalidation on Mutations:**
```python
# On register/update/unregister:
- Delete: container:{type}:{id}
- Delete: children:{parent_id}
- Delete ALL: containers:{user_id}:{type} for affected users (owner, editors, viewers)

# On add_resource/remove_resource:
- Update: container:{type}:{id} resources list
- Emit: resource_added/resource_removed event

# On ACL change:
- Delete ALL: containers:{user_id}:{type} for old AND new ACL members
- Emit: acl_changed event
```

**Code Reference:** [backend/src/services/container_registry.py](../backend/src/services/container_registry.py)

### 8.2 Frontend SSE Sync (`api-v5.ts`)

**Event-Source Based Sync:** `frontend/src/lib/api-v5.ts`

Replaces old polling/wide queries with Server-Sent Events (SSE) for real-time updates.

**Subscription Flow:**
1. **Connect:** `GET /api/v5/events/containers?token=...&since=...`
2. **Catch-Up:** Server sends missed events since `since` timestamp
3. **Live:** Server streams `ContainerChanged` events via SSE
4. **Reconnect:** Auto-reconnect with exponential backoff (max 5 retries, 3s base delay)

**Client Implementation:**
```typescript
// frontend/src/lib/api-v5.ts
subscribeToContainerEvents(onEvent, onError) {
  const eventSource = new EventSource(`/api/v5/events/containers?token=${token}&since=${lastTimestamp}`);
  
  eventSource.onmessage = (msg) => {
    const event = JSON.parse(msg.data);
    onEvent(event);
    lastTimestamp = event.timestamp; // Track for reconnect
  };
  
  eventSource.onerror = (err) => {
    onError(err);
    // Auto-reconnect logic with exponential backoff
  };
  
  return () => eventSource.close();
}
```

**Frontend Store Integration:** `frontend/src/lib/store/container-slice.ts`

```typescript
handleContainerEvent(event: ContainerChanged) {
  switch (event.action) {
    case 'resource_added':
      // 1. Update active view nodes
      // 2. Update containerRegistry cache
      
    case 'resource_removed':
      // 1. Remove from active view nodes
      // 2. Remove from containerRegistry cache
      
    case 'updated':
      // 1. Update node position + metadata in active view
      // 2. Update containerRegistry cache
      // 3. Toast if another user moved the node
      
    case 'acl_changed':
      // 1. Check if current user lost access
      // 2. If lost access to active container -> navigate to root
      // 3. Update containerRegistry cache
  }
}
```

**Container Registry (Frontend):** `store.containerRegistry`

Mirrors backend cache on frontend for instant UI updates:
```typescript
containerRegistry: {
  [containerId: string]: {
    container: Container,
    resources: ResourceLink[]
  }
}
```

**Code References:**
- [frontend/src/lib/api-v5.ts](../frontend/src/lib/api-v5.ts) - SSE subscription client
- [frontend/src/lib/store/container-slice.ts](../frontend/src/lib/store/container-slice.ts) - Event handler + registry cache

### 8.3 Definition Service (Shared Definitions)

**Definition Registry:** `backend/src/services/definition_service.py`

Handles CRUD for agent/tool/source definition templates with tier gating.

**Access Rules:**
- **System Definitions:** `created_by == null` → public, no ACL check
- **Custom Definitions:** `created_by != null` → ACL check (owner/editors/viewers)
- **Tier Gating:** `min_tier` field (free/pro/enterprise) → user tier must meet minimum

**Key Methods:**
```python
# Create custom definition (PRO/ENT only)
create_definition(definition_type, definition_data, user_id, user_tier)

# Get definition with ACL check
get_definition(definition_id, definition_type, user_id)

# List available definitions (system + custom with ACL + tier)
list_available_definitions(definition_type, user_id, user_tier)

# Update custom definition (owner/editor only)
update_definition(definition_id, definition_type, updates, user_id)

# Delete custom definition (owner only)
delete_definition(definition_id, definition_type, user_id)
```

**Shared Access Pattern:**
1. **System Definitions:** Available to all users (if tier permits)
2. **Custom Definitions:** Owner shares via ACL → viewers/editors get access → appears in `list_available_definitions()`
3. **Tier Filtering:** User tier checked against `min_tier` before returning definition

**Code Reference:** [backend/src/services/definition_service.py](../backend/src/services/definition_service.py)

### 8.4 Parent-Child Resource Sync

**ResourceLink Orchestration:** `backend/src/models/links.py`

ResourceLinks connect parent containers to child container instances.

**Sync Flow on Mutations:**
```python
# Backend: ContainerRegistry.add_resource()
1. Validate parent exists and user has edit access
2. Create ResourceLink with parent_id, resource_type, resource_id, instance_id
3. Save to parent's resources subcollection
4. Update parent's cached resources list
5. Emit resource_added event

# Frontend: handleContainerEvent('resource_added')
1. If event.container_id == activeContainerId:
   - Add node to ReactFlow canvas
2. Update containerRegistry[event.container_id].resources
3. UI instantly reflects new resource
```

**Position Sync for Collaborative Editing:**
```python
# Backend: ContainerRegistry.update_resource()
1. Update ResourceLink metadata (x, y, etc.)
2. Emit updated event with link_id + updates payload

# Frontend: handleContainerEvent('updated')
1. Find node by link_id
2. Update node.position = {x, y}
3. If event.user_id != current_user_id:
   - Toast: "Item moved by another user"
4. Update containerRegistry cache
```

**Event Granularity:** Individual resource add/remove/update → minimal payload, targeted updates

### 8.5 Backend API Routes (`v5_containers.py`)

**Unified Container API:** `backend/src/api/routes/v5_containers.py`

**Endpoints:**
```python
# Container CRUD
GET    /api/v5/containers/{type}            # List with ACL filter (cached)
POST   /api/v5/containers/{type}            # Create + emit created event
GET    /api/v5/containers/{type}/{id}       # Get (cached)
PUT    /api/v5/containers/{type}/{id}       # Update + emit updated event
DELETE /api/v5/containers/{type}/{id}       # Delete + emit deleted event

# Resource Links
GET    /api/v5/containers/{type}/{id}/resources  # List resources (cached)
POST   /api/v5/containers/{type}/{id}/resources  # Add resource + emit resource_added
DELETE /api/v5/containers/{type}/{id}/resources/{link_id}  # Remove + emit resource_removed

# Batch Operations
POST   /api/v5/containers/batch             # Batch create/update/delete

# SSE Stream
GET    /api/v5/events/containers            # Subscribe to ContainerChanged events
  ?since=<timestamp>                         # Catch-up on missed events
  ?token=<auth_token>                        # Auth via query param for EventSource

# Workspace Convenience
GET    /api/v5/workspace                    # UserSession + all resources
POST   /api/v5/workspace/sync               # Sync shared sessions to workspace
```

**Code Reference:** [backend/src/api/routes/v5_containers.py](../backend/src/api/routes/v5_containers.py)

### 8.7 Container Lifecycle: Unlink vs. Destroy vs. Move

The system distinguishes between removing a container from a session (Unlink/Orphan), permanently deleting it (Destroy), and moving it (Adopt).

**Constraint:** A container instance exists in exactly **one** location (one `parent_id`) at a time. The workspace is a strict Tree, not a Graph.

**1. Remove Resource (Unlink/Orphan)**
*   **User Action:** "Remove from Session"
*   **Endpoint:** `DELETE /api/v5/containers/{type}/{parent_id}/resources/{link_id}`
*   **Logic:**
    1.  **Delete ResourceLink:** Remove the link from the parent's `/resources/` collection.
    2.  **Orphan Child:** If the child container's `parent_id` matches this parent:
        *   Set child's `parent_id` to `None`.
        *   **Reset child's `depth` to 1.**
        *   **Result:** Container becomes an "Orphan" (available in "Add Existing" pool).
    3.  **Emit Events:** `resource_removed` (on parent) + `updated` (on child).

**2. Delete Container (Destroy)**
*   **User Action:** "Delete Agent/Tool/Session" (Owner only)
*   **Endpoint:** `DELETE /api/v5/containers/{type}/{id}`
*   **Logic:**
    1.  **Cleanup Parent:** Find the parent container (via `parent_id`) and delete the `ResourceLink` pointing to this container.
    2.  **Delete Children:** Recursively destroy all child containers (if any).
    3.  **Delete Instance:** Delete the container document and its `/resources/` subcollection.
    4.  **Emit Events:** `deleted` (on container) + `resource_removed` (on parent).

**3. Add Existing (Move/Adopt)**
*   **User Action:** "Add Existing" (from picker)
*   **Logic:**
    1.  **Validate:** Ensure container is not a SESSION (Sessions cannot be moved/adopted to prevent cycles and complexity).
    2.  **Move:** If container already has a parent, remove it from old parent (implicit unlink).
    3.  **Adopt:**
        *   Set child's `parent_id` to new parent.
        *   Update child's `depth` = `parent.depth + 1`.
    4.  **Link:** Create ResourceLink in new parent's `/resources/`.
    5.  **Emit Events:** `resource_added` (on new parent) + `resource_removed` (on old parent, if any) + `updated` (on child).

---

## 9. Missing System Data

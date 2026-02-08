# GitHub Copilot Instructions

**Project:** My Tiny Data Collider (React + Vite + FastAPI)  
**Architecture:** Universal Object Model v4.2.0

---

## Big Picture

A visual **Data Collider** where users orchestrate AI workflows on a ReactFlow canvas. Container-based architecture: Session → Agent → Tool → Source. Everything except Source/User is navigable.

**Key Files:**
- `ARCHITECTURE_V4.md` — Container model, depth/tier rules, terminal node behavior
- `BUG_LIST.md` — Current cycle's issue tracking (Phase 1/2/3 sections)
- `frontend/docs/chatagent-context.md` — ChatAgent grounding (API mappings, UX vocabulary)

---

## 3-Phase Workflow

| Phase | Mode | Task | Focus |
|-------|------|------|-------|
| **1. UX** | `🎮 Start: Demo + Edge Debug` | No backend | ReactFlow, Zustand, visual bugs |
| **2. Integration** | `Start: Full Stack` | Mock Firestore | API wiring, data integrity |
| **3. Production** | `Start: Cloud Mode` | Real Firestore | Security, performance |

**Log issues to `BUG_LIST.md`** under the appropriate phase section.

---

## Critical Patterns

### Terminal Nodes (Source, User)
- **Cannot** navigate into (no double-click, no "Open" menu)
- **Cannot** have children
- Detect via: `type === 'source' || type === 'user'`

### Depth/Tier Rules
- FREE: max L2, PRO/ENTERPRISE: max L4
- At max depth, only SOURCE can be added
- See `ARCHITECTURE_V4.md` Section 2.2

### State Access
```javascript
// Zustand store (browser_evaluate)
window.__workspaceStore.getState()

// Collider Bridge (DEV builds)
window.__colliderBridge.inbox.push({ id: 'x', command: 'get_state' })
```

### localStorage
- Key: `workspace-storage`
- Persists across phases; demo data loads only when empty + `VITE_MODE=demo`

### Collider Bridge (DEV builds)
Bidirectional Copilot ↔ Host communication for testing. Push to `inbox`, read from `outbox`.

| Command | Purpose |
|---------|---------|
| `navigate_into` | Enter container by nodeId |
| `navigate_back` | Go up one level |
| `open_context_menu` | Right-click on nodeId |
| `click_menu_item` | Click menu item by text |
| `capture_state` | Get full state snapshot |
| `assert_url` | Verify URL pattern |
| `assert_breadcrumb` | Check breadcrumb text |

Console tags: `[BRIDGE→HOST]`, `[BRIDGE_RESULT]`

---

## MCP Tools (MANDATORY)

**Never guess APIs. Query tools first:**
- **MCP Playwright** — `browser_snapshot`, `browser_evaluate`, `browser_console_messages`
- **Context7** — Library docs (Playwright, ReactFlow, FastAPI)
- **AI Toolkit** — `aitk-get_agent_code_gen_best_practices` for ChatAgent work
- **Azure MCP** — Firestore rules, Cloud Run

---

## VS Code Extensions (Phase 2+)

| Extension | Purpose | Phase |
|-----------|---------|-------|
| **OpenAPI Editor** (`42crunch.vscode-openapi`) | Validate `openapi-schema.json`, catch schema drift | 2, 3 |
| **httpYac** (`anweber.vscode-httpyac`) | Request chaining, env switching (mock/prod) | 2, 3 |
| **Pytest IntelliSense** (`cameron.vscode-pytest`) | Fixture autocomplete in `conftest.py` | 2, 3 |
| **Python Test Explorer** (`littlefoxteam.vscode-python-test-adapter`) | Visual test runner sidebar | 2, 3 |

---

## Quick Commands

```powershell
# Frontend tests (Demo mode, no backend)
npx playwright test uom- --project=msedge --timeout=15000

# Backend tests
pytest tests/unit/api/test_resources_api.py -v

# Health check
Invoke-RestMethod -Uri 'http://localhost:8000/health'
```

**Test Credentials:** `enterprise@test.com` / `testpassword123` (ENTERPRISE tier)

---

## Stack Summary

| Layer | Tech | Key Files |
|-------|------|-----------|
| Frontend | React 18, Vite, Zustand, ReactFlow 12 | `workspace-store.ts`, `GameCanvas.tsx` |
| Backend | FastAPI, Pydantic, Firestore | `src/api/routes/`, `src/services/` |
| AI | Gemini 3 Pro (cloud), WebLLM (local) | `gemini-live-client.ts`, `voice-agent.ts` |

---

## Code Conventions

### Zustand Stores
```typescript
// Pattern: Single store with persist middleware
export const useWorkspaceStore = create<WorkspaceState>()(
  persist((...a) => ({ ...initialState }), { name: 'workspace-storage' })
)

// Selectors: Always use individual selectors to prevent re-renders
const nodes = useWorkspaceStore((s) => s.nodes)
const { addNode } = useWorkspaceStore.getState()  // Actions outside React
```

**Stores:** `workspace-store.ts` (main), `toast-store.ts`, `chat-store.ts`

### Component Naming
| Category | Pattern | Examples |
|----------|---------|----------|
| Canvas nodes | `{Type}Node.tsx` | `AgentNode`, `SourceNode`, `ToolNode` |
| Modals | `{Action}{Type}Modal.tsx` | `AddAgentInstanceModal`, `CreateCustomToolModal` |
| Context menus | `{Scope}ContextMenu.tsx` | `ContextMenu`, `SessionContextMenu` |
| Forms | `{Type}QuickEditForm.tsx` | `SessionQuickEditForm`, `ContainerQuickEditForm` |

### Import Order
1. React/external libs (`react`, `@xyflow/react`, `zustand`)
2. API modules (`./api-v4`, `./api-types`)
3. Store hooks (`./workspace-store`, `./toast-store`)
4. Types (`./types`)
5. Components (relative paths)

---

## Response Protocol

1. **Confidence ≥80%** → Implement directly
2. **Confidence <80%** → State brief plan, proceed
3. **Every response** → Include next action
4. **Tool preference** → VS Code tasks > scripts > manual

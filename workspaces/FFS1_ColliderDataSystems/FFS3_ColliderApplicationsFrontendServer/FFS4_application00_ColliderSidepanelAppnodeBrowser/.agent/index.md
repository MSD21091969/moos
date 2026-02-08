# FFS4 Collider Sidepanel Appnode Browser - Agent Context

> Chrome extension sidepanel for browsing and managing appnodes in the Collider system

## Location

`D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS3_ColliderApplicationsFrontendServer\FFS4_application00_ColliderSidepanelAppnodeBrowser\.agent\`

## Hierarchy

```
FFS0_Factory (Root)
  └── FFS1_ColliderDataSystems (IDE Context)
        └── FFS3_ColliderFrontend (Frontend Server)
              └── FFS4_Sidepanel (This Application)
```

## Purpose

### User-Facing Purpose
The Sidepanel provides a persistent companion UI in Chrome that allows users to:
- Browse and navigate container nodes (Appnode Browser)
- Interact with the AI pilot/main agent seat
- View appnode tree structure
- Perform quick actions on containers
- Access frequently used features without leaving the current tab

### Technical Role
Acts as the main UI bridge between the Chrome Extension and the Collider backend services, providing:
- Real-time container tree visualization (Appnode Browser)
- AI Pilot/Main Agent Seat interface for agent interactions
- Quick access toolbar for common operations
- Integration point for other FFS applications (FFS5 PiP for user comms, FFS6 IDE)

### Key Responsibilities
- Render container hierarchy in tree view (Appnode Browser)
- Provide AI Pilot/Agent Seat interface for agent interactions
- Handle user interactions (expand/collapse, select, context menu)
- Communicate with Chrome Extension background service
- Sync state with backend via ColliderDataServer

## Key Components

### Pages/Routes
- Sidepanel operates in Chrome's side panel (not a web route)
- Opens via Chrome Extension icon or keyboard shortcut

### Main Components
- **AppnodeTree** - Hierarchical tree view of containers (Appnode Browser)
- **PilotSeatPanel** - AI Pilot/Main Agent Seat interface for agent interactions
- **ContainerCard** - Individual container display with quick actions
- **QuickActionsToolbar** - Common operations (create, delete, refresh)
- **SearchBar** - Filter and search containers
- **StatusIndicator** - Connection status to backend

### State Management
- **Zustand store** for local sidepanel state
- **Chrome Storage API** for persistent settings
- Key stores:
  - `useSidepanelStore` - Tree state, selected node, expanded nodes
  - `useExtensionStore` - Extension-wide state (shared with background)

### Integration Points

**Backend APIs:**
- `GET /api/containers` - Fetch container tree
- `POST /api/containers` - Create new container
- `DELETE /api/containers/:id` - Delete container
- `PATCH /api/containers/:id` - Update container

**Chrome Extension:**
- Messages sent:
  - `SIDEPANEL_READY` - Notify extension sidepanel loaded
  - `CONTAINER_SELECTED` - User selected a container
  - `OPEN_IN_PIP` - Request to open container in PiP window (FFS5)
  - `OPEN_IN_IDE` - Request to open in IDE (FFS6)
- Messages received:
  - `CONTAINER_UPDATED` - Container changed, refresh view
  - `SYNC_STATE` - Sync state from background service

**Other FFS Apps:**
- FFS5 (PiP): User-to-user communication window (WebRTC)
- FFS6 (IDE): Sends file path to open in IDE

**Note:** The actual implementation code lives in FFS2 Chrome Extension:
`FFS2_ColliderBackends_MultiAgentChromeExtension/ColliderMultiAgentsChromeExtension/src/`

## Development

### Running Locally

The sidepanel is part of the Chrome Extension (FFS2):

```bash
cd FFS2_ColliderBackends_MultiAgentChromeExtension/ColliderMultiAgentsChromeExtension
pnpm dev
# Load unpacked extension in Chrome
# Open sidepanel from extension icon
```

### Key Dependencies

- `@plasmohq/messaging` - Chrome extension messaging
- `@plasmohq/storage` - Chrome storage wrapper
- React - UI framework
- Zustand - State management

### Environment Variables

```bash
PLASMO_PUBLIC_API_BASE=http://localhost:8000
```

## Domain Context

- **Domain**: sidepanel
- **App Type**: extension-ui
- **Features**:
  - appnode_browser - Browse container tree
  - container_tree - Hierarchical tree view
  - quick_actions - Common operations toolbar

## Related Documentation

- FFS3 Frontend: `../knowledge/codebase.md`
- Chrome Extension: `../../../FFS2_ColliderBackends_MultiAgentChromeExtension/.agent/`
- Backend API: `../../../FFS2_ColliderBackends_MultiAgentChromeExtension/ColliderDataServer/.agent/`

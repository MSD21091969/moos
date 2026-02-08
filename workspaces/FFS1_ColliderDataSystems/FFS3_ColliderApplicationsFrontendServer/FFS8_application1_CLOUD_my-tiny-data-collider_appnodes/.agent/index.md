# FFS8 My Tiny Data Collider - CLOUD Domain - Agent Context

> Personal data collection and visualization platform for the Collider system

## Location

`D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS3_ColliderApplicationsFrontendServer\FFS8_application1_CLOUD_my-tiny-data-collider_appnodes\.agent\`

## Hierarchy

```
FFS0_Factory (Root)
  └── FFS1_ColliderDataSystems (IDE Context)
        └── FFS3_ColliderFrontend (Frontend Server)
              └── FFS8_my-tiny-data-collider (This Application)
```

## Purpose

### User-Facing Purpose
My Tiny Data Collider is the main personal data platform that allows users to:
- Collect and store personal data (containers/nodes)
- Visualize data relationships in interactive graphs
- Export and import data collections
- Organize data in hierarchical structures
- Share data collections with others
- Sync data across devices (cloud storage)

### Technical Role
Acts as the primary CLOUD domain application for personal data management:
- Container node CRUD operations
- 3D Force Graph visualization using D3/Three.js
- Data import/export (JSON, CSV, etc.)
- Cloud synchronization with backend
- Collaborative features (sharing, permissions)
- Real-time updates via WebSocket

### Key Responsibilities
- Create, read, update, delete container nodes
- Render interactive 3D graph of node relationships
- Handle data import/export workflows
- Sync local changes with cloud backend
- Manage sharing and collaboration permissions
- Track data versioning and history
- Implement search and filtering across nodes

## Key Components

### Pages/Routes
- `/app` - Main application dashboard
- `/app/graph` - 3D Force Graph visualization
- `/app/containers` - Container list view
- `/app/container/:id` - Container detail view
- `/app/import` - Data import wizard
- `/app/export` - Export dialog
- `/app/shared` - Shared collections
- `/app/sync` - Sync status and settings

### Main Components
- **ForceGraph3D** (`src/components/ForceGraph3D.tsx`) - 3D graph visualization
- **ContainerList** (`src/components/ContainerList.tsx`) - Table/card view of containers
- **ContainerEditor** (`src/components/ContainerEditor.tsx`) - Create/edit container form
- **NodeInspector** (`src/components/NodeInspector.tsx`) - Side panel for selected node details
- **DataImporter** (`src/components/DataImporter.tsx`) - Import wizard (JSON, CSV, etc.)
- **DataExporter** (`src/components/DataExporter.tsx`) - Export options dialog
- **SyncStatus** (`src/components/SyncStatus.tsx`) - Cloud sync indicator
- **ShareDialog** (`src/components/ShareDialog.tsx`) - Share collection with others
- **SearchBar** (`src/components/SearchBar.tsx`) - Global search across containers

### State Management
- **Zustand stores** for application state
- Key stores:
  - `useDataStore` - Container nodes, graph data
  - `useSyncStore` - Sync status, pending changes
  - `useGraphStore` - Graph layout, selection, camera
  - `useShareStore` - Shared collections, permissions
- **TanStack Query** for server state caching

### Integration Points

**Backend APIs:**
- `GET /api/containers` - Fetch user's containers
- `POST /api/containers` - Create container
- `PUT /api/containers/:id` - Update container
- `DELETE /api/containers/:id` - Delete container
- `GET /api/containers/:id/relationships` - Get node relationships
- `POST /api/import` - Import data
- `GET /api/export` - Export data
- `POST /api/share` - Share collection
- `WebSocket /ws/sync` - Real-time sync channel

**Chrome Extension:**
- Messages sent:
  - `DATA_UPDATED` - Notify extension of data changes
  - `CONTAINER_CREATED` - New container created
- Messages received:
  - `SYNC_CONFLICT` - Conflict resolution needed
  - `SHARED_UPDATE` - Shared collection updated

**Other FFS Apps:**
- FFS4 (Sidepanel): Navigate to containers from tree view
- FFS5 (PiP): Share collaboration during calls
- FFS7 (Admin): Quota and storage management

## Development

### Running Locally

```bash
cd collider-frontend
pnpm dev
# Navigate to http://localhost:3000/app
```

### Key Dependencies

- `react-force-graph-3d` - 3D force-directed graph
- `three` - 3D rendering engine
- `d3-force-3d` - Physics simulation
- `recharts` - Charts for analytics
- `react-dropzone` - File upload
- `papaparse` - CSV parsing
- `date-fns` - Date formatting
- `@collider/api-client` - Backend API
- `@collider/node-container` - Shared container types

### Environment Variables

```bash
NEXT_PUBLIC_API_BASE=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
NEXT_PUBLIC_MAX_UPLOAD_SIZE=10485760  # 10MB
```

## Data Model

### Container Node

```typescript
interface ContainerNode {
  id: string;
  name: string;
  type: 'folder' | 'file' | 'note' | 'link' | 'custom';
  description?: string;
  metadata: Record<string, any>;
  tags: string[];
  parentId?: string;
  children?: ContainerNode[];
  createdAt: Date;
  updatedAt: Date;
  ownerId: string;
  sharedWith?: SharedPermission[];
}

interface SharedPermission {
  userId: string;
  permission: 'view' | 'edit' | 'admin';
}
```

### Graph Data

```typescript
interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

interface GraphNode {
  id: string;
  name: string;
  val: number;  // Node size
  color: string;
  metadata: any;
}

interface GraphLink {
  source: string;
  target: string;
  value: number;  // Link strength
}
```

## Domain Context

- **Domain**: cloud
- **App Type**: web-app
- **Features**:
  - data_collection - Container CRUD
  - container_nodes - Hierarchical data structures
  - cloud_sync - Real-time synchronization
  - export_import - Data portability
  - 3d_graph - Interactive visualization
  - collaboration - Sharing and permissions

## Key Features

### 1. 3D Force Graph Visualization

Interactive 3D graph powered by Three.js:
- Force-directed layout
- Zoom, pan, rotate controls
- Node selection and highlighting
- Relationship visualization
- Search and filter nodes
- Camera animations

### 2. Data Import/Export

Support for multiple formats:
- JSON (native format)
- CSV (with column mapping)
- Markdown (for notes)
- XML
- Custom formats via plugins

### 3. Cloud Synchronization

Real-time sync across devices:
- Optimistic UI updates
- Conflict resolution
- Offline support (IndexedDB)
- Merge strategies
- Version history

### 4. Collaboration & Sharing

Share collections with others:
- Granular permissions (view, edit, admin)
- Invite by email
- Public sharing links
- Activity feed
- Commenting on nodes

## Performance Considerations

- **Graph Rendering**: Limit visible nodes (>1000 use LOD)
- **WebGL**: Hardware acceleration for 3D
- **Data Pagination**: Load containers on-demand
- **IndexedDB**: Local caching for offline
- **Web Workers**: Parse large imports off main thread

## Offline Support

Uses IndexedDB + service worker:
- Cache containerdata locally
- Queue sync operations
- Auto-sync when online
- Conflict resolution UI

## Related Documentation

- FFS3 Frontend: `../knowledge/codebase.md`
- Backend API: `../../../FFS2_ColliderBackends_MultiAgentChromeExtension/ColliderDataServer/.agent/`
- Shared Libraries: `../../libs/node-container/.agent/`
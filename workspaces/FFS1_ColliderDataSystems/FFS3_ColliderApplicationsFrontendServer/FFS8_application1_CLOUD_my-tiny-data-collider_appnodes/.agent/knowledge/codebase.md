# Codebase: FFS8 My Tiny Data Collider - CLOUD Domain

> Next.js web app with 3D Force Graph (Three.js), real-time sync (WebSocket), and offline-first architecture (IndexedDB)

## Overview

My Tiny Data Collider is the flagship personal data management application. It provides users with a powerful platform to collect, organize, visualize, and share their data. The application employs a 3D force-directed graph for intuitive data exploration, real-time cloud synchronization for multi-device access, and comprehensive import/export capabilities for data portability.

## Directory Structure

```
collider-frontend/apps/my-tiny-data-collider/
├── app/
│   ├── app/
│   │   ├── layout.tsx                      # App layout wrapper
│   │   ├── page.tsx                        # Dashboard home
│   │   ├── graph/
│   │   │   └── page.tsx                    # 3D graph view
│   │   ├── containers/
│   │   │   ├── page.tsx                    # Container list
│   │   │   └── [id]/
│   │   │       └── page.tsx                # Container detail
│   │   ├── import/
│   │   │   └── page.tsx                    # Import wizard
│   │   ├── export/
│   │   │   └── page.tsx                    # Export dialog
│   │   ├── shared/
│   │   │   └── page.tsx                    # Shared collections
│   │   └── sync/
│   │       └── page.tsx                    # Sync settings
├── components/
│   ├── ForceGraph3D/
│   │   ├── ForceGraph3D.tsx                # Main 3D graph
│   │   ├── GraphControls.tsx               # Camera controls
│   │   ├── GraphSearch.tsx                 # Node search overlay
│   │   └── GraphLegend.tsx                 # Node type legend
│   ├── ContainerList/
│   │   ├── ContainerTable.tsx              # Table view
│   │   ├── ContainerCard.tsx               # Card view
│   │   └── ContainerFilters.tsx            # Filter controls
│   ├── ContainerEditor/
│   │   ├── ContainerForm.tsx               # Create/edit form
│   │   ├── MetadataEditor.tsx              # Metadata key-value editor
│   │   └── TagInput.tsx                    # Tag management
│   ├── NodeInspector/
│   │   ├── NodeInspector.tsx               # Side panel
│   │   ├── NodeDetails.tsx                 # Node properties
│   │   ├── NodeRelationships.tsx           # Connected nodes
│   │   └── NodeHistory.tsx                 # Version history
│   ├── DataImporter/
│   │   ├── ImportWizard.tsx                # Multi-step wizard
│   │   ├── FileUploader.tsx                # Dropzone
│   │   ├── ImportPreview.tsx               # Data preview
│   │   └── ColumnMapper.tsx                # CSV column mapping
│   ├── DataExporter/
│   │   ├── ExportDialog.tsx                # Export options
│   │   ├── FormatSelector.tsx              # JSON/CSV/etc selector
│   │   └── ExportProgress.tsx              # Export status
│   ├── SyncStatus/
│   │   ├── SyncIndicator.tsx               # Status badge
│   │   ├── SyncLog.tsx                     # Sync history
│   │   └── ConflictResolver.tsx            # Merge conflicts UI
│   ├── ShareDialog/
│   │   ├── ShareDialog.tsx                 # Main dialog
│   │   ├── PermissionSelector.tsx          # Permission dropdown
│   │   └── ShareLink.tsx                   # Public link generator
│   └── SearchBar/
│       └── GlobalSearch.tsx                # Full-text search
├── hooks/
│   ├── useContainers.ts                    # Container CRUD
│   ├── useGraph.ts                         # Graph state
│   ├── useSync.ts                          # Sync logic
│   ├── useOfflineCache.ts                  # IndexedDB cache
│   ├── useWebSocket.ts                     # WebSocket connection
│   ├── useImporter.ts                      # Import logic
│   ├── useExporter.ts                      # Export logic
│   └── useShare.ts                         # Sharing logic
├── stores/
│   ├── dataStore.ts                        # Container data
│   ├── syncStore.ts                        # Sync state
│   ├── graphStore.ts                       # Graph state
│   └── shareStore.ts                       # Sharing state
├── services/
│   ├── containerService.ts                 # Container API client
│   ├── syncService.ts                      # Sync orchestration
│   ├── offlineService.ts                   # IndexedDB operations
│   ├── websocketService.ts                 # WebSocket client
│   ├── importService.ts                    # Data parsing
│   └── exportService.ts                    # Data serialization
├── workers/
│   ├── import.worker.ts                    # Import processing
│   └── export.worker.ts                    # Export processing
└── types/
    ├── container.ts                        # Container types
    ├── graph.ts                            # Graph types
    ├── sync.ts                             # Sync types
    └── share.ts                            # Sharing types
```

## Component Architecture

### Core Components

**ForceGraph3D** (`components/ForceGraph3D/ForceGraph3D.tsx`)
- **Purpose**: 3D force-directed graph visualization
- **Props**:
  - `data: GraphData` - Nodes and links
  - `onNodeClick: (node: GraphNode) => void`
  - `highlightedNodes: Set<string>`
- **State**: Camera position, selected node, hovered node
- **Dependencies**: `react-force-graph-3d`, `three`
- **Integration**: Fetches data from `useGraph` hook

**ContainerEditor** (`components/ContainerEditor/ContainerForm.tsx`)
- **Purpose**: Create and edit container nodes
- **Props**:
  - `container?: Container` - Existing container for edit mode
  - `onSave: (container: Container) => void`
- **State**: Form data, validation errors
- **Dependencies**: React Hook Form, Zod
- **Integration**: Creates/updates via `useContainers` hook

**SyncIndicator** (`components/SyncStatus/SyncIndicator.tsx`)
- **Purpose**: Real-time sync status badge
- **Props**: None (uses sync store)
- **State**: Sync status (idle, syncing, error)
- **Dependencies**: None
- **Integration**: Subscribes to WebSocket sync events

## Data Flow

### Container CRUD Flow

```
1. User creates container in ContainerForm
2. Form validation (Zod schema)
3. Optimistic UI update → Add to dataStore
4. POST /api/containers → Backend
5. WebSocket broadcast → Other clients
6. IndexedDB write → Offline cache
7. Success → Confirm in UI
8. Failure → Rollback optimistic update, show error
```

### Real-Time Sync Flow

```
1. WebSocket connection established
2. Subscribe to user's sync channel
3. Local change → Send via WebSocket
4. Remote change → Receive via WebSocket
5. Conflict detection → Compare timestamps
6. Conflict resolution:
   - Last Write Wins (default)
   - Manual merge (conflictResolver UI)
7. Update local store + IndexedDB
8. Re-render affected components
```

### 3D Graph Rendering Flow

```
1. useGraph hook fetches container data
2. Transform containers → GraphData (nodes + links)
3. ForceGraph3D receives GraphData
4. Three.js scene initialization
5. D3-force-3d physics simulation starts
6. Render loop (60 FPS)
7. User interaction → Update camera/selection
8. Selected node → Open NodeInspector
```

## Key Features Implementation

### Feature 1: 3D Force Graph

**Implementation:**
```typescript
// components/ForceGraph3D/ForceGraph3D.tsx
'use client';

import ForceGraph3D from 'react-force-graph-3d';
import { useGraph } from '@/hooks/useGraph';
import { useEffect, useRef } from 'react';

export function ForceGraph3DComponent() {
  const { graphData, selectedNode, setSelectedNode } = useGraph();
  const fgRef = useRef<any>();

  useEffect(() => {
    if (fgRef.current && selectedNode) {
      // Zoom to selected node
      const node = graphData.nodes.find(n => n.id === selectedNode);
      if (node) {
        fgRef.current.cameraPosition(
          { x: node.x, y: node.y, z: node.z + 100 },
          node,
          1000
        );
      }
    }
  }, [selectedNode]);

  return (
    <ForceGraph3D
      ref={fgRef}
      graphData={graphData}
      nodeLabel="name"
      nodeAutoColorBy="type"
      onNodeClick={(node) => setSelectedNode(node.id)}
      nodeThreeObject={(node) => {
        // Custom node rendering with Three.js
        const geometry = new THREE.SphereGeometry(node.val);
        const material = new THREE.MeshLambertMaterial({
          color: node.color,
          transparent: true,
          opacity: 0.75
        });
        return new THREE.Mesh(geometry, material);
      }}
      linkDirectionalParticles={2}
      linkDirectionalParticleWidth={2}
    />
  );
}
```

### Feature 2: Real-Time Sync

**Implementation:**
```typescript
// hooks/useSync.ts
import { useEffect } from 'use';
import { useWebSocket } from './useWebSocket';
import { useDataStore } from '@/stores/dataStore';
import { offlineService } from '@/services/offlineService';

export function useSync() {
  const { socket, connected } = useWebSocket();
  const { containers, updateContainer, addContainer, removeContainer } = useDataStore();

  useEffect(() => {
    if (!socket) return;

    // Listen for remote changes
    socket.on('container:created', (container) => {
      addContainer(container);
      offlineService.saveContainer(container);
    });

    socket.on('container:updated', async (update) => {
      const local = containers.find(c => c.id === update.id);

      if (!local) {
        // New container from remote
        addContainer(update.container);
      } else {
        // Conflict detection
        if (update.updatedAt > local.updatedAt) {
          // Remote is newer
          updateContainer(update.id, update.container);
        } else {
          // Local is newer, send our version
          socket.emit('container:update', {
            id: local.id,
            container: local,
            timestamp: local.updatedAt
          });
        }
      }

      offlineService.saveContainer(update.container);
    });

    socket.on('container:deleted', (id) => {
      removeContainer(id);
      offlineService.deleteContainer(id);
    });
  }, [socket, containers]);

  const syncAll = async () => {
    // Sync all local changes
    const pendingChanges = await offlineService.getPendingChanges();
    for (const change of pendingChanges) {
      socket?.emit(`container:${change.action}`, change.data);
    }
  };

  return { connected, syncAll };
}
```

### Feature 3: Offline Support

**Implementation:**
```typescript
// services/offlineService.ts
import { openDB, DBSchema, IDBPDatabase } from 'idb';

interface ColliderDB extends DBSchema {
  containers: {
    key: string;
    value: Container;
    indexes: { 'by-updated': Date };
  };
  pendingSync: {
    key: string;
    value: { action: 'create' | 'update' | 'delete'; data: any; timestamp: Date };
  };
}

class OfflineService {
  private db: IDBPDatabase<ColliderDB> | null = null;

  async init() {
    this.db = await openDB<ColliderDB>('collider-data', 1, {
      upgrade(db) {
        const containerStore = db.createObjectStore('containers', {
          keyPath: 'id'
        });
        containerStore.createIndex('by-updated', 'updatedAt');

        db.createObjectStore('pendingSync', { keyPath: 'id' });
      },
    });
  }

  async saveContainer(container: Container) {
    if (!this.db) await this.init();
    await this.db!.put('containers', container);
  }

  async getContainers(): Promise<Container[]> {
    if (!this.db) await this.init();
    return await this.db!.getAll('containers');
  }

  async deleteContainer(id: string) {
    if (!this.db) await this.init();
    await this.db!.delete('containers', id);
  }

  async queueSync(action: string, data: any) {
    if (!this.db) await this.init();
    await this.db!.put('pendingSync', {
      id: crypto.randomUUID(),
      action,
      data,
      timestamp: new Date()
    });
  }

  async getPendingChanges() {
    if (!this.db) await this.init();
    return await this.db!.getAll('pendingSync');
  }
}

export const offlineService = new OfflineService();
```

### Feature 4: Data Import

**Implementation:**
```typescript
// components/DataImporter/ImportWizard.tsx
'use client';

import { useState } from 'react';
import { useImporter } from '@/hooks/useImporter';

export function ImportWizard() {
  const [step, setStep] = useState(1);
  const [file, setFile] = useState<File | null>(null);
  const { importData, isImporting, progress } = useImporter();

  const handleFileSelect = (acceptedFiles: File[]) => {
    setFile(acceptedFiles[0]);
    setStep(2);
  };

  const handleImport = async () => {
    if (!file) return;

    setStep(3);

    // Use Web Worker for parsing
    const worker = new Worker(new URL('@/workers/import.worker.ts', import.meta.url));

    worker.postMessage({ file });

    worker.onmessage = async (e) => {
      const { data, format } = e.data;

      // Import to backend
      await importData(data, format);

      setStep(4); // Success
    };
  };

  return (
    <div>
      {step === 1 && <FileUploader onDrop={handleFileSelect} />}
      {step === 2 && <ImportPreview file={file} onConfirm={handleImport} />}
      {step === 3 && <ImportProgress progress={progress} />}
      {step === 4 && <ImportSuccess />}
    </div>
  );
}
```

## Styling Approach

- **Framework:** Tailwind CSS
- **3D Rendering:** Three.js (WebGL)
- **Layout:** Flex + Grid
- **Theme:** Dark theme optimized for graph visualization

## Performance Considerations

- **Graph:** Limit to 1000 visible nodes, LOD for larger graphs
- **WebGL:** Hardware acceleration
- **Web Workers:** Offload parsing/serialization
- **IndexedDB:** Batch writes (transaction grouping)
- **React:** Virtualized lists for container table

## Testing

```bash
npx nx test my-tiny-data-collider
```

### Test Coverage
- Component tests: Graph interactions, forms
- Hook tests: Sync logic, conflict resolution
- Integration tests: End-to-end import/export
- E2E tests: Full user workflows

## Known Issues / Technical Debt

- Large graphs (>5000 nodes) cause performance degradation
- Conflict resolution UI needs UX improvements
- No real-time collaboration cursors yet
- Export to PDF not implemented

## Security Considerations

- API calls authenticated with JWT
- WebSocket connection authenticated on handshake
- Shared links signed with expiration
- Granular permissions enforced on backend
- XSS protection for user-generated content

## Related Code

- **Backend API:** `FFS2_ColliderBackends/ColliderDataServer/`
- **Shared Libraries:** `libs/node-container/`, `libs/api-client/`
- **WebSocket Server:** `FFS2_ColliderBackends/ColliderGraphToolServer/`

## Development Workflow

1. **Adding new container type:**
   ```bash
   # Update types in libs/node-container
   # Add icon/color in ForceGraph3D
   # Update form validation
   # Test import/export
   ```

2. **Debugging sync issues:**
   - Check WebSocket connection in Network tab
   - Inspect IndexedDB in Application tab
   - Check sync logs in SyncLog component

3. **Building for production:**
   ```bash
   npx nx build my-tiny-data-collider
   ```
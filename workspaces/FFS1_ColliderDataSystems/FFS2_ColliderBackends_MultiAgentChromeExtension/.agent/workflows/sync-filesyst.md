---
description: Sync local filesystem workspace data to ColliderDataServer via Native Messaging
---

# Sync: Filesystem to DataServer

Triggers a filesystem sync — reads local `.agent/` context and workspace structure, then pushes it to the ColliderDataServer via the Native Messaging host.

## Prerequisites

- ColliderDataServer running on `:8000`
- Native Messaging host registered (see `ColliderMultiAgentsChromeExtension` setup)
- Chrome Extension loaded and authenticated

## Steps

1. Verify the DataServer is reachable:

   ```powershell
   curl http://localhost:8000/health
   ```

2. Trigger sync via the extension sidepanel:
   - Open the Chrome Extension sidepanel
   - Navigate to the workspace node you want to sync
   - Click **Sync Filesystem** (or use the agent command: `sync workspace`)

3. Alternatively, trigger sync directly via the DataServer API:

   ```powershell
   curl -X POST http://localhost:8000/api/v1/sync/filesyst `
     -H "Authorization: Bearer <token>" `
     -H "Content-Type: application/json" `
     -d '{"workspace_path": "D:/FFS0_Factory/workspaces/FFS1_ColliderDataSystems"}'
   ```

4. Verify sync completed — check SSE stream or DataServer logs for confirmation events.

## Notes

- Sync is additive — existing nodes are updated, new nodes are created.
- The `FILESYST` domain config must be enabled for the target workspace node.

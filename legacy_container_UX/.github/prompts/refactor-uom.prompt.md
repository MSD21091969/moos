---
description: Refactor component to UOM v5
---
Refactor the selected code to align with Universal Object Model v5.0.

# Core Rules
1.  **Containers over Sessions:**
    -   Replace `sessions` array with `containers`.
    -   Replace `activeSessionId` with `activeContainerId`.
    -   `UserSession` objects are now `Container` objects.

2.  **State Access:**
    -   Use `useWorkspaceStore` from `@/store`.
    -   Select specific slices: `const containers = useWorkspaceStore(s => s.containers)`.

3.  **Terminology:**
    -   **UI:** "Sticky Note" (User facing)
    -   **Code:** "Container" (Internal)
    -   **Legacy:** "Session" (Avoid unless wrapping for backward compatibility)

4.  **Validation:**
    -   Ensure no `any` types are introduced.
    -   Preserve existing functionality.

# ResourceLink-Centric Grid (v5.1+)

5.  **Grid = f(ResourceLinks):**
    -   Grid renders `ResourceLink[]`, NOT containers directly.
    -   Each grid item = `ResourceLink` (position, config) + `Container` (state).
    -   Use `containerRegistry[id].resources` for child links.

6.  **Library = Orphans:**
    -   Orphans are containers with `parent_id === null`.
    -   "Add Existing" menu reads from `orphanContainers` memo.
    -   Filter by type: `getOrphansByType('agent' | 'tool' | 'source')`.

7.  **SSE Sync Pattern:**
    -   Visual data (position, color) → immediate render.
    -   Library data (parent_id) → registry update only, read on menu open.
    -   Use `handleContainerEvent` CASE 2 for container updates.

8.  **Strict Tree Topology:**
    -   Backend rejects adoption if `parent_id !== null`.
    -   Must unlink before re-adopting elsewhere.
    -   Use `instance_id` in `addResourceLink` for existing containers.

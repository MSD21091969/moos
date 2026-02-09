# Architecture Documentation Accuracy Report
**Date**: 2026-02-09
**Inspected**: 11 files in `.agent/knowledge/architecture/`
**Current Implementation**: v2.0 (Frontend Architecture Restructure)

---

## ⚠️ Critical Issues (Require Immediate Updates)

### 1. **02_backend.md** - Multiple Severe Inaccuracies

**Issue**: References non-existent "Frontend Server" component

**Lines 33-35**:
```
Backend Stack (Python FastAPI)
├── DATA
├── GRAPH
└── FRONTEND (Portal)  ❌ WRONG - Portal was deleted!
```

**Actual Current Stack**:
```
Backend Stack
├── ColliderDataServer (FastAPI + SQLite)
├── ColliderGraphToolServer (FastAPI + WebSocket)
└── ColliderVectorDbServer (FastAPI + ChromaDB)
```

**Lines 129-138**: Entire "Frontend Server" section is obsolete
- No static file server exists anymore
- Portal app was deleted in Component 2 of rebuild

**Lines 28-30, 43-46**: Database mismatch
- **Stated**: PostgreSQL
- **Actual**: SQLite

**Lines 43-46**: Incorrect path
- **Stated**: `ColliderDataServer/`
- **Actual**: `FFS2_ColliderBackends_MultiAgentChromeExtension/ColliderDataServer/`

**Fix Required**:
- Remove all "Frontend Server" and "Portal" references
- Change PostgreSQL → SQLite throughout
- Update all file paths to include FFS2 parent directory
- Remove frontend section entirely (lines 129-138)

---

### 2. **03_frontend.md** - Outdated Component Structure

**Issue**: Describes v1.0 monolithic structure, not current v2.0 workspace-driven packages

**Lines 187-188**:
```
FFS2 Chrome Extension (sidepanel.tsx, src/components/sidepanel/)
Context Documentation: FFS4 (.agent/ context only)
```
❌ **WRONG**: Sidepanel now imports from FFS4 package `@collider/sidepanel-ui`

**Lines 207**:
```
FFS2 Chrome Extension (pipWindow.tsx, src/components/pip/)
```
❌ **WRONG**: PiP is now FFS5 package `@collider/pip-ui`

**Missing Information**:
- 7 application packages (FFS4-8)
- Workspace-driven architecture
- Package import strategy
- Context-driven routing (Component 9)

**Fix Required**:
- Add section on v2.0 package-based architecture
- Document FFS4-8 packages with sizes and purposes
- Explain workspace-driven model
- Update FFS2 references to show package imports
- Add WebRTC endpoint documentation

---

### 3. **08_workspace_strategy.md** - Completely Outdated Structure

**Issue**: Shows incorrect FFS4-10 directory structure

**Lines 36-42**:
```
collider-frontend/
├── apps/
│   ├── FFS4/  ❌ WRONG!
│   ├── FFS5/  ❌ WRONG!
│   └── FFS6-10/  ❌ WRONG!
```

**Actual Structure**:
```
FFS3_ColliderApplicationsFrontendServer/
├── collider-frontend/       # Shared libraries only
│   └── libs/
│       ├── api-client/
│       ├── node-container/
│       ├── shared-ui/
│       └── workspace-router/
├── FFS4_application00_ColliderSidepanelAppnodeBrowser/app/
├── FFS5_application01_ColliderPictureInPictureMainAgentSeat/app/
├── FFS6_applicationx_FILESYST_ColliderIDE_appnodes/app/
├── FFS7_applicationz_ADMIN_ColliderAccount_appnodes/app/
└── FFS8_application1_CLOUD_my-tiny-data-collider_appnodes/app/
```

**Fix Required**:
- Complete rewrite of directory structure section
- Document package-based architecture (not apps/ subdirs)
- Add workspace configuration (pnpm-workspace.yaml)
- Document build output (dist/ for each package)
- Add sharp override context

---

### 4. **05_security.md** - Database Mismatch

**Issue**: References PostgreSQL instead of SQLite

**Lines 26, 76**:
- **Stated**: "Lookup UserAccount in PostgreSQL"
- **Actual**: SQLite database

**Fix Required**:
- Change all PostgreSQL references → SQLite
- Note: Storage model remains same (tables, schema)

---

## ✅ Accurate Files (Minor Updates Only)

### **01_components.md** - Mostly Accurate ✅
- General component concepts still valid
- NodeContainer pattern documentation correct
- **Minor update needed**: Add note about FFS4-8 packages

### **02_domains.md** - Accurate ✅
- Domain concepts (FILESYST, CLOUD, ADMIN) still valid
- Context loading explained correctly
- No changes needed

### **04_data_flow.md** - Mostly Accurate ✅
- Protocols (REST, SSE, WebSocket, Native Messaging) unchanged
- **Minor update needed**: Add WebRTC P2P protocol to matrix (Component 1)

### **06_integration.md** - Accurate ✅
- LangGraph ↔ Pydantic AI integration concepts unchanged
- Workflow lifecycle still valid
- Context loading flow correct
- No changes needed

### **07_templates.md** - Accurate ✅
- Template topology concepts unchanged
- Hydration paradigm still valid
- No changes needed

---

## 📋 Index Files

### **_index.md** (architecture/) - Needs Full Rewrite ❌

**Current**: 52 lines, outdated structure
**Issue**: Lists files but doesn't guide through current v2.0 architecture

**Fix Required**:
- Mirror structure of main knowledge base `_index.md`
- Add quick reference: Foundation → Backend → Frontend packages
- Add version context (v2.0 workspace-driven)
- Link to main implementation log (2026-02-09_frontend_architecture_restructure.md)

---

## 🔧 Recommended Update Priority

### Priority 1: Critical (Blocks Understanding)
1. **02_backend.md** - Remove frontend server, fix database, update paths
2. **08_workspace_strategy.md** - Complete restructure to match v2.0
3. **03_frontend.md** - Add v2.0 package architecture, update component refs

### Priority 2: Important (Consistency)
4. **05_security.md** - PostgreSQL → SQLite
5. **_index.md** - Rewrite with v2.0 context

### Priority 3: Enhancement (Completeness)
6. **04_data_flow.md** - Add WebRTC P2P to protocol matrix
7. **01_components.md** - Add note about application packages

---

## 📊 Summary Statistics

| Status | Count | Files |
|--------|-------|-------|
| ❌ **Critical Issues** | 4 | 02_backend.md, 03_frontend.md, 05_security.md, 08_workspace_strategy.md |
| ⚠️ **Needs Update** | 1 | _index.md |
| ✅ **Accurate** | 5 | 01_components.md, 02_domains.md, 04_data_flow.md, 06_integration.md, 07_templates.md |
| ➕ **Minor Updates** | 2 | 01_components.md (add packages note), 04_data_flow.md (add WebRTC) |

**Accuracy Rate**: 45% (5/11 files fully accurate)
**Critical Issues**: 36% (4/11 files with major inaccuracies)

---

## 🎯 Key Architectural Changes (v1.0 → v2.0)

To update documentation correctly, understand these fundamental changes:

### What Changed:

1. **Frontend Architecture**: Monolithic → Package-based
   - Deleted: Portal app
   - Added: FFS4-8 application packages (~165 kB total)
   - Pattern: Workspace protocol imports (NOT dynamic loading)

2. **Directory Structure**: Single monorepo → Separate app directories
   - Old: `collider-frontend/apps/FFS4-10/`
   - New: `FFS4_application00_ColliderSidepanelAppnodeBrowser/app/`

3. **Database**: PostgreSQL → SQLite
   - Schema unchanged, just storage backend

4. **Component Locations**: Chrome extension local → Package imports
   - Sidepanel components moved to FFS4 package
   - PiP moved to FFS5 package

5. **New Protocols**: Added WebRTC P2P + Signaling
   - Endpoint: `ws://localhost:8000/api/v1/ws/rtc/`
   - Package: FFS5 (`@collider/pip-ui`)

6. **Routing**: Static → Context-driven
   - Added: ContextManager.switchWorkspaceContext()
   - Added: workspace-router library
   - Broadcasts: CONTEXT_CHANGED messages

---

## 📝 Recommended Update Workflow

1. **Read**: [2026-02-09_frontend_architecture_restructure.md](../2026-02-09_frontend_architecture_restructure.md)
2. **Update**: Files in Priority 1 order
3. **Cross-reference**: Use implementation log for accurate details
4. **Verify**: Check against current codebase structure
5. **Commit**: One file at a time with clear descriptions

---

**Report Generated**: 2026-02-09
**Inspection Method**: Line-by-line comparison with v2.0 implementation log
**Confidence Level**: High (based on complete rebuild documentation)

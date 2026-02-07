# Phase 2 - Load Testing Plan: 50+ Sessions

**Status:** ⏸️ PLAN MODE - Awaiting your confirmation to implement

---

## Overview

**Goal:** Create 50+ sessions across all accessible levels, validate complete data persistence chain, identify all bugs/edge cases.

**Current Constraint:** No agent/tool definitions exist → **Can only test L1 sessions in Phase 2**  
**Timeline:** Can extend to L2-L4 once definitions are seeded

**Estimated Duration:**
- Creation: 10 seconds (batch API)
- Validation: 30 seconds (Firestore checks)
- Total: ~1-2 minutes

---

## Plan: Load Test 50 L1 Sessions + Comprehensive Validation

### What We'll Test

#### ✅ Achievable Now (L1 Sessions Only)
1. **Batch Creation API**
   - POST `/api/v5/containers/batch` with 50 sessions
   - Response validation (success count, IDs)
   - Error handling on invalid payloads

2. **Firestore State Validation** (Per Session)
   - ✓ Document ID format: `sess_[a-f0-9]{12}`
   - ✓ Depth field: all equal 1
   - ✓ Parent ID: all equal `usersession_enterprise@test.com`
   - ✓ Status: all "active"
   - ✓ ACL owner: all "enterprise@test.com"
   - ✓ Timestamps: all recent and valid
   - ✓ Metadata: all have title (from creation payload)

3. **ResourceLinks Validation**
   - Parent's `resources_sessions` subcollection has 50 documents
   - Each link has: `link_id`, `resource_id`, `resource_type: 'session'`, `instance_id`, `metadata`
   - All reference valid sessions

4. **UX Reflection** (Playwright)
   - Canvas shows all 50 sessions as nodes
   - Each node has correct title from creation
   - Right-click menu shows "Open", "Edit", "Delete" (not "Add")
   - Double-click opens session

#### 🔴 Cannot Test (Blocked on Definitions)
- Agent creation (requires `definition_id`)
- Tool nesting
- L2-L4 depth validation with actual agents/tools
- Terminal node (Source) enforcement with agents

---

## Test Structure

### Test 1: Batch Creation (API Level)

```python
# backend/tests/integration/test_load_sessions_50.py

@pytest.mark.integration
@pytest.mark.slow
async def test_create_50_sessions_batch(integration_client, enterprise_tier_user):
    """Create 50 L1 sessions via batch API"""
    
    # Batch 1: Sessions 1-25
    response = client.post("/api/v5/containers/batch", json={
        "operations": [
            {
                "action": "create",
                "container_type": "session",
                "data": {
                    "parent_id": "usersession_enterprise@test.com",
                    "session_metadata": {
                        "title": f"Load Test Session {i+1}",
                        "session_type": "chat"
                    }
                }
            } for i in range(25)
        ]
    })
    
    assert response.status_code == 201
    assert response.json()["success_count"] == 25
    batch_1_ids = [r["instance_id"] for r in response.json()["results"]]
    
    # Batch 2: Sessions 26-50
    response = client.post("/api/v5/containers/batch", json={
        "operations": [
            {...}  # Sessions 26-50
        ]
    })
    
    assert response.status_code == 201
    batch_2_ids = [r["instance_id"] for r in response.json()["results"]]
    
    all_session_ids = batch_1_ids + batch_2_ids
    
    # Validate: 50 unique IDs
    assert len(set(all_session_ids)) == 50
    assert all(id.startswith("sess_") for id in all_session_ids)
    
    return all_session_ids
```

**Expected Output:**
```
✅ Batch 1: 25 sessions created
✅ Batch 2: 25 sessions created
✅ All 50 IDs unique
✅ All IDs in correct format
```

### Test 2: Firestore State Validation (Database Level)

```python
@pytest.mark.integration
async def test_firestore_state_50_sessions(mock_firestore, session_ids):
    """Validate Firestore documents for all 50 sessions"""
    
    errors = []
    
    for i, session_id in enumerate(session_ids, 1):
        doc = await mock_firestore.collection("sessions").document(session_id).get()
        
        if not doc.exists:
            errors.append(f"Session {i}: Document doesn't exist in Firestore")
            continue
        
        data = doc.to_dict()
        
        # Validate each field
        checks = [
            (data.get("depth") == 1, f"depth = {data.get('depth')}, expected 1"),
            (data.get("parent_id") == "usersession_enterprise@test.com", f"parent_id mismatch"),
            (data.get("status") == "active", f"status = {data.get('status')}"),
            (data.get("acl", {}).get("owner") == "enterprise@test.com", "ACL owner mismatch"),
            ("title" in data.get("session_metadata", {}), "Missing title in metadata"),
            ("created_at" in data, "Missing created_at"),
            ("created_by" in data, "Missing created_by"),
        ]
        
        for check, msg in checks:
            if not check:
                errors.append(f"Session {i} ({session_id}): {msg}")
    
    if errors:
        print("\n".join(errors))
        assert False, f"{len(errors)} validation failures"
    
    print(f"✅ All 50 sessions validated")
    return True
```

**Expected Output:**
```
✅ Session 1: depth ✓ parent ✓ status ✓ acl ✓ metadata ✓ timestamps ✓
✅ Session 2: depth ✓ parent ✓ status ✓ acl ✓ metadata ✓ timestamps ✓
...
✅ Session 50: depth ✓ parent ✓ status ✓ acl ✓ metadata ✓ timestamps ✓
✅ All 50 sessions validated
```

### Test 3: ResourceLinks Validation (Parent-Child Relationships)

```python
@pytest.mark.integration
async def test_resourcelinks_50_sessions(mock_firestore, session_ids):
    """Validate ResourceLink documents in parent's resources_sessions subcollection"""
    
    parent_id = "usersession_enterprise@test.com"
    parent_doc = await mock_firestore.collection("usersessions").document(parent_id).get()
    
    assert parent_doc.exists, "Parent usersession doesn't exist"
    
    # Get all ResourceLinks
    links = await mock_firestore \
        .collection("usersessions") \
        .document(parent_id) \
        .collection("resources_sessions") \
        .stream()
    
    link_list = [doc.to_dict() for doc in links]
    link_resource_ids = [link["resource_id"] for link in link_list]
    
    # Validate
    assert len(link_list) == 50, f"Expected 50 links, found {len(link_list)}"
    assert set(link_resource_ids) == set(session_ids), "Link resource_ids don't match created session IDs"
    
    errors = []
    for i, link in enumerate(link_list, 1):
        required_fields = ["link_id", "resource_id", "resource_type", "instance_id"]
        for field in required_fields:
            if field not in link:
                errors.append(f"Link {i}: Missing field '{field}'")
        
        if link.get("resource_type") != "session":
            errors.append(f"Link {i}: resource_type = {link.get('resource_type')}, expected 'session'")
    
    if errors:
        assert False, "\n".join(errors)
    
    print(f"✅ All 50 ResourceLinks validated")
    return True
```

**Expected Output:**
```
✅ 50 ResourceLink documents found
✅ All resource_ids match created sessions
✅ All required fields present
✅ All resource_type = 'session'
```

### Test 4: UX Reflection (Playwright Browser Test)

```typescript
// frontend/tests/e2e/load-test-50-sessions.spec.ts

test("Load test: 50 sessions visible on canvas", async ({ page }) => {
  // 1. Navigate to workspace
  await page.goto("http://localhost:5173/workspace");
  
  // 2. Wait for canvas to load all nodes
  const nodes = page.locator(".react-flow__node-session");
  await page.waitForTimeout(3000); // Wait for Firestore sync
  
  const count = await nodes.count();
  console.log(`✅ Canvas shows ${count} session nodes`);
  expect(count).toBe(50);
  
  // 3. Sample check: Random 5 sessions exist and have correct labels
  for (let i = 1; i <= 5; i++) {
    const randomIndex = Math.floor(Math.random() * 50) + 1;
    const expectedTitle = `Load Test Session ${randomIndex}`;
    
    const node = nodes.nth(randomIndex - 1);
    const label = await node.locator(".node-label").textContent();
    
    expect(label).toContain(expectedTitle);
    console.log(`✅ Session ${randomIndex} visible with correct label`);
  }
  
  // 4. Test right-click menu on first session
  const firstNode = nodes.first();
  await firstNode.click({ button: "right" });
  
  const menu = page.locator("[role='menu']");
  await expect(menu).toBeVisible();
  
  const openOption = page.locator("text=Open");
  const editOption = page.locator("text=Edit");
  const deleteOption = page.locator("text=Delete");
  const addAgentOption = page.locator("text=Add Agent");
  
  await expect(openOption).toBeVisible();
  await expect(editOption).toBeVisible();
  await expect(deleteOption).toBeVisible();
  
  // Session menus should NOT show "Add Agent" at L1
  expect(await addAgentOption.count()).toBe(0);
  console.log("✅ Context menu correct (Open, Edit, Delete; no Add Agent)");
});
```

**Expected Output:**
```
✅ Canvas shows 50 session nodes
✅ Session 17 visible with correct label
✅ Session 42 visible with correct label
✅ Session 8 visible with correct label
✅ Session 33 visible with correct label
✅ Session 5 visible with correct label
✅ Context menu correct
```

---

## Error Collection Strategy

### Where Errors Come From

1. **API Errors** - 400/403/500 responses
2. **Firestore Inconsistencies** - Missing docs, wrong depth, invalid parent_id
3. **ResourceLink Gaps** - Missing links, duplicate IDs
4. **UX Issues** - Nodes not visible, wrong labels, menu state incorrect
5. **Performance Issues** - Batch API slow, Firestore sync delays

### Error Logging

**Real-time Console Output:**
```
[13:45:22] Starting load test: 50 sessions
[13:45:23] ✅ Batch 1: 25 created
[13:45:24] ✅ Batch 2: 25 created
[13:45:25] Validating Firestore...
[13:45:31] ✅ All 50 sessions present
[13:45:32] ✅ Depth validation: 50/50 ✓
[13:45:33] ✅ Parent ID validation: 50/50 ✓
[13:45:34] ❌ ERROR: Session 7 missing from ResourceLinks
[13:45:35] ❌ ERROR: Session 23 has wrong metadata
[13:45:36] ⚠️  UX: 49/50 nodes visible (1 missing after cache timeout)
[13:45:37] Test completed with 2 errors
```

**Machine-readable Report:**
```json
{
  "test_name": "load_test_50_sessions",
  "timestamp": "2025-12-09T13:45:37Z",
  "duration_seconds": 75,
  "phase": 2,
  "tier": "enterprise",
  
  "creation": {
    "batches": 2,
    "sessions_requested": 50,
    "sessions_created": 50,
    "success_rate": 1.0
  },
  
  "firestore_validation": {
    "documents_found": 50,
    "depth_valid": 50,
    "parent_id_valid": 50,
    "status_valid": 50,
    "acl_valid": 50,
    "metadata_valid": 48,
    "errors": [
      {
        "session_id": "sess_abc123def456",
        "field": "session_metadata.title",
        "error": "Missing or empty"
      },
      {
        "session_id": "sess_xyz789abc123",
        "field": "session_metadata.title",
        "error": "Empty string"
      }
    ]
  },
  
  "resourcelinks_validation": {
    "links_found": 49,
    "expected": 50,
    "missing_link_for": ["sess_abc123def456"],
    "errors": [
      {
        "index": 7,
        "error": "ResourceLink missing for session 7"
      }
    ]
  },
  
  "ux_validation": {
    "nodes_visible": 49,
    "expected": 50,
    "cache_timeout_issues": 1,
    "missing_nodes": ["sess_abc123def456"]
  },
  
  "overall": {
    "status": "FAILED",
    "error_count": 3,
    "warnings": 1
  }
}
```

### Where to Log Errors

- **Console:** Real-time feedback during test
- **JSON Report:** `backend/test-results/load_test_50_sessions_[timestamp].json`
- **BUG_LIST.md:** Specific issues for fixing
- **Terminal:** Summary at end

---

## TODO Mapping: Which TODO Items This Tests

| TODO Item | Covered? | Status | Notes |
|-----------|----------|--------|-------|
| Create L2 Session (BUG) | ✅ Yes | Tested at L1 | L2 blocked by cache bug P2-CACHE-001 |
| Add Agent to Session | ❌ No | Blocked | No definitions exist |
| Add Tool to Agent (L3) | ❌ No | Blocked | No definitions exist |
| Add Source (Terminal) | 🟡 Partial | Can test structure | Can't nest under agents (no agents) |
| Test Depth Limit | ✅ Yes | All at depth=1 | Validates tier allows this level |
| Delete with Cascade | ❌ No | Future test | Can add as Test 5 |

---

## Success Criteria

### ✅ PASS Conditions
- [ ] All 50 sessions created via batch API
- [ ] API response shows 50 successful operations
- [ ] All 50 documents in Firestore with depth=1
- [ ] All 50 documents have valid parent_id
- [ ] All 50 documents have correct ACL/status
- [ ] All 50 ResourceLinks created in parent
- [ ] All 50 nodes visible on canvas
- [ ] Zero errors in validation
- [ ] Test completes in < 2 minutes

### 🔴 FAIL Conditions
- [ ] Any batch response shows < 50 successes
- [ ] Any Firestore document missing or corrupted
- [ ] ResourceLink count < 50
- [ ] Depth != 1 for any session
- [ ] Parent_id mismatch for any session
- [ ] Any node fails to render on canvas
- [ ] Any validation error in report

---

## Estimated Timeline & Resources

| Phase | Duration | What |
|-------|----------|------|
| Setup | 30s | Start backend, frontend, auth |
| Batch Create | 15s | 2 API calls (50 sessions) |
| Firestore Check | 15s | Query 50 docs, validate fields |
| ResourceLinks | 10s | Query parent's subcollection |
| UX Render | 30s | Wait for Firestore sync, check canvas |
| Validation | 15s | Check all assertions |
| **Total** | **~2 min** | |

---

## Next Steps After Testing

### If All Tests Pass ✅
1. Conclude Phase 2 testing is successful
2. Begin Phase 3: Add definitions, test L2-L4 agents/tools
3. Document findings in IMPLEMENTATION_LOG.md

### If Tests Fail 🔴
1. Collect error report from JSON
2. Log specific issues to BUG_LIST.md
3. Categorize by severity/root-cause
4. Plan fixes (see "Big Fixes" section below)

### Bugs Expected to Surface
- P2-CACHE-001: New children not immediately visible (cache TTL)
- P2-EDIT-001: If we test edits, won't persist
- P2-FIRESTORE-001: Potential subcollection issues with 50 docs
- P2-UX-RENDER-001: Canvas might lag with 50 nodes
- P2-RESOURCELINK-001: Potential batch inconsistencies

---

## Big Fixes (After Testing)

Once we complete this 50-session load test and identify all bugs, we'll tackle:

### Priority 1: Unblock L2+ Testing
- [ ] Define definitions architecture (inline vs. system-provided vs. custom)
- [ ] Seed agent/tool definitions in Firestore
- [ ] Enable Agent creation from definitions
- [ ] Test L2-L4 nesting with 50-session trees

### Priority 2: Fix Data Persistence
- [ ] P2-EDIT-001: Session edits not persisting
- [ ] Add v5Api.updateSession() call
- [ ] Test edit persistence

### Priority 3: Fix Cache Invalidation
- [ ] P2-CACHE-001: New children invisible until reload
- [ ] Invalidate parent cache on child creation
- [ ] Test real-time visibility

### Priority 4: Fix Scaling Issues
- [ ] Any issues that surface at 50-session scale
- [ ] Canvas performance with many nodes
- [ ] Firestore consistency under batch load

---

## Your Decision Points

**Question 1: Proceed with 50-session load test?**
- ✅ YES - Run all 4 test categories, collect comprehensive error report
- 🔄 MAYBE - Start with just batch creation test, see what errors surface first
- ❌ NO - Skip to fixes first, come back to testing later

**Question 2: Include UX test (Playwright)?**
- ✅ YES - Full end-to-end including canvas visibility
- ❌ NO - Skip Playwright, focus on API + Firestore only (faster)

**Question 3: Depth coverage preference?**
- 📊 FLAT (50 L1 sessions) - Fast, comprehensive horizontal testing
- 🌳 TREE (nested L1-L2-L3) - Requires agents/definitions (blocked)

**Question 4: On errors, stop or continue?**
- ⛔ STOP - Fail on first error (strict)
- 📋 CONTINUE - Collect all errors, report at end

---

## Files to Create/Modify

```
NEW:
  backend/tests/integration/test_load_sessions_50.py
  frontend/tests/e2e/load-test-50-sessions.spec.ts
  test-results/load_test_50_sessions_[timestamp].json

MODIFY:
  BUG_LIST.md (add any new issues found)
  IMPLEMENTATION_LOG.md (document test results)
```

---

## Summary

**Plan: Create 50+ L1 sessions, validate complete persistence chain, identify all bugs**

- **4 Test Categories:** Batch API, Firestore State, ResourceLinks, UX
- **Estimated Time:** ~2 minutes
- **Expected Issues:** Cache visibility, metadata persistence, scale effects
- **Outcome:** Comprehensive bug report + readiness for Phase 3 fixes

**Ready to implement?** Confirm your answers above and I'll execute all 4 tests!

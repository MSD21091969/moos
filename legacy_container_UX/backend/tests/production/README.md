# Production Tests

**Validation tests for deployed infrastructure**

---

## Tests

### test_production_chatagent.py

**Purpose**: Validate Cloud Run backend API (10 tests)

**Tests**:
1. ✅ Health check
2. ✅ Authentication (JWT)
3. ✅ Session CRUD
4. ✅ Tools discovery
5. ✅ Agent execution
6. ✅ Rate limiting
7. ✅ Streaming (SSE)
8. ✅ Document upload
9. ✅ Tool execution
10. ✅ Quota tracking

**Usage**:
```powershell
cd tests/production
python test_production_chatagent.py

# Expected: 10/10 passing in ~2 seconds
```

### test_production_sdk.py

**Purpose**: Validate Python SDK against production (5 tests)

**Tests**:
1. ✅ Client initialization (JWT)
2. ✅ User info retrieval
3. ✅ Session management
4. ✅ Agent execution
5. ✅ Session cleanup

**Usage**:
```powershell
cd tests/production
python test_production_sdk.py

# Expected: 5/5 passing in ~2 seconds
```

---

## Configuration

**Required Environment**:
- Backend deployed to Cloud Run
- Test user exists: `test@test.com` / `test123`
- ENTERPRISE tier with 10k quota

**URLs**:
- Backend: https://my-tiny-data-collider-ng2rb7mwyq-ez.a.run.app
- Frontend: https://frontend-h82zowkjy-sams-projects-5a778627.vercel.app

---

## Results

Test results are written to JSON files:
- `test_production_results.json` (API tests)
- `test_production_sdk_results.json` (SDK tests)

**Note**: Result files are gitignored (ephemeral data).

---

## CI Integration

These tests can be added to CI pipeline for deployment validation:

```yaml
# .github/workflows/validate-production.yml
- name: Validate Production
  run: |
    python tests/production/test_production_chatagent.py
    python tests/production/test_production_sdk.py
```

---

*See [main test documentation](../README.md) for unit/integration tests*

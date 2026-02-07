# Test Suite Documentation

**Comprehensive test coverage for My Tiny Data Collider**

---

## Test Results

**Current Status**: 586/588 tests passing (99.7%)

| Category | Tests | Status | Coverage |
|----------|-------|--------|----------|
| **Unit Tests** | 508/508 | ✅ 100% | 63% avg |
| **Integration Tests** | 63/63 | ✅ 100% | - |
| **Production API Tests** | 10/10 | ✅ 100% | - |
| **Production SDK Tests** | 5/5 | ✅ 100% | - |
| **Deferred** | 2 | ⏸️ Documented | - |
| **Total** | 586/588 | ✅ 99.7% | 63% |

---

## Running Tests

### Quick Commands

```powershell
# All unit tests (fast ~2 min)
pytest tests/unit/ -v

# With coverage
pytest tests/unit/ --cov=src --cov-report=html
# Open htmlcov/index.html

# Integration tests (~5 min)
pytest tests/integration/ -v

# Specific layer
pytest tests/unit/api/ -v              # Routes (56 tests)
pytest tests/unit/services/ -v         # Services (46 tests)
pytest tests/unit/tools/ -v            # Tools (40 tests)

# Specific file
pytest tests/unit/api/test_api_routes_sessions_fixed_2025-11-02.py -v

# Specific test
pytest tests/unit/services/test_services_auth_service_fixed_2025-11-02.py::test_login_success -v

# Re-run last failed
pytest --lf -v

# Stop on first failure
pytest -x

# Verbose with print statements
pytest -v -s
```

---

## Test Structure

```
tests/
├── conftest.py                       # Shared fixtures (client, mock_firestore, user_ctx)
│
├── unit/                             # Fast, isolated tests (508 tests)
│   ├── README.md                     # Test organization guide
│   │
│   ├── api/                          # Route tests (56 tests, 100%)
│   │   ├── test_api_routes_sessions_fixed_2025-11-02.py  # 18 tests
│   │   ├── test_api_routes_agent_fixed_2025-11-02.py     # 7 tests
│   │   ├── test_api_routes_auth_fixed_2025-11-02.py      # 3 tests
│   │   ├── test_api_routes_documents_fixed_2025-11-02.py # 11 tests
│   │   ├── test_api_routes_tools_fixed_2025-11-02.py     # 6 tests
│   │   ├── test_api_routes_rate_limit_fixed_2025-11-02.py # 3 tests
│   │   ├── test_api_routes_jobs_fixed_2025-11-02.py      # 3 tests
│   │   ├── test_api_routes_user_fixed_2025-11-02.py      # 3 tests
│   │   └── DEFERRED_API_TESTS.md     # Missing service methods (9 methods)
│   │
│   ├── services/                     # Service tests (46 tests, 100%)
│   │   ├── test_services_quota_service_fixed_2025-11-02.py      # 10 tests
│   │   ├── test_services_auth_service_fixed_2025-11-02.py       # 11 tests
│   │   ├── test_services_document_service_fixed_2025-11-02.py   # 11 tests
│   │   ├── test_services_session_service_fixed_2025-11-02.py    # 9 tests
│   │   ├── test_services_tool_service_fixed_2025-11-02.py       # 5 tests
│   │   ├── test_services_agent_service_2025-11-02.py            # 6 tests
│   │   └── DEFERRED_TESTS.md         # Cache decorator type mutation (2 tests)
│   │
│   ├── tools/                        # Tool tests (40 tests, 100%)
│   │   ├── test_export_tools_2025-11-02.py      # 11 tests
│   │   ├── test_text_tools_2025-11-02.py        # 16 tests
│   │   └── test_transform_tools_2025-11-02.py   # 13 tests
│   │
│   ├── core/                         # Core utilities (~127 tests)
│   ├── models/                       # Model validation (~81 tests)
│   ├── persistence/                  # Database tests (~11 tests)
│   └── agents/                       # Agent tests (~8 tests)
│
└── integration/                      # Multi-component tests (63 tests)
    ├── README.md
    └── test_session_lifecycle.py     # Full workflow validation
```

---

## Test Fixtures

### Common Fixtures (conftest.py)

```python
# TestClient for API testing
@pytest.fixture
def client() -> TestClient:
    """FastAPI test client with mocked Firestore"""
    return TestClient(app)

# Mock Firestore for fast tests
@pytest.fixture
def mock_firestore() -> MockFirestoreClient:
    """In-memory Firestore mock"""
    return MockFirestoreClient()

# Sample domain objects
@pytest.fixture
def sample_session() -> Session:
    """Pre-configured test session"""
    return Session(
        session_id="sess_test123",
        user_id="user_test",
        tier="PRO",
        ...
    )

# User context for auth
@pytest.fixture
def user_ctx() -> UserContext:
    """Test user context"""
    return UserContext(
        user_id="user_test",
        email="test@test.com",
        tier=Tier.PRO,
        ...
    )
```

---

## Test Patterns

### 1. Unit Test Pattern

```python
def test_feature_success():
    """
    TEST: Feature works with valid input
    PURPOSE: Verify happy path
    VALIDATES: Expected output
    EXPECTED: Success result
    """
    # Arrange
    input_data = {...}
    
    # Act
    result = my_function(input_data)
    
    # Assert
    assert result == expected_output
    assert result.status == "success"
```

### 2. API Test Pattern

```python
def test_endpoint_success(client: TestClient):
    """
    TEST: POST /endpoint returns 200
    PURPOSE: Verify endpoint behavior
    VALIDATES: Response structure
    EXPECTED: Valid response model
    """
    # Arrange
    headers = {"Authorization": "Bearer token"}
    payload = {"key": "value"}
    
    # Act
    response = client.post("/endpoint", json=payload, headers=headers)
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
```

### 3. Service Test Pattern

```python
@pytest.mark.asyncio
async def test_service_operation(mock_firestore: MockFirestoreClient):
    """
    TEST: Service method handles business logic
    PURPOSE: Verify service layer isolation
    VALIDATES: Domain logic correctness
    EXPECTED: Returns domain object
    """
    # Arrange
    service = MyService(mock_firestore)
    user_ctx = UserContext(...)
    
    # Act
    result = await service.do_operation(user_ctx, ...)
    
    # Assert
    assert isinstance(result, DomainModel)
    assert result.field == expected_value
```

---

## Coverage Targets

**Current Coverage**: 63%

### Well-Covered (90-100%)
- ✅ Tools: 100% (export, text, transform)
- ✅ Core middleware: 100%
- ✅ Core security: 100%
- ✅ Models: 100% (events, users, documents)
- ✅ Persistence: 100%

### Good Coverage (70-89%)
- ✅ API routes: 74% average
- ✅ Services: 74% average
- ✅ Core utilities: 82-94%

### Needs Improvement (0-69%)
- ⚠️ SDK: 0% (only production validation tests)

**Goals**:
- Minimum: 70% (CI requirement)
- Target: 90%
- Critical paths: 100% (auth, quota, security)

---

## Production Tests

### API Validation (test_production_chatagent.py)

10 tests validating deployed Cloud Run backend:

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

```powershell
python tests/production/test_production_chatagent.py
# Expected: 10/10 tests passing in ~2 seconds
```

### SDK Validation (test_production_sdk.py)

5 tests validating Python SDK:

1. ✅ Client initialization (JWT)
2. ✅ User info retrieval
3. ✅ Session management
4. ✅ Agent execution
5. ✅ Session cleanup

```powershell
python tests/production/test_production_sdk.py
# Expected: 5/5 tests passing in ~2 seconds
```

---

## Deferred Tests

### Cache Decorator Type Mutation (2 tests)

**Location**: `tests/unit/services/DEFERRED_TESTS.md`

**Issue**: Cache decorator changes return type from domain object to tuple
**Impact**: Low (caching works, type signature incorrect)
**Priority**: Medium (fix in Phase 2)

### Missing Service Methods (9 methods)

**Location**: `tests/unit/api/DEFERRED_API_TESTS.md`

**Missing**:
- Session sharing endpoints (share, unshare, transfer)
- Background job triggers
- Advanced quota operations

**Status**: Documented, will implement based on user needs

---

## CI Requirements

**GitHub Actions** runs on every push/PR:

```yaml
✅ Ruff check: 0 errors
✅ Ruff format: No changes
✅ MyPy: 0 type errors
✅ Pytest: All tests passing
✅ Coverage: ≥70%
✅ Docker: Build successful
```

**Failure = PR blocked**

---

## Troubleshooting

### Common Issues

**1. Tests fail locally but pass in CI**
```powershell
# Clear pytest cache
pytest --cache-clear

# Reinstall dependencies
pip install -e ".[dev]" --force-reinstall
```

**2. Coverage drops unexpectedly**
```powershell
# Remove old coverage data
Remove-Item .coverage -Force
Remove-Item -Recurse -Force htmlcov/

# Re-run with coverage
pytest --cov=src --cov-report=html
```

**3. Slow tests**
```powershell
# Run in parallel (requires pytest-xdist)
pytest -n auto

# Run fastest tests first
pytest --ff  # Failed first
```

**4. Import errors**
```powershell
# Ensure editable install
pip install -e .

# Verify PYTHONPATH
$env:PYTHONPATH="C:\Users\Geurt\my-tiny-data-collider"
```

---

## Related Documentation

- **[Development Guide](../docs/development/README.md)**: Local setup
- **[Contributing Guide](../CONTRIBUTING.md)**: Code standards
- **[Architecture Guide](../docs/architecture/README.md)**: System design

---

*Last updated: 2025-11-10*

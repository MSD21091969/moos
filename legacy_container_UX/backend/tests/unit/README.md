# Unit Tests

**Status**: 473/475 passing (99.6%) | **Coverage**: 69% (4412 lines)

## Structure

```
tests/unit/
├── api/                 # 56 tests - FastAPI routes (8 endpoints)
├── services/            # 46 tests - Business logic (6 services)
├── tools/               # 40 tests - Agent tools (3 modules)
├── core/                # 127 tests - Infrastructure (18 modules)
├── models/              # 81 tests - Pydantic models (7 modules)
├── persistence/         # 11 tests - Firestore clients (2 modules)
└── agents/              # 8 tests - PydanticAI agents (1 module)
```

## Quick Start

```bash
# All unit tests
pytest tests/unit/ -v

# Category-specific
pytest tests/unit/api/ -v           # 56 tests
pytest tests/unit/services/ -v      # 46 tests
pytest tests/unit/tools/ -v         # 40 tests

# Coverage report
pytest tests/unit/ --cov=src --cov-report=html
# Open htmlcov/index.html
```

## Test Commands

```bash
# Single file
pytest tests/unit/api/test_api_routes_sessions_fixed_2025-11-02.py -v

# Single test
pytest tests/unit/api/test_api_routes_sessions_fixed_2025-11-02.py::TestCreateSession::test_create_session_success -v

# Stop on first failure
pytest tests/unit/ -x

# Parallel execution
pytest tests/unit/ -n auto
```

## Test Inventory

**API Routes (56 tests)**:
- sessions (18), agent (7), auth (3), documents (11), tools (6), rate_limit (3), jobs (3), user (3), UI (2)

**Services (46 tests)**:
- quota (10), auth (11), documents (11), sessions (9), tools (5)

**Tools (40 tests)**:
- export (11), text (16), transform (13)

**Passing Rate**: 99.6% (473/475)

**Deferred (2 tests)**:
1. `test_core_secrets_google_cloud` - Missing optional dependency
2. `test_services_document_file_size_limits` - Phase 2 feature

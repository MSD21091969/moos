# Scripts Documentation

**Utility scripts for My Tiny Data Collider**

> **NOTE:** The primary entry points for the full application are in the root `scripts/` folder (e.g., `start-dev-environment.ps1`). The scripts in this folder are primarily for backend-specific tasks or mock modes.

## Directory Structure

```
scripts/
├── README.md               # This file
├── development/            # Dev environment scripts
│   ├── dev.ps1            # Start full dev stack
│   ├── start_server.ps1   # Start backend only
│   └── stop.ps1           # Stop all services
├── testing/               # Testing utilities
│   ├── activate_test_user.py
│   ├── check_firestore_users.py
│   ├── create_test_user.py
│   └── compare_openapi_specs.py
└── deployment/            # Deployment tools
    └── setup-mcp-tools.ps1
```

---

## Quick Reference

| Script | Purpose | Usage |
|--------|---------|-------|
| **testing/create_test_user.py** | Create single test user | `python scripts/testing/create_test_user.py` |
| **testing/check_firestore_users.py** | List all Firestore users | `python scripts/testing/check_firestore_users.py` |
| **development/dev.ps1** | Start dev environment | `./scripts/development/dev.ps1` |
| **development/start_server.ps1** | Start backend server | `./scripts/development/start_server.ps1` |
| **development/stop.ps1** | Stop services | `./scripts/development/stop.ps1` |
| **deployment/setup-mcp-tools.ps1** | Setup MCP tools | `./scripts/deployment/setup-mcp-tools.ps1` |
| **deployment/tail-cloud-run-logs.ps1** | Tail / fetch Cloud Run logs | `./scripts/deployment/tail-cloud-run-logs.ps1 -ProjectId <id> [-Tail]` |

---

## User Management

### testing/create_test_user.py

**Purpose**: Create a single test user with custom settings

**Usage**:
```powershell
# Interactive mode
python scripts/create_test_user.py

# Will prompt for:
# - Email
# - Password
# - Tier (FREE/PRO/ENTERPRISE)
```

**Features**:
- Bcrypt password hashing (72-byte limit)
- Automatic quota assignment
- Validation for duplicate emails

### check_firestore_users.py

**Purpose**: List all users in Firestore database

**Usage**:
```powershell
# List all users
python scripts/check_firestore_users.py

# Output:
# Users in Firestore:
# - test@example.com (ENTERPRISE, quota: 10000)
# - pro@example.com (PRO, quota: 1000)
```

**Use Cases**:
- Verify user creation
- Debug authentication issues
- Check quota assignments

---

## Deployment

### deploy-cloud.ps1

**Purpose**: Automated deployment to Google Cloud Run

**Usage**:
```powershell
# Deploy to production
./scripts/deploy-cloud.ps1

# Script performs:
# 1. Build Docker image
# 2. Tag for Artifact Registry
# 3. Push to registry
# 4. Deploy to Cloud Run
# 5. Verify health check
```

**Requirements**:
- Google Cloud SDK installed
- Docker running
- Authenticated with GCP (`gcloud auth login`)
- Required secrets in Secret Manager

**Environment**:
- Region: europe-west4
- Memory: 1024Mi
- CPU: 2 vCPU
- Max instances: 20

### tail-cloud-run-logs.ps1

**Purpose**: Inspect Cloud Run logs without leaving the terminal

**Usage**:
```powershell
# Tail logs continuously (requires gcloud auth)
./scripts/deployment/tail-cloud-run-logs.ps1 -ProjectId my-gcp-project -Tail

# Fetch last 100 entries as JSON
./scripts/deployment/tail-cloud-run-logs.ps1 -ProjectId my-gcp-project -Limit 100 > logs.json
```

**Notes**:
- Falls back to `GCP_PROJECT_ID` environment variable when `-ProjectId` is omitted
- Uses `gcloud beta logging tail` for live streaming
- Helpful when Logfire trace sampling misses application startup failures

---

## Development

### dev.ps1

**Purpose**: Quick development environment setup

**Usage**:
```powershell
# Start backend + frontend
./scripts/dev.ps1

# Runs:
# - Backend: uvicorn src.main:app --reload
# - Frontend: cd frontend && npm run dev
```

**Ports**:
- Backend: http://localhost:8000
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs

### setup-mcp-tools.ps1

**Purpose**: Configure Model Context Protocol tools

**Usage**:
```powershell
# Setup MCP integration
./scripts/setup-mcp-tools.ps1
```

**Configures**:
- GitHub MCP tool
- Filesystem MCP tool
- Sequential thinking tool

---

## Testing

### run-tests.ps1

**Purpose**: Run test suite with coverage

**Usage**:
```powershell
# All tests with coverage
./scripts/run-tests.ps1

# Generates:
# - Terminal coverage summary
# - HTML coverage report (htmlcov/)
```

**Options**:
```powershell
# Unit tests only
./scripts/run-tests.ps1 unit

# Integration tests only
./scripts/run-tests.ps1 integration

# With verbose output
./scripts/run-tests.ps1 -v
```

---

## Utilities

### compare_openapi_specs.py

**Purpose**: Compare OpenAPI spec changes between versions

**Usage**:
```powershell
# Compare specs
python scripts/compare_openapi_specs.py \
  --old specs/openapi-v1.json \
  --new openapi.json

# Output:
# - New endpoints
# - Removed endpoints
# - Changed schemas
```

**Use Cases**:
- API versioning
- Breaking change detection
- Documentation updates

---

## Script Development Guidelines

### Creating New Scripts

**Python Scripts**:
```python
#!/usr/bin/env python3
"""
Script: my_script.py
Purpose: Brief description
Usage: python scripts/my_script.py
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import settings

def main():
    """Main execution"""
    pass

if __name__ == "__main__":
    main()
```

**PowerShell Scripts**:
```powershell
<#
.SYNOPSIS
    Brief description

.DESCRIPTION
    Detailed description

.EXAMPLE
    ./scripts/my_script.ps1
#>

# Set error action
$ErrorActionPreference = "Stop"

# Script logic
Write-Host "Starting..."
```

### Best Practices

1. **Documentation**: Add header comment with purpose and usage
2. **Error Handling**: Use try/catch and meaningful error messages
3. **Environment**: Check prerequisites before execution
4. **Logging**: Use structured logging for debugging
5. **Testing**: Validate script behavior in dev before production

---

## Troubleshooting

### Common Issues

**1. "Module not found" errors**
```powershell
# Ensure virtual environment is activated
.\.venv\Scripts\Activate.ps1

# Reinstall dependencies
pip install -e ".[dev]"
```

**2. "Permission denied" on PowerShell scripts**
```powershell
# Set execution policy (one-time)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Or run with bypass
powershell -ExecutionPolicy Bypass -File ./scripts/my_script.ps1
```

**3. "GOOGLE_APPLICATION_CREDENTIALS not found"**
```powershell
# Set environment variable
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\service-account.json"

# Or use mock mode
$env:USE_FIRESTORE_MOCKS="true"
```

**4. Docker not running**
```powershell
# Start Docker Desktop
# Verify Docker is running
docker ps
```

---

## Related Documentation

- **[Development Guide](../docs/development/README.md)**: Local setup
- **[Deployment Guide](../docs/deployment/README.md)**: Cloud deployment
- **[Contributing Guide](../CONTRIBUTING.md)**: Development workflow

---

*Last updated: 2025-11-10*

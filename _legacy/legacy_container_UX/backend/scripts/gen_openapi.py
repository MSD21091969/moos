#!/usr/bin/env python3
"""Generate OpenAPI schema with mocked Google Cloud dependencies.

This script works around Python 3.14 incompatibility with google-cloud-firestore
by mocking the Google Cloud imports before loading the FastAPI app.
"""
import sys
import os
from pathlib import Path

# Mock Google Cloud before any imports
class MockClass:
    """Mock class that returns itself for any attribute or call."""
    def __init__(self, *args, **kwargs): pass
    def __getattr__(self, name): return MockClass()
    def __call__(self, *args, **kwargs): return MockClass()
    def __iter__(self): return iter([])
    def __bool__(self): return False
    def __mro_entries__(self, bases): return (object,)

class MockModule:
    """Mock module that returns MockClass for any attribute."""
    def __getattr__(self, name): return MockClass()
    Client = MockClass
    AsyncClient = MockClass
    firestore = MockClass()
    Credentials = MockClass
    ReadOnlyScoped = object
    CredentialsWithQuotaProject = object
    GoogleCloudError = Exception
    NotFound = Exception

# Install mocks BEFORE any app imports
for mod in [
    'google.cloud',
    'google.cloud.firestore',
    'google.cloud.firestore_v1',
    'google.cloud.firestore_v1._helpers',
    'google.cloud.firestore_v1.async_client',
    'google.cloud.firestore_v1.client',
    'google.cloud.exceptions',
    'google.cloud.storage',
    'google.auth',
    'google.auth.credentials',
    'google.auth.transport',
    'google.auth.transport.requests',
    'google.api_core',
    'google.api_core.gapic_v1',
    'google.api_core.exceptions',
    'google.oauth2',
    'google.oauth2.credentials',
    'google.oauth2.id_token',
    'google_auth_oauthlib',
    'google_auth_oauthlib.flow',
]:
    sys.modules[mod] = MockModule()

# Set environment for test mode
os.environ['ENVIRONMENT'] = 'test'
os.environ['SKIP_FIREBASE_INIT'] = '1'
os.environ['USE_FIRESTORE_MOCKS'] = 'true'
os.environ['JWT_SECRET_KEY'] = 'test_secret_for_openapi_gen'
os.environ['LOGFIRE_TOKEN'] = ''
os.environ['REDIS_ENABLED'] = 'false'

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

def main():
    import json
    from typing import Any
    
    # Now safe to import app
    from src.main import app
    
    # Get OpenAPI schema
    schema = app.openapi()
    
    # Fix $ref+default violations (OpenAPI 3.1.0 compliance)
    def fix_ref_with_default(node: Any) -> tuple[int, Any]:
        fix_count = 0
        
        def fix_node(n: Any) -> Any:
            nonlocal fix_count
            if isinstance(n, dict):
                if "$ref" in n and len(n) > 1:
                    ref_value = n.pop("$ref")
                    n["allOf"] = [{"$ref": ref_value}]
                    fix_count += 1
                for key, value in n.items():
                    n[key] = fix_node(value)
            elif isinstance(n, list):
                return [fix_node(item) for item in n]
            return n
        
        return fix_count, fix_node(node)
    
    fix_count, schema = fix_ref_with_default(schema)
    
    # Write to file
    output_path = backend_dir / "openapi-schema.json"
    with open(output_path, "w") as f:
        json.dump(schema, f, indent=2)
    
    print(f"✅ OpenAPI schema exported to {output_path}")
    print(f"   Version: {schema['info']['version']}")
    print(f"   Paths: {len(schema['paths'])}")
    print(f"   Schemas: {len(schema.get('components', {}).get('schemas', {}))}")
    if fix_count > 0:
        print(f"   Fixed: {fix_count} $ref+default violations")

if __name__ == "__main__":
    main()

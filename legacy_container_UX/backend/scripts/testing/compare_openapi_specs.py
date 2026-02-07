#!/usr/bin/env python3
"""
OpenAPI Spec Comparison Script for CI
Compares generated OpenAPI spec with committed spec to detect drift.
Strict mode: Fails CI if any undocumented endpoints are detected.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, Set, Tuple


def normalize_json(data: Any) -> str:
    """Normalize JSON for comparison (sorted keys, consistent formatting)."""
    return json.dumps(data, sort_keys=True, indent=2)


def extract_endpoints(spec: Dict[str, Any]) -> Set[Tuple[str, str]]:
    """Extract (path, method) tuples from OpenAPI spec."""
    endpoints = set()
    paths = spec.get("paths", {})
    for path, methods in paths.items():
        for method in methods.keys():
            if method in ["get", "post", "put", "patch", "delete", "options", "head"]:
                endpoints.add((path, method.upper()))
    return endpoints


def compare_specs(committed_spec: Dict, generated_spec: Dict) -> Tuple[bool, str]:
    """
    Compare two OpenAPI specs and return (is_valid, message).
    
    Strict mode validation:
    - New endpoints in generated spec = FAIL (undocumented)
    - Removed endpoints = WARNING (not a failure)
    - Schema changes = INFO (not a failure for now)
    """
    committed_endpoints = extract_endpoints(committed_spec)
    generated_endpoints = extract_endpoints(generated_spec)
    
    new_endpoints = generated_endpoints - committed_endpoints
    removed_endpoints = committed_endpoints - generated_endpoints
    
    messages = []
    
    # Check for undocumented endpoints (STRICT MODE - FAIL)
    if new_endpoints:
        messages.append("\n❌ UNDOCUMENTED ENDPOINTS DETECTED (CI FAILURE)\n")
        messages.append("The following endpoints exist in the running app but are NOT in openapi.json:\n")
        for path, method in sorted(new_endpoints):
            messages.append(f"  - {method} {path}")
        messages.append("\n💡 Fix: Run the app locally and regenerate openapi.json:")
        messages.append("   python -c \"import json; from src.main import app; print(json.dumps(app.openapi(), indent=2))\" > openapi.json")
        messages.append("   Then commit the updated openapi.json file.\n")
    
    # Check for removed endpoints (WARNING - not a failure)
    if removed_endpoints:
        messages.append("\n⚠️  REMOVED ENDPOINTS DETECTED (WARNING)\n")
        messages.append("The following endpoints are in openapi.json but NOT in the running app:\n")
        for path, method in sorted(removed_endpoints):
            messages.append(f"  - {method} {path}")
        messages.append("\n💡 This may be intentional (deprecated endpoints), but verify it's expected.\n")
    
    # Check for schema drift (full spec comparison)
    committed_norm = normalize_json(committed_spec)
    generated_norm = normalize_json(generated_spec)
    
    if committed_norm != generated_norm and not new_endpoints and not removed_endpoints:
        messages.append("\n📝 SCHEMA CHANGES DETECTED (INFO)\n")
        messages.append("OpenAPI schemas differ but endpoints are the same.")
        messages.append("This may be due to:")
        messages.append("  - Updated request/response models")
        messages.append("  - Changed descriptions or examples")
        messages.append("  - Modified validation rules\n")
        messages.append("💡 Review the diff artifact and update openapi.json if changes are intentional.\n")
    
    if not messages:
        messages.append("✅ OpenAPI spec is up to date!\n")
    
    # STRICT MODE: Fail only if new undocumented endpoints exist
    is_valid = len(new_endpoints) == 0
    
    return is_valid, "\n".join(messages)


def main():
    """Main comparison logic."""
    if len(sys.argv) != 3:
        print("Usage: python compare_openapi_specs.py <committed_spec.json> <generated_spec.json>")
        sys.exit(1)
    
    committed_path = Path(sys.argv[1])
    generated_path = Path(sys.argv[2])
    
    # Load specs
    try:
        with open(committed_path, "r", encoding="utf-8") as f:
            committed_spec = json.load(f)
    except FileNotFoundError:
        print(f"❌ ERROR: Committed spec not found: {committed_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ ERROR: Invalid JSON in committed spec: {e}")
        sys.exit(1)
    
    try:
        with open(generated_path, "r", encoding="utf-8") as f:
            generated_spec = json.load(f)
    except FileNotFoundError:
        print(f"❌ ERROR: Generated spec not found: {generated_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ ERROR: Invalid JSON in generated spec: {e}")
        sys.exit(1)
    
    # Compare
    is_valid, message = compare_specs(committed_spec, generated_spec)
    
    print("=" * 80)
    print("OpenAPI Spec Comparison Report")
    print("=" * 80)
    print(message)
    
    # Exit with appropriate code
    if is_valid:
        print("✅ CI PASSED: OpenAPI spec validation successful")
        sys.exit(0)
    else:
        print("❌ CI FAILED: Undocumented endpoints detected (strict mode)")
        sys.exit(1)


if __name__ == "__main__":
    main()

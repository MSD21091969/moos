#!/usr/bin/env python3
"""Export OpenAPI schema directly from FastAPI app without HTTP request.

Includes post-processing to fix OpenAPI 3.1.0 validation issues caused by
Pydantic v2 generating invalid `$ref` + `default` combinations.
"""
import json
import sys
from pathlib import Path
from typing import Any

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))


def fix_ref_with_default(schema: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    """
    Fix OpenAPI 3.1.0 validation error: $ref cannot have sibling keywords.
    
    Pydantic v2 generates `{"$ref": "...", "default": "..."}` for enum fields
    with defaults, which violates OpenAPI 3.1.0 spec. 
    
    Fix: Wrap $ref in allOf when default is present.
    
    Before: {"$ref": "#/components/schemas/Foo", "default": "bar"}
    After:  {"allOf": [{"$ref": "#/components/schemas/Foo"}], "default": "bar"}
    
    Returns:
        Tuple of (fix_count, fixed_schema)
    """
    fix_count = 0
    
    def fix_node(node: Any) -> Any:
        nonlocal fix_count
        
        if isinstance(node, dict):
            # Check if this node has $ref with siblings (like default)
            if "$ref" in node and len(node) > 1:
                ref_value = node.pop("$ref")
                # Wrap $ref in allOf, keep other properties at same level
                node["allOf"] = [{"$ref": ref_value}]
                fix_count += 1
            
            # Recursively process all values
            for key, value in node.items():
                node[key] = fix_node(value)
                
        elif isinstance(node, list):
            return [fix_node(item) for item in node]
        
        return node
    
    fixed = fix_node(schema)
    return fix_count, fixed


if __name__ == "__main__":
    from src.main import app
    
    # Get the OpenAPI schema directly from the app
    schema = app.openapi()
    
    # Fix OpenAPI 3.1.0 validation issues
    fix_count, schema = fix_ref_with_default(schema)
    if fix_count > 0:
        print(f"🔧 Fixed {fix_count} $ref+default violations")
    
    # Write to file
    output_path = Path(__file__).parent / "openapi-schema.json"
    with open(output_path, "w") as f:
        json.dump(schema, f, indent=2)
    
    print(f"✅ OpenAPI schema exported to {output_path}")
    print(f"   Size: {output_path.stat().st_size} bytes")

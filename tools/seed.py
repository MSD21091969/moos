"""Export tools for seeding definitions to the Collider."""
import json
from pathlib import Path
from typing import Optional


def export_to_collider(
    definition_path: str,
    collider_path: str = "D:/my-tiny-data-collider",
    **kwargs
) -> str:
    """Export a validated definition to Collider format.
    
    Args:
        definition_path: Path to the definition to export
        collider_path: Path to the Collider project
        
    Returns:
        Export confirmation
    """
    from definitions.base import ColliderAgentDefinition
    
    def_path = Path(definition_path)
    if not def_path.is_absolute():
        def_path = Path(__file__).parent.parent / "definitions" / definition_path
    
    if not def_path.exists():
        return f"Error: Definition not found at {def_path}"
    
    collider = Path(collider_path)
    if not collider.exists():
        return f"Error: Collider path not found at {collider}"
    
    # Read and exec the definition to get the object
    content = def_path.read_text(encoding="utf-8")
    
    # Extract definition name (look for CAPS variable assignments)
    import ast
    tree = ast.parse(content)
    
    definitions_found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    definitions_found.append(target.id)
    
    if not definitions_found:
        return "No definition constants found (looking for UPPERCASE names)"
    
    # Create export directory
    export_dir = collider / "runtime" / "agents"
    export_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy the definition file
    export_path = export_dir / def_path.name
    export_path.write_text(content, encoding="utf-8")
    
    return f"""## Export Complete

**Source**: {def_path}
**Destination**: {export_path}
**Definitions found**: {', '.join(definitions_found)}

The definition is now available in the Collider at:
  `runtime/agents/{def_path.name}`

Import in Collider:
```python
from runtime.agents.{def_path.stem} import {definitions_found[0]}
```
"""


def list_collider_agents(collider_path: str = "D:/my-tiny-data-collider", **kwargs) -> str:
    """List agents already in the Collider."""
    collider = Path(collider_path)
    agents_dir = collider / "runtime" / "agents"
    
    if not agents_dir.exists():
        return "No agents directory in Collider yet."
    
    agents = list(agents_dir.glob("*.py"))
    
    if not agents:
        return "No agents exported to Collider yet."
    
    result = ["## Collider Agents\n"]
    for a in agents:
        result.append(f"- `{a.name}`")
    
    return "\n".join(result)

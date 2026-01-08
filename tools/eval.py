"""Meta-tools for evaluating and improving definitions."""
import ast
import json
from pathlib import Path
from typing import Optional


DEFINITIONS_DIR = Path(__file__).parent.parent / "definitions"


def read_definition(path: str, **kwargs) -> str:
    """Read and parse a definition file.
    
    Args:
        path: Path to definition file (relative to definitions/ or absolute)
        
    Returns:
        Definition content and parsed structure
    """
    # Resolve path
    p = Path(path)
    if not p.is_absolute():
        p = DEFINITIONS_DIR / path
    
    if not p.exists():
        return f"Error: Definition not found at {p}"
    
    content = p.read_text(encoding="utf-8")
    
    # Parse to extract key info
    try:
        tree = ast.parse(content)
        classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        functions = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        assigns = [n.targets[0].id for n in ast.walk(tree) 
                   if isinstance(n, ast.Assign) and n.targets 
                   and isinstance(n.targets[0], ast.Name)]
    except SyntaxError as e:
        return f"Syntax error in {p}: {e}"
    
    return f"""## Definition: {p.name}

**Path**: {p}
**Classes**: {', '.join(classes) or 'None'}
**Functions**: {', '.join(functions) or 'None'}
**Top-level assignments**: {', '.join(assigns) or 'None'}

### Source:
```python
{content}
```
"""


def list_definitions(**kwargs) -> str:
    """List all available definitions."""
    defs = list(DEFINITIONS_DIR.glob("*.py"))
    
    result = ["## Available Definitions\n"]
    for d in defs:
        if d.name.startswith("_"):
            continue
        result.append(f"- `{d.name}`")
    
    return "\n".join(result)


def eval_definition(path: str, **kwargs) -> str:
    """Evaluate a definition and score it.
    
    Args:
        path: Path to definition file
        
    Returns:
        Evaluation report with scores
    """
    p = Path(path)
    if not p.is_absolute():
        p = DEFINITIONS_DIR / path
    
    if not p.exists():
        return f"Error: Definition not found at {p}"
    
    content = p.read_text(encoding="utf-8")
    
    # Scoring criteria
    scores = {}
    
    # 1. Documentation (docstrings)
    has_module_doc = content.strip().startswith('"""') or content.strip().startswith("'''")
    scores["documentation"] = 100 if has_module_doc else 50
    
    # 2. Type hints
    has_type_hints = "->" in content or ": str" in content or ": int" in content
    scores["type_hints"] = 100 if has_type_hints else 30
    
    # 3. Pydantic usage
    uses_pydantic = "BaseModel" in content or "Field(" in content
    scores["pydantic"] = 100 if uses_pydantic else 0
    
    # 4. ColliderAgentDefinition
    has_definition = "ColliderAgentDefinition" in content
    scores["agent_definition"] = 100 if has_definition else 0
    
    # 5. System prompt quality
    has_system_prompt = "system_prompt" in content
    prompt_length = len(content.split("system_prompt")[1].split('"""')[1]) if has_system_prompt and '"""' in content else 0
    scores["system_prompt"] = min(100, prompt_length // 5)
    
    # Overall score
    overall = sum(scores.values()) // len(scores)
    
    return f"""## Evaluation: {p.name}

**Overall Score**: {overall}/100

### Criteria Scores:
| Criterion | Score |
|-----------|-------|
| Documentation | {scores['documentation']}/100 |
| Type Hints | {scores['type_hints']}/100 |
| Pydantic Usage | {scores['pydantic']}/100 |
| Agent Definition | {scores['agent_definition']}/100 |
| System Prompt | {scores['system_prompt']}/100 |

### Recommendations:
{_get_recommendations(scores)}
"""


def _get_recommendations(scores: dict) -> str:
    """Generate recommendations based on scores."""
    recs = []
    if scores["documentation"] < 100:
        recs.append("- Add module-level docstring explaining purpose")
    if scores["type_hints"] < 100:
        recs.append("- Add type hints to all functions")
    if scores["pydantic"] < 100:
        recs.append("- Consider using Pydantic models for data structures")
    if scores["agent_definition"] < 100:
        recs.append("- Include a ColliderAgentDefinition for agent behavior")
    if scores["system_prompt"] < 50:
        recs.append("- Expand system prompt with detailed instructions")
    return "\n".join(recs) if recs else "- Definition is well-structured!"


def improve_definition(path: str, suggestion: Optional[str] = None, **kwargs) -> str:
    """Suggest improvements for a definition.
    
    Args:
        path: Path to definition file
        suggestion: Optional specific improvement to apply
        
    Returns:
        Improvement suggestions or applied changes
    """
    p = Path(path)
    if not p.is_absolute():
        p = DEFINITIONS_DIR / path
    
    if not p.exists():
        return f"Error: Definition not found at {p}"
    
    content = p.read_text(encoding="utf-8")
    
    improvements = []
    
    # Check for common issues
    if "from __future__" not in content:
        improvements.append("Add `from __future__ import annotations` for forward refs")
    
    if "ConfigDict" not in content and "BaseModel" in content:
        improvements.append("Consider using ConfigDict for model configuration")
    
    if "version" not in content.lower() and "ColliderAgentDefinition" in content:
        improvements.append("Add version field to track definition changes")
    
    if not improvements:
        improvements.append("Definition looks good! Consider adding tests.")
    
    return f"""## Improvement Suggestions: {p.name}

{chr(10).join(f'- {i}' for i in improvements)}
"""

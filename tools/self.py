"""Self-modification tools for Gödel.

These tools allow Gödel to read and modify its own definition.
Use with extreme care.
"""
from pathlib import Path
import datetime
import shutil


GODEL_PATH = Path(__file__).parent.parent / "definitions" / "godel.py"
BACKUP_DIR = Path(__file__).parent.parent / ".godel_backups"


def read_self(**kwargs) -> str:
    """Read Gödel's own definition.
    
    This is the recursive self-reference that makes Gödel special.
    
    Returns:
        The current Gödel definition source code
    """
    if not GODEL_PATH.exists():
        return "Error: Gödel definition not found!"
    
    content = GODEL_PATH.read_text(encoding="utf-8")
    return f"""## Gödel's Self-Reference

You are reading your own definition. This is intentionally self-referential.

**Path**: {GODEL_PATH}
**Size**: {len(content)} bytes
**Last Modified**: {datetime.datetime.fromtimestamp(GODEL_PATH.stat().st_mtime)}

### Your Source:
```python
{content}
```

**Note**: You can modify this with `modify_self()`, but document your rationale.
"""


def modify_self(changes: str, rationale: str, **kwargs) -> str:
    """Modify Gödel's own definition.
    
    This is the most powerful and dangerous tool. Use with care.
    
    Args:
        changes: The new content for godel.py
        rationale: Why this modification is necessary
        
    Returns:
        Confirmation of the modification
    """
    if not GODEL_PATH.exists():
        return "Error: Gödel definition not found!"
    
    if not rationale or len(rationale) < 20:
        return "Error: Rationale must be at least 20 characters explaining why."
    
    # Create backup directory
    BACKUP_DIR.mkdir(exist_ok=True)
    
    # Backup current version
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"godel_{timestamp}.py"
    shutil.copy(GODEL_PATH, backup_path)
    
    # Validate the new content (basic syntax check)
    try:
        compile(changes, "godel.py", "exec")
    except SyntaxError as e:
        return f"Error: Invalid Python syntax in proposed changes: {e}"
    
    # Write new content
    GODEL_PATH.write_text(changes, encoding="utf-8")
    
    # Log the modification
    log_path = BACKUP_DIR / "modifications.log"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write(f"Rationale: {rationale}\n")
        f.write(f"Backup: {backup_path}\n")
        f.write(f"{'='*60}\n")
    
    return f"""## Self-Modification Complete

**Backup created**: {backup_path}
**Rationale logged**: {rationale[:50]}...

⚠️ Your definition has been modified. Restart to apply changes.

To revert:
```python
shutil.copy("{backup_path}", "{GODEL_PATH}")
```
"""


def list_self_backups(**kwargs) -> str:
    """List all backups of Gödel's definition."""
    if not BACKUP_DIR.exists():
        return "No backups found. Gödel has never modified itself."
    
    backups = list(BACKUP_DIR.glob("godel_*.py"))
    
    if not backups:
        return "No backups found."
    
    result = ["## Gödel Self-Modification History\n"]
    for b in sorted(backups, reverse=True):
        result.append(f"- `{b.name}` ({b.stat().st_size} bytes)")
    
    return "\n".join(result)

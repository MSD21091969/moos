# Math Maintenance Rules

## Data Evolution

When changing math models, create transformation mappings.

### Schema Changes

```python
# Old: Container without scope_depth
# New: Container with scope_depth

def migrate_container_v1_to_v2(old: dict) -> Container:
    return Container(
        id=old["id"],
        name=old["name"],
        scope_depth=old.get("scope_depth", 1),  # Default R=1
        links=[migrate_link(l) for l in old.get("links", [])]
    )
```

### Migration Utilities

See `models/integration.py`:

- `migrate_legacy_container()`: Convert old dicts to new Container
- `validate_container_graph()`: Verify graph integrity

## Deprecation Policy

1. Mark old pattern as LEGACY in docstring
2. Add deprecation warning
3. Keep for 2 versions
4. Remove in version N+2

```python
def old_method(self):
    """LEGACY: Use new_method() instead."""
    warnings.warn("old_method deprecated", DeprecationWarning)
    return self.new_method()
```

## Version Compatibility

- Math models are versioned with the codebase
- Breaking changes require migration script
- Test suites must pass before and after migration

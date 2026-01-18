# Math Coding Style

## Naming Conventions

| Pattern        | Example                     | Usage                      |
| -------------- | --------------------------- | -------------------------- |
| `_id` suffix   | `container_id`, `owner_id`  | UUID references            |
| `R`            | `scope_depth`               | Recursion depth (0 = root) |
| `_port` suffix | `input_port`, `output_port` | Port references            |

## Type Hints

Always use strict typing for math models.

```python
# Good
def compose(self, other: Link) -> Link | None:

# Bad
def compose(self, other):
```

## Pydantic Validators

Use `model_validator` over `__init__` for validation logic.

```python
@model_validator(mode='after')
def validate_scope(self) -> Self:
    if self.scope_depth > MAX_RECURSION_DEPTH:
        raise ValueError("Scope too deep")
    return self
```

## Immutability

Math models should prefer immutability. Use `Field(frozen=True)` where appropriate.

```python
class Port(BaseModel):
    model_config = ConfigDict(frozen=True)
    name: str
    type_schema: dict
```

## Import Order

1. Standard library
2. Third-party (pydantic, numpy)
3. Local models (`from models.categorical_base import ...`)

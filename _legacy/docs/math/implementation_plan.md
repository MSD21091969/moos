# Functorial Base Models Architecture

Refactor Collider's base models to enforce category-theoretic properties: functorial composition, category laws (associativity, identity), and port promotion as functorial lifting F: R+1 → R.

## User Review Required

> [!IMPORTANT] > **Breaking Changes to Definition Model**
>
> - `Definition` becomes abstract base with `AtomicDefinition` and `CompositeDefinition` subclasses
> - New `compose()` method enforces functorial composition F(g∘f) = F(g)∘F(f)
> - Validators will reject invalid compositions (type mismatches, broken associativity)

> [!WARNING] > **Link Composition Validation**
>
> - Links now enforce composition closure: `link1.compose(link2)` validates source/target compatibility
> - May break existing code that creates disconnected Link chains
> - Identity Links (`id_C: C → C`) become first-class citizens

> [!CAUTION] > **Port Promotion Type Safety**
>
> - Port promotion across scopes (R+1 → R) adds runtime type checking via functor preservation
> - Invalid promotions (type-breaking lifts) will raise `ValidationError`
> - Requires explicit promotion functor `F_promote: Port[R+1] → Port[R]`

---

## Proposed Changes

### Core Models (Category Theory Foundation)

#### [NEW] [categorical_base.py](file:///d:/agent-factory/models/categorical_base.py)

Base classes enforcing category laws. All Collider models inherit from these.

**Key Features:**

- `CategoryObject` mixin for objects in category C_Collider
- `Morphism` base class for Link composition with associativity checks
- `Functor` protocol defining F(id) = id and F(g∘f) = F(g)∘F(f)
- Pydantic validators enforcing category laws

**Implementation:**

```python
class CategoryObject(BaseModel):
    """Mixin for objects in category C_Collider"""

    @classmethod
    def identity(cls, obj_id: UUID) -> Morphism:
        """Return identity morphism id_A: A → A"""

class Morphism(BaseModel):
    """Base for all morphisms (Links) with composition"""
    source: UUID
    target: UUID

    def compose(self, other: Morphism) -> Morphism:
        """Compose morphisms: self ∘ other"""
        # Enforce: self.target == other.source

    @model_validator(mode='after')
    def validate_composition_closure(self) -> Self:
        """Ensure composition stays in category"""
```

---

#### [MODIFY] [definition.py](file:///d:/agent-factory/models/definition.py)

Refactor to abstract base with functorial composition.

**Changes:**

1. Make `Definition` abstract base class
2. Create `AtomicDefinition` and `CompositeDefinition` subclasses
3. Add `compose()` method implementing functor F(g∘f) = F(g)∘F(f)
4. Add quotient functor `Q: Graph_internal → Interface_external`
5. Validators for identity preservation: `F(id) = id`

**New Methods:**

```python
class Definition(BaseModel, ABC):
    """Abstract functor F: C_Abstract → C_Concrete"""

    @abstractmethod
    def compose(self, other: Definition) -> CompositeDefinition:
        """Functorial composition: F(g∘f)"""

    @abstractmethod
    def apply(self, container: Container) -> Container:
        """Apply functor: F(Container)"""

    def is_identity(self) -> bool:
        """Check if this is identity functor"""

class CompositeDefinition(Definition):
    """Quotient functor collapsing internal graph to boundary"""

    def quotient_functor(self) -> tuple[PortSet, PortSet]:
        """Q: G_internal → (inputs_boundary, outputs_boundary)"""
        # Implements boundary derivation from operad algebra
```

---

#### [MODIFY] [link.py](file:///d:/agent-factory/models/link.py)

Enforce morphism composition laws.

**Changes:**

1. Inherit from `Morphism` base class
2. Add `compose()` with associativity validation
3. Add `identity()` class method for `id_C: C → C`
4. Validators ensuring composition closure

**New Methods:**

```python
class Link(Morphism, BaseModel):
    """Links as morphisms in C_Collider"""

    def compose(self, other: Link) -> Optional[Link]:
        """
        Compose Links: (self ∘ other)
        Requires: self.target == other.source
        Returns: Link(source=other.source, target=self.target)
        """

    @classmethod
    def identity(cls, container_id: UUID) -> Link:
        """Identity morphism: id_C"""
        return cls(
            owner_id=container_id,
            eastside_container_id=container_id,
            is_identity=True
        )

    @model_validator(mode='after')
    def validate_associativity(self) -> Self:
        """Ensure (h∘g)∘f = h∘(g∘f)"""
```

---

#### [MODIFY] [container.py](file:///d:/agent-factory/models/container.py)

Enforce Container as category object.

**Changes:**

1. Inherit from `CategoryObject`
2. Add `compose_sequential()` for E→W paths
3. Add `compose_parallel()` for N/S tensor product
4. Depth-aware recursion level (R=0 = UserObject, R≥1 = nested)

**New Methods:**

```python
class Container(CategoryObject, BaseModel):
    """Objects in category C_Collider"""

    recursion_depth: int = 1  # R level

    def compose_sequential(self, *others: Container) -> Link:
        """Sequential composition: self → c1 → c2 → ..."""
        # Returns composite Link via functorial composition

    def compose_parallel(self, *others: Container) -> list[Container]:
        """Parallel tensor product: self ⊗ c1 ⊗ c2 ⊗ ..."""
        # Returns list arranged N/S with no inter-Links
```

---

### Port Promotion (Functorial Lifting)

#### [NEW] [port_promotion.py](file:///d:/agent-factory/models/port_promotion.py)

Implement port promotion as functorial lifting F: R+1 → R.

**Key Concepts:**

- Port at depth R+1 is "lifted" to parent scope R
- Functor F_promote preserves type structure
- Validation ensures F(promoted_port) maintains type safety

**Implementation:**

```python
class Port(BaseModel):
    """Port with scope depth"""
    name: str
    type_schema: dict  # Pydantic schema
    scope_depth: int   # Recursion level R

class PortPromotionFunctor:
    """Functor F: Port[R+1] → Port[R]"""

    def promote(self, port: Port) -> Port:
        """
        Lift port from inner scope (R+1) to outer scope (R)
        Preserves: type_schema (functorial preservation)
        """
        if port.scope_depth == 0:
            raise ValueError("Cannot promote root-level port")

        return Port(
            name=f"promoted_{port.name}",
            type_schema=port.type_schema,  # PRESERVE
            scope_depth=port.scope_depth - 1
        )

    @staticmethod
    def validate_preservation(original: Port, promoted: Port) -> bool:
        """Ensure F preserves type structure"""
        return original.type_schema == promoted.type_schema
```

**Integration with CompositeDefinition:**

```python
class CompositeDefinition(Definition):

    def promote_internal_ports(self) -> tuple[list[Port], list[Port]]:
        """
        Promote R+1 ports to R for composite boundary
        Returns: (promoted_inputs, promoted_outputs)
        """
        functor = PortPromotionFunctor()

        promoted_inputs = []
        promoted_outputs = []

        for defn in self.internal_definitions:
            for port in defn.unsatisfied_inputs():
                promoted = functor.promote(port)
                if functor.validate_preservation(port, promoted):
                    promoted_inputs.append(promoted)
                else:
                    raise ValidationError("Port promotion broke type safety")
```

---

### Graph Logic Methods

#### [NEW] [graph_operations.py](file:///d:/agent-factory/models/graph_operations.py)

Categorical graph operations using functorial composition.

**Key Operations:**

- `compose_path(links: list[Link]) -> Link` - Reduce path to single morphism
- `tensor_product(containers: list[Container]) -> list[Container]` - Parallel ⊗
- `quotient_graph(containers, links) -> CompositeDefinition` - Functor Q

**Implementation:**

```python
def compose_path(links: list[Link]) -> Link:
    """
    Functorial path composition: h∘g∘f
    Validates associativity at each step
    """
    from functools import reduce

    def compose_pair(link1: Link, link2: Link) -> Link:
        result = link1.compose(link2)
        if result is None:
            raise ValueError(f"Links not composable: {link1.id} ∘ {link2.id}")
        return result

    return reduce(compose_pair, links)

def quotient_graph(
    containers: list[Container],
    links: list[Link]
) -> CompositeDefinition:
    """
    Quotient functor Q: G_internal → Interface
    Collapses graph to boundary I/O
    """
    # Compute unsatisfied inputs (boundary)
    all_inputs = [port for c in containers for port in c.inputs]
    all_outputs = [port for c in containers for port in c.outputs]

    wired_inputs = {link.target_port for link in links}
    consumed_outputs = {link.source_port for link in links}

    boundary_inputs = [p for p in all_inputs if p.id not in wired_inputs]
    boundary_outputs = [p for p in all_outputs if p.id not in consumed_outputs]

    return CompositeDefinition(
        type="composite",
        input_ports=boundary_inputs,
        output_ports=boundary_outputs,
        internal_graph=(containers, links)
    )
```

---

### Category Law Enforcement

#### [NEW] [validators.py](file:///d:/agent-factory/models/validators.py)

Pydantic validators for category laws.

**Validators:**

1. **Associativity**: `(h∘g)∘f = h∘(g∘f)`
2. **Identity**: `f∘id = f = id∘f`
3. **Composition Closure**: `f∘g` stays in category
4. **Functor Preservation**: `F(g∘f) = F(g)∘F(f)`

**Implementation:**

```python
from pydantic import field_validator, model_validator

def validate_associativity(
    link1: Link,
    link2: Link,
    link3: Link
) -> bool:
    """Verify (h∘g)∘f = h∘(g∘f)"""
    # Left association
    left = (link1.compose(link2)).compose(link3)

    # Right association
    right = link1.compose(link2.compose(link3))

    return left == right  # Must be equal

def validate_identity_law(link: Link) -> bool:
    """Verify f∘id = f = id∘f"""
    id_source = Link.identity(link.source)
    id_target = Link.identity(link.target)

    # f∘id_source = f
    left_identity = link.compose(id_source) == link

    # id_target∘f = f
    right_identity = id_target.compose(link) == link

    return left_identity and right_identity

class CompositeDefinition(Definition):

    @model_validator(mode='after')
    def validate_functor_laws(self) -> Self:
        """Ensure F(g∘f) = F(g)∘F(f)"""
        # For each pair of internal definitions
        for i, defn1 in enumerate(self.internal_definitions):
            for defn2 in self.internal_definitions[i+1:]:
                # Check if composable
                if self._are_connected(defn1, defn2):
                    # Compose internally then apply functor
                    internal_composite = defn1.compose(defn2)
                    F_composite = self.apply_quotient(internal_composite)

                    # Apply functor then compose
                    F_defn1 = self.apply_quotient(defn1)
                    F_defn2 = self.apply_quotient(defn2)
                    composite_F = F_defn1.compose(F_defn2)

                    # Must be equal
                    assert F_composite == composite_F, "Functor law violated"

        return self
```

---

### UserObject as Initial Object

#### [MODIFY] [user_object.py](file:///d:/agent-factory/models/user_object.py)

Formalize UserObject as initial object in category (R=0).

**Key Property:** In category theory, an **initial object** has exactly one morphism to every other object.

For Collider:

- UserObject (R=0) is the root
- Unique morphism to any Container at R=1: ownership/creation

**Changes:**

```python
class UserObject(CategoryObject, BaseModel):
    """Initial object in C_Collider (R=0)"""

    recursion_depth: int = 0  # Always 0

    @classmethod
    def is_initial_object(cls) -> bool:
        """UserObject is initial in category"""
        return True

    def create_morphism_to(self, container: Container) -> Link:
        """
        Unique morphism from initial object to any Container
        Represents ownership/creation
        """
        if container.recursion_depth != 1:
            raise ValueError("UserObject can only create R=1 Containers")

        return Link(
            owner_id=self.id,
            eastside_container_id=container.id,
            description="User owns this container",
            is_initial_morphism=True
        )
```

---

## Verification Plan

### Automated Tests

```bash
# Category law property tests
pytest tests/test_category_laws.py -v

# Test associativity for random Link triples
# Test identity laws for all Link types
# Test functor preservation F(g∘f) = F(g)∘F(f)
```

**Test Cases:**

1. **Associativity**: Generate random Link chains, verify `(h∘g)∘f = h∘(g∘f)`
2. **Identity**: For each Link, verify `f∘id = f = id∘f`
3. **Functor Composition**: Build Composite, verify `F(g∘f) = F(g)∘F(f)`
4. **Port Promotion**: Promote ports across scopes, verify type preservation
5. **Quotient Functor**: Build internal graphs, verify boundary derivation matches operad algebra

### Manual Verification

- Build nested Container hierarchy (R=0 → R=1 → R=2 → R=3)
- Verify UserObject as initial object (unique morphism to each R=1)
- Compose Definitions functorially, inspect composite boundaries
- Promote ports from R=2 → R=1, validate types preserved
- Test edge cases: empty graphs, single-node graphs, cyclic attempts

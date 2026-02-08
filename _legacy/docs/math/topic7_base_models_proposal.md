# Topic 7: Scope Isolation Base Models Proposal

**From**: Scope Isolation & Port Promotion Theory  
**Date**: 2026-01-15

---

## Executive Summary

Propose Pydantic base models implementing **categorical port promotion** with **scope depth R enforcement** to prevent spaghetti wiring and enable type-safe boundary crossing in recursive Container graphs.

**Core Principle**: Ports can only be promoted (R+1 → R) via explicit functor application, wires only connect at matching scope depths.

---

## 1. Port Class - Typed Interface with Scope

```python
from pydantic import BaseModel, field_validator, computed_field
from typing import Literal, Type, Optional, Any
from uuid import UUID, uuid4
from enum import Enum

class PortDirection(str, Enum):
    """Port direction for boundary crossing"""
    INPUT = "input"
    OUTPUT = "output"

class Port(BaseModel):
    """Type-safe port with categorical scope enforcement"""

    id: UUID = Field(default_factory=uuid4)
    name: str
    direction: PortDirection
    scope_depth: int = Field(ge=0, description="R value: 0=UserObject root, R+1=nested")
    port_type: Type[Any]  # Pydantic type for validation
    description: Optional[str] = None

    # Metadata for graph rendering
    visual_hint: Optional[str] = None  # "north", "east", "west", "south"

    class Config:
        arbitrary_types_allowed = True  # For Type[Any]

    @field_validator('scope_depth')
    @classmethod
    def validate_depth(cls, v):
        """Ensure non-negative depth"""
        if v < 0:
            raise ValueError("scope_depth must be >= 0 (UserObject is R=0)")
        return v

    def promote(self) -> "Port":
        """
        Categorical lifting: F(Port@R+1) → Port@R

        Functor properties:
        - Preserves type: port_type unchanged
        - Preserves direction: input stays input
        - Decrements depth: R+1 → R

        Raises:
            ValueError: If already at root scope (R=0)
        """
        if self.scope_depth == 0:
            raise ValueError("Cannot promote root-level port (R=0)")

        return Port(
            id=uuid4(),  # New identity at parent scope
            name=f"promoted_{self.name}",
            direction=self.direction,
            scope_depth=self.scope_depth - 1,
            port_type=self.port_type,
            description=f"Promoted from R={self.scope_depth}: {self.description or self.name}",
            visual_hint=self.visual_hint
        )

    def demote(self, new_name: Optional[str] = None) -> "Port":
        """
        Inverse operation: Push port into child scope
        Used during graph injection/morphing
        """
        return Port(
            id=uuid4(),
            name=new_name or f"nested_{self.name}",
            direction=self.direction,
            scope_depth=self.scope_depth + 1,
            port_type=self.port_type,
            description=f"Demoted to R={self.scope_depth + 1}",
            visual_hint=self.visual_hint
        )

    @computed_field
    @property
    def fully_qualified_name(self) -> str:
        """Scope-aware name for debugging"""
        return f"{self.name}@R{self.scope_depth}"

    def is_compatible(self, other: "Port") -> bool:
        """
        Check if two ports can be wired together

        Requirements:
        - Same scope depth
        - Opposite directions (output → input)
        - Compatible types (Pydantic type checking)
        """
        if self.scope_depth != other.scope_depth:
            return False
        if self.direction == other.direction:
            return False
        # Type compatibility check (simplified)
        return True  # TODO: Deep type checking


class PortSignature(BaseModel):
    """Collection of ports forming a Definition's interface"""

    inputs: list[Port] = Field(default_factory=list)
    outputs: list[Port] = Field(default_factory=list)

    @computed_field
    @property
    def scope_depth(self) -> int:
        """All ports must have same scope depth"""
        depths = [p.scope_depth for p in self.inputs + self.outputs]
        if not depths:
            return 0
        if len(set(depths)) > 1:
            raise ValueError("Mixed scope depths in PortSignature")
        return depths[0]

    def promote_all(self) -> "PortSignature":
        """Promote entire signature to parent scope (quotient functor)"""
        return PortSignature(
            inputs=[p.promote() for p in self.inputs],
            outputs=[p.promote() for p in self.outputs]
        )
```

---

## 2. Wire Class - Scope-Enforced Connections

```python
from pydantic import field_validator, model_validator

class Wire(BaseModel):
    """Type-safe, scope-enforced connection between ports"""

    id: UUID = Field(default_factory=uuid4)
    source_port: Port  # Must be OUTPUT
    target_port: Port  # Must be INPUT

    # Metadata
    label: Optional[str] = None

    @model_validator(mode='after')
    def validate_wire(self):
        """Enforce wiring rules"""

        # Rule 1: Scope depth must match (categorical law)
        if self.source_port.scope_depth != self.target_port.scope_depth:
            raise ValueError(
                f"Scope violation: cannot wire across depths "
                f"R={self.source_port.scope_depth} → R={self.target_port.scope_depth}. "
                f"Use port promotion first."
            )

        # Rule 2: Direction must be output → input
        if self.source_port.direction != PortDirection.OUTPUT:
            raise ValueError("source_port must be OUTPUT")
        if self.target_port.direction != PortDirection.INPUT:
            raise ValueError("target_port must be INPUT")

        # Rule 3: Type compatibility
        if not self.source_port.is_compatible(self.target_port):
            raise ValueError(
                f"Type mismatch: {self.source_port.port_type} → {self.target_port.port_type}"
            )

        return self

    @computed_field
    @property
    def scope_depth(self) -> int:
        """Wire inherits scope from its ports"""
        return self.source_port.scope_depth

    def compose(self, other: "Wire") -> Optional["Wire"]:
        """
        Categorical composition: if this.target == other.source, compose

        Returns composite wire: self.source → other.target
        """
        if self.target_port.id != other.source_port.id:
            return None

        return Wire(
            source_port=self.source_port,
            target_port=other.target_port,
            label=f"({self.label or 'w1'})∘({other.label or 'w2'})"
        )
```

---

## 3. ScopeEnforcer Mixin - Automatic Depth Management

```python
class ScopeEnforcer(BaseModel):
    """Mixin for models that enforce scope depth constraints"""

    scope_depth: int = Field(ge=0)
    _depth_cache: Optional[int] = None  # Private cache

    def validate_child_depth(self, child_depth: int):
        """Ensure child is exactly one level deeper"""
        if child_depth != self.scope_depth + 1:
            raise ValueError(
                f"Child must be at R={self.scope_depth + 1}, got R={child_depth}"
            )

    def validate_sibling_depth(self, sibling_depth: int):
        """Ensure sibling is at same level"""
        if sibling_depth != self.scope_depth:
            raise ValueError(
                f"Sibling must be at R={self.scope_depth}, got R={sibling_depth}"
            )

    def increment_depth(self, delta: int = 1) -> int:
        """Return new depth for nested element"""
        return self.scope_depth + delta

    def decrement_depth(self, delta: int = 1) -> int:
        """Return new depth for promoted element"""
        new_depth = self.scope_depth - delta
        if new_depth < 0:
            raise ValueError("Cannot decrement below R=0")
        return new_depth
```

---

## 4. Container Base Class - Recursive with Scope

```python
from typing import Optional, List, ForwardRef

ContainerRef = ForwardRef('Container')

class Container(ScopeEnforcer):
    """
    Recursive container with scope-aware ports and links

    Scope invariants:
    - All ports must have scope_depth == self.scope_depth
    - All internal links connect ports at self.scope_depth
    - Child containers have scope_depth == self.scope_depth + 1
    """

    id: UUID = Field(default_factory=uuid4)
    name: str
    description: Optional[str] = None

    # Port interface
    ports: PortSignature = Field(default_factory=PortSignature)

    # Internal wiring (at this scope level)
    internal_wires: List[Wire] = Field(default_factory=list)

    # Recursive structure
    children: List[ContainerRef] = Field(default_factory=list)
    parent_id: Optional[UUID] = None

    # Definition reference (optional - can be empty container)
    definition_id: Optional[UUID] = None

    # Visual layout hints
    visual_x: Optional[int] = None
    visual_y: Optional[int] = None

    @model_validator(mode='after')
    def validate_scope_consistency(self):
        """Ensure all elements respect scope depth"""

        # Check ports
        if self.ports.scope_depth != self.scope_depth:
            raise ValueError("Port signature scope mismatch")

        # Check wires
        for wire in self.internal_wires:
            if wire.scope_depth != self.scope_depth:
                raise ValueError(f"Wire {wire.id} scope mismatch")

        # Check children
        for child in self.children:
            self.validate_child_depth(child.scope_depth)

        return self

    def add_child_container(self, child: ContainerRef):
        """Add nested container at R+1"""
        child.scope_depth = self.increment_depth()
        child.parent_id = self.id
        self.children.append(child)

    def promote_child_ports(self, child_id: UUID) -> List[Port]:
        """
        Promote child's unsatisfied ports to this level

        Returns list of promoted ports that become part of this Container's interface
        """
        child = next((c for c in self.children if c.id == child_id), None)
        if not child:
            raise ValueError(f"Child {child_id} not found")

        # Find unsatisfied ports (not wired internally in child)
        wired_port_ids = {
            wire.target_port.id for wire in child.internal_wires
        }

        unsatisfied = [
            port for port in child.ports.inputs
            if port.id not in wired_port_ids
        ]

        # Promote each
        promoted = [port.promote() for port in unsatisfied]

        # Add to this Container's interface
        self.ports.inputs.extend(promoted)

        return promoted

    def derive_composite_boundary(self) -> PortSignature:
        """
        Operad-style boundary derivation: (All Inputs) - (Internal Wires)

        Combines:
        - Own declared ports
        - Promoted unsatisfied child ports
        """
        all_inputs = set(self.ports.inputs)
        all_outputs = set(self.ports.outputs)

        # Add promoted child ports
        for child in self.children:
            child_boundary = child.derive_composite_boundary()
            # Promote child boundary to this level
            promoted = child_boundary.promote_all()
            all_inputs.update(promoted.inputs)
            all_outputs.update(promoted.outputs)

        # Subtract internally satisfied
        wired_targets = {w.target_port.id for w in self.internal_wires}
        wired_sources = {w.source_port.id for w in self.internal_wires}

        boundary_inputs = [p for p in all_inputs if p.id not in wired_targets]
        boundary_outputs = [p for p in all_outputs if p.id not in wired_sources]

        return PortSignature(
            inputs=boundary_inputs,
            outputs=boundary_outputs
        )

# Resolve forward reference
Container.model_rebuild()
```

---

## 5. Graph Morphing Operations

```python
class GraphMorpher:
    """Stateless operations for graph manipulation preserving scope invariants"""

    @staticmethod
    def inject_subgraph(
        target: Container,
        subgraph_root: Container
    ) -> Container:
        """
        Morph: Insert subgraph inside target node

        Steps:
        1. Increment all subgraph depths by 1
        2. Promote subgraph boundary to match target's old interface
        3. Replace target's definition with subgraph
        """
        # Deep copy subgraph
        import copy
        nested_subgraph = copy.deepcopy(subgraph_root)

        # Increment all depths
        def increment_recursive(container: Container):
            container.scope_depth += 1
            for child in container.children:
                increment_recursive(child)

        increment_recursive(nested_subgraph)

        # Promote boundary to match target interface
        promoted_boundary = nested_subgraph.derive_composite_boundary()

        # Verify compatibility
        if promoted_boundary.scope_depth != target.scope_depth:
            raise ValueError("Boundary scope mismatch after injection")

        # Replace
        target.children = [nested_subgraph]
        target.ports = promoted_boundary

        return target

    @staticmethod
    def split_container(
        container: Container,
        strategy: Literal["by_io", "by_semantic", "by_definition"]
    ) -> List[Container]:
        """
        Morph: Decompose container into multiple at same depth

        Returns list of new containers, redistribute ports/wires
        """
        if strategy == "by_io":
            # Split by input/output groups
            # Implementation depends on port clustering logic
            pass

        # TODO: Implement other strategies
        raise NotImplementedError(f"Strategy {strategy} not yet implemented")

    @staticmethod
    def fuse_containers(containers: List[Container]) -> Container:
        """
        Morph: Merge multiple containers into one (inverse of split)

        Requirements:
        - All at same scope depth
        - No cyclic dependencies
        """
        if not containers:
            raise ValueError("Cannot fuse empty list")

        # Validate same depth
        depths = {c.scope_depth for c in containers}
        if len(depths) > 1:
            raise ValueError(f"Cannot fuse across depths: {depths}")

        depth = depths.pop()

        # Merge
        fused = Container(
            name=f"fused_{'_'.join(c.name for c in containers[:3])}",
            scope_depth=depth
        )

        # Union all ports
        for c in containers:
            fused.ports.inputs.extend(c.ports.inputs)
            fused.ports.outputs.extend(c.ports.outputs)
            fused.internal_wires.extend(c.internal_wires)
            fused.children.extend(c.children)

        # Deduplicate
        fused.ports.inputs = list({p.id: p for p in fused.ports.inputs}.values())
        fused.ports.outputs = list({p.id: p for p in fused.ports.outputs}.values())

        return fused
```

---

## 6. Integration Points

### With pydantic-graph (beta)

```python
from pydantic_graph import Graph, Node

class ContainerGraphAdapter:
    """Convert between Container model and pydantic-graph"""

    @staticmethod
    def to_graph_node(container: Container) -> Node:
        """Convert Container to pydantic-graph Node"""
        return Node(
            id=str(container.id),
            data=container.model_dump(),
            metadata={"scope_depth": container.scope_depth}
        )

    @staticmethod
    def build_graph(root: Container) -> Graph:
        """
        Build pydantic-graph from Container tree

        Respects scope boundaries - only creates edges between same-depth nodes
        """
        graph = Graph()

        def add_recursive(container: Container):
            graph.add_node(ContainerGraphAdapter.to_graph_node(container))

            # Add edges from wires (same scope only)
            for wire in container.internal_wires:
                graph.add_edge(
                    str(wire.source_port.id),
                    str(wire.target_port.id),
                    metadata={"scope_depth": wire.scope_depth}
                )

            # Recurse children
            for child in container.children:
                add_recursive(child)

        add_recursive(root)
        return graph
```

### With Graph Grammar Templates

```python
class GraphGrammar(BaseModel):
    """Template for preset container structures"""

    name: str
    description: str
    pattern: str  # Pattern to match (e.g., "MapReduce", "Pipeline")

    def instantiate(self, params: dict) -> Container:
        """Create Container structure from template"""
        if self.pattern == "MapReduce":
            return self._create_mapreduce(params)
        # ... other patterns
        raise NotImplementedError(f"Pattern {self.pattern} not implemented")

    def _create_mapreduce(self, params: dict) -> Container:
        """Create MapReduce container structure"""
        root = Container(
            name=params.get("name", "MapReduce"),
            scope_depth=params.get("depth", 0)
        )

        # Create Map child
        map_container = Container(
            name="Map",
            scope_depth=root.increment_depth()
        )

        # Create Reduce child
        reduce_container = Container(
            name="Reduce",
            scope_depth=root.increment_depth()
        )

        root.add_child_container(map_container)
        root.add_child_container(reduce_container)

        # Wire them
        # ... port creation and wiring logic

        return root
```

---

## 7. Answers to Fundamental Questions

### LinkedContainerDefinition Mechanism

**Decision**: Hybrid approach

- **Graph logic** knows topology (Links, port connections)
- **Containers** own state (Definition instances, execution context)
- **Dependencies** tracked in both: Graph edges + Container.children

**Rationale**: Separation of concerns enables independent optimization

### Scope Depth Representation

**Decision**: Explicit field with cached validation

```python
scope_depth: int = Field(ge=0)  # Explicit, fast lookup
```

**Validation**: Pydantic model_validator ensures consistency with parent/child relationships

**Alternative considered**: Implicit (computed from parent chain) rejected due to O(R) cost

### Container vs Graph Separation

**Containers**: Discrete entities with:

- Internal complexity (nested children)
- Executable definitions
- Port interfaces

**Graph**: Dataflow structure with:

- Edges between ports
- Topology for execution order
- Scope-stratified adjacency

**Integration**: `ContainerGraphAdapter` bridges the two

### Preset Structures

**Support via**: `GraphGrammar` pattern matching

- Template library for common structures
- Instantiation with parameters
- Type-safe validation post-creation

**Balance**: Presets ensure predictability, create_model() enables dynamic adaptation

---

## 8. Next Steps

1. **Implement in** `shared/models/base.py`
2. **Add tests** for scope validation, promotion, morphing
3. **Integrate with** pydantic-graph (beta)
4. **Create template** library in `parts/graph/templates/`
5. **Build graph builder** using these primitives

**Awaiting**: Proposals from Topics 1-6 for synthesis into unified architecture

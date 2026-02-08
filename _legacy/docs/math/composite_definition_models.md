# Scope-Aware Composite Definition - Pydantic Models

## Architecture Overview

Integrates **Boundary Derivation** (Topic 4) with **Scope Isolation** (Topic 7) for recursive container composition.

**Key Insight**: Promoted ports from R+1 appear as emerged inputs/outputs at R level.

---

## 1. Core Base Models

### ScopedPort

Tracks port identity across recursion levels.

```python
from pydantic import BaseModel, Field
from typing import Literal, Optional
from enum import Enum

class PortDirection(str, Enum):
    INPUT = "input"
    OUTPUT = "output"

class ScopedPort(BaseModel):
    """Port with scope/recursion level tracking"""

    name: str = Field(..., description="Port identifier")
    direction: PortDirection
    recursion_level: int = Field(
        ...,
        ge=0,
        description="Scope depth: R=0 (UserObject), R=1+ (Container)"
    )
    data_type: str = Field(default="Any", description="Port data type")

    # Port promotion tracking
    promoted_from: Optional['ScopedPort'] = Field(
        None,
        description="If promoted, the R+1 port this was lifted from"
    )

    # Scope crossing metadata
    scope_boundary_crossed: bool = Field(
        default=False,
        description="True if port was promoted from nested scope"
    )

    @property
    def scoped_name(self) -> str:
        """Fully qualified name with scope: 'portname@R2'"""
        return f"{self.name}@R{self.recursion_level}"

    def promote_to_level(self, target_level: int) -> 'ScopedPort':
        """
        Functorial lifting: Port@R+1 → Port@R
        Category theory: Promotion as functor F: C_{R+1} → C_R
        """
        if target_level >= self.recursion_level:
            raise ValueError(f"Can only promote to shallower level: {target_level} < {self.recursion_level}")

        return ScopedPort(
            name=f"promoted_{self.name}",
            direction=self.direction,
            recursion_level=target_level,
            data_type=self.data_type,
            promoted_from=self,
            scope_boundary_crossed=True
        )

    class Config:
        frozen = True  # Immutable for graph consistency
```

### ScopedWire

Links between ports across scopes.

```python
class WireScope(str, Enum):
    INTERNAL = "internal"      # Same R level
    CROSS_SCOPE = "cross_scope"  # R → R+1 or R+1 → R

class ScopedWire(BaseModel):
    """Wire connecting two ScopedPorts, potentially crossing scope boundaries"""

    source: ScopedPort = Field(..., description="Output port")
    target: ScopedPort = Field(..., description="Input port")

    @property
    def wire_scope(self) -> WireScope:
        """Determine if wire is internal or crosses scope"""
        if self.source.recursion_level == self.target.recursion_level:
            return WireScope.INTERNAL
        return WireScope.CROSS_SCOPE

    @property
    def scope_delta(self) -> int:
        """Delta between source and target levels"""
        return abs(self.source.recursion_level - self.target.recursion_level)

    def validate_connection(self) -> bool:
        """Validate wire respects scope rules"""
        # Source must be OUTPUT, target must be INPUT
        if self.source.direction != PortDirection.OUTPUT:
            return False
        if self.target.direction != PortDirection.INPUT:
            return False

        # Cross-scope wires limited to adjacent levels
        if self.wire_scope == WireScope.CROSS_SCOPE:
            if self.scope_delta != 1:
                return False

        # Type compatibility (simplified)
        if self.source.data_type != self.target.data_type:
            return False

        return True
```

---

## 2. CompositeDefinition Model

Dynamically derived Definition from container topology with scope awareness.

```python
from typing import Set, Dict, List, Tuple
from pydantic import computed_field, create_model

class BoundaryDerivationMethod(str, Enum):
    OPERAD = "operad"          # Functorial composition
    UNSATISFIED = "unsatisfied"  # Set-based algorithm
    DATAFLOW = "dataflow"      # Compiler-style analysis

class CompositeDefinition(BaseModel):
    """
    Emerged Definition from recursive container composition
    Integrates:
    - Operad boundary derivation (Topic 4)
    - Scope isolation & port promotion (Topic 7)
    - Data flow analysis
    """

    name: str = Field(..., description="Composite Definition name")
    recursion_level: int = Field(..., ge=0, description="Scope level of this composite")

    # Internal topology
    internal_containers: List['ContainerNode'] = Field(
        default_factory=list,
        description="Nested containers at R+1, R+2, ... levels"
    )
    internal_wires: List[ScopedWire] = Field(
        default_factory=list,
        description="Wiring between internal containers"
    )

    # Derived boundary (computed)
    _boundary_inputs: Optional[Set[ScopedPort]] = None
    _boundary_outputs: Optional[Set[ScopedPort]] = None
    _promoted_ports: Optional[Set[ScopedPort]] = None

    # Validation: all three methods should agree
    _derivation_validated: bool = False

    @computed_field
    def boundary_inputs(self) -> Set[ScopedPort]:
        """Emerged input ports at this recursion level"""
        if self._boundary_inputs is None:
            self._derive_boundary()
        return self._boundary_inputs

    @computed_field
    def boundary_outputs(self) -> Set[ScopedPort]:
        """Emerged output ports at this recursion level"""
        if self._boundary_outputs is None:
            self._derive_boundary()
        return self._boundary_outputs

    @computed_field
    def promoted_ports(self) -> Set[ScopedPort]:
        """Ports promoted from nested scopes (R+1 → R)"""
        if self._promoted_ports is None:
            self._derive_boundary()
        return self._promoted_ports

    def _derive_boundary(self) -> None:
        """
        Tri-method boundary derivation with scope awareness
        """
        # Method 1: Operad-style (functorial)
        boundary_operad = self._derive_operad()

        # Method 2: Unsatisfied Needs with scope
        boundary_unsatisfied = self._derive_unsatisfied_with_scope()

        # Method 3: Data flow across scopes
        boundary_dataflow = self._derive_dataflow_scoped()

        # Validate all methods agree
        assert boundary_operad == boundary_unsatisfied == boundary_dataflow, \
            "Boundary derivation methods disagree!"

        self._boundary_inputs = boundary_operad['inputs']
        self._boundary_outputs = boundary_operad['outputs']
        self._promoted_ports = boundary_operad['promoted']
        self._derivation_validated = True

    def _derive_operad(self) -> Dict[str, Set[ScopedPort]]:
        """
        Operad-style composition with functorial port promotion
        F: Container@R+1 → Interface@R
        """
        # Recursively derive boundaries for all nested containers first
        nested_boundaries = {}
        for container in self.internal_containers:
            if container.recursion_level > self.recursion_level:
                # Derive R+1 boundary, then promote to R
                nested_def = container.definition
                if isinstance(nested_def, CompositeDefinition):
                    nested_boundaries[container.id] = {
                        'inputs': nested_def.boundary_inputs,
                        'outputs': nested_def.boundary_outputs
                    }

        # Apply functorial composition
        inputs = set()
        outputs = set()
        promoted = set()

        for container in self.internal_containers:
            # Add container's ports at its level
            for port in container.input_ports:
                if not self._is_satisfied_internally(port):
                    if port.recursion_level == self.recursion_level:
                        inputs.add(port)
                    elif port.recursion_level > self.recursion_level:
                        # Promote from R+1 to R
                        promoted_port = port.promote_to_level(self.recursion_level)
                        inputs.add(promoted_port)
                        promoted.add(promoted_port)

            for port in container.output_ports:
                if not self._is_consumed_internally(port):
                    outputs.add(port)

        return {'inputs': inputs, 'outputs': outputs, 'promoted': promoted}

    def _derive_unsatisfied_with_scope(self) -> Dict[str, Set[ScopedPort]]:
        """
        Modified Unsatisfied Needs Algorithm:
        Boundary@R = (All Inputs@R ∪ All Inputs@R+1)
                     - (Internal Wires@R)
                     - (Promoted Ports handled)
        """
        # Collect all inputs at all levels
        all_inputs = set()
        all_outputs = set()

        for container in self.internal_containers:
            all_inputs.update(container.input_ports)
            all_outputs.update(container.output_ports)

        # Internal satisfaction via wires
        satisfied_inputs = set()
        consumed_outputs = set()

        for wire in self.internal_wires:
            # Wire satisfies target input
            satisfied_inputs.add(wire.target)
            consumed_outputs.add(wire.source)

        # Unsatisfied inputs - partition by scope
        unsatisfied_at_R = set()
        unsatisfied_at_R_plus = set()

        for inp in all_inputs:
            if inp not in satisfied_inputs:
                if inp.recursion_level == self.recursion_level:
                    unsatisfied_at_R.add(inp)
                elif inp.recursion_level > self.recursion_level:
                    unsatisfied_at_R_plus.add(inp)

        # Promote R+1 inputs to R
        promoted = set()
        for inp in unsatisfied_at_R_plus:
            promoted_port = inp.promote_to_level(self.recursion_level)
            promoted.add(promoted_port)

        # Boundary inputs = native@R + promoted@R
        boundary_inputs = unsatisfied_at_R | promoted

        # Exposed outputs (not consumed internally)
        boundary_outputs = all_outputs - consumed_outputs

        return {'inputs': boundary_inputs, 'outputs': boundary_outputs, 'promoted': promoted}

    def _derive_dataflow_scoped(self) -> Dict[str, Set[ScopedPort]]:
        """
        Data Flow Analysis with Scope Context
        - Reaching Definitions: Track scope level of each definition
        - Live Variable Analysis: Propagate across scope boundaries
        """
        # Build CFG from container graph
        cfg = self._build_scoped_cfg()

        # Forward: Reaching Definitions
        reaching = self._reaching_definitions_scoped(cfg)

        # Backward: Live Variable Analysis
        live = self._live_variable_analysis_scoped(cfg)

        # Boundary detection
        boundary_inputs = set()
        boundary_outputs = set()
        promoted = set()

        # Entry blocks: unsatisfied inputs at R
        for block in cfg.entry_blocks:
            for inp in block.IN:
                if not self._has_internal_provider(inp, reaching):
                    if inp.recursion_level == self.recursion_level:
                        boundary_inputs.add(inp)
                    elif inp.recursion_level > self.recursion_level:
                        promoted_port = inp.promote_to_level(self.recursion_level)
                        boundary_inputs.add(promoted_port)
                        promoted.add(promoted_port)

        # Exit blocks: live outputs
        for block in cfg.exit_blocks:
            boundary_outputs.update(block.OUT)

        return {'inputs': boundary_inputs, 'outputs': boundary_outputs, 'promoted': promoted}

    def _is_satisfied_internally(self, port: ScopedPort) -> bool:
        """Check if input port is satisfied by internal wire"""
        for wire in self.internal_wires:
            if wire.target == port:
                return True
        return False

    def _is_consumed_internally(self, port: ScopedPort) -> bool:
        """Check if output port is consumed by internal wire"""
        for wire in self.internal_wires:
            if wire.source == port:
                return True
        return False

    def _build_scoped_cfg(self) -> 'ScopedCFG':
        """Build Control Flow Graph with scope annotations"""
        # Implementation: Convert container graph to CFG
        pass

    def _reaching_definitions_scoped(self, cfg: 'ScopedCFG') -> Dict:
        """
        Reaching Definitions with scope tracking
        IN[Block@R] can include OUT[Block@R+1] if promoted
        """
        pass

    def _live_variable_analysis_scoped(self, cfg: 'ScopedCFG') -> Dict:
        """Live Variable Analysis across scope boundaries"""
        pass

    def _has_internal_provider(self, port: ScopedPort, reaching: Dict) -> bool:
        """Check if port has internal definition that reaches it"""
        pass

    def to_pydantic_model(self) -> type[BaseModel]:
        """
        Dynamic model generation using create_model()
        Converts CompositeDefinition → concrete Definition class
        """
        # Build field spec from boundary ports
        fields = {}

        for inp in self.boundary_inputs:
            fields[inp.name] = (inp.data_type, Field(..., description=f"Input at {inp.scoped_name}"))

        for out in self.boundary_outputs:
            fields[out.name] = (out.data_type, Field(..., description=f"Output at {out.scoped_name}"))

        # Dynamically create Definition model
        DynamicDefinition = create_model(
            f"{self.name}Definition",
            **fields
        )

        return DynamicDefinition
```

---

## 3. Data Flow Across Scopes

### ScopedCFG (Control Flow Graph)

```python
class ScopedBlock(BaseModel):
    """Basic block in CFG with scope context"""

    id: str
    container_id: str
    recursion_level: int

    # Data flow sets (scope-aware)
    IN: Set[ScopedPort] = Field(default_factory=set)
    OUT: Set[ScopedPort] = Field(default_factory=set)
    GEN: Set[ScopedPort] = Field(default_factory=set)
    KILL: Set[ScopedPort] = Field(default_factory=set)

    # For live variable analysis
    USE: Set[ScopedPort] = Field(default_factory=set)
    DEF: Set[ScopedPort] = Field(default_factory=set)

    predecessors: List['ScopedBlock'] = Field(default_factory=list)
    successors: List['ScopedBlock'] = Field(default_factory=list)

    # Scope boundary annotations
    is_scope_entry: bool = False  # Entry to nested scope (R → R+1)
    is_scope_exit: bool = False   # Exit from nested scope (R+1 → R)

class ScopedCFG(BaseModel):
    """Control Flow Graph with scope isolation"""

    blocks: List[ScopedBlock]
    entry_blocks: List[ScopedBlock]
    exit_blocks: List[ScopedBlock]

    def reaching_definitions_worklist(self) -> None:
        """
        Iterative worklist algorithm with scope tracking
        Modified: OUT[B@R] can propagate to IN[B'@R-1] if promoted
        """
        worklist = list(self.blocks)

        # Initialize
        for block in self.blocks:
            block.GEN = set(block.container.output_ports)
            block.KILL = set(block.container.input_ports)

        # Fixed-point iteration
        while worklist:
            block = worklist.pop(0)

            # IN = union of predecessor OUTs
            new_IN = set()
            for pred in block.predecessors:
                for port in pred.OUT:
                    # Handle scope promotion
                    if port.recursion_level > block.recursion_level:
                        new_IN.add(port.promote_to_level(block.recursion_level))
                    elif port.recursion_level == block.recursion_level:
                        new_IN.add(port)

            block.IN = new_IN

            # OUT = GEN ∪ (IN - KILL)
            new_OUT = block.GEN | (block.IN - block.KILL)

            if new_OUT != block.OUT:
                block.OUT = new_OUT
                worklist.extend(block.successors)

    def live_variable_worklist(self) -> None:
        """
        Live Variable Analysis (backward) with scope awareness
        """
        worklist = list(self.blocks)

        # Initialize USE and DEF
        for block in self.blocks:
            block.USE = set(block.container.input_ports)
            block.DEF = set(block.container.output_ports)
            block.OUT = set()

        # Backward iteration
        while worklist:
            block = worklist.pop(0)

            # OUT = union of successor INs
            new_OUT = set()
            for succ in block.successors:
                new_OUT |= succ.IN

            block.OUT = new_OUT

            # IN = USE ∪ (OUT - DEF)
            new_IN = block.USE | (block.OUT - block.DEF)

            if new_IN != block.IN:
                block.IN = new_IN
                worklist.extend(block.predecessors)
```

---

## 4. Container Node with Scope

```python
class ContainerNode(BaseModel):
    """Container instance in composite graph with scope tracking"""

    id: str
    definition: Union['Definition', 'CompositeDefinition']
    recursion_level: int = Field(..., ge=0)

    # Ports (cached from definition)
    input_ports: Set[ScopedPort] = Field(default_factory=set)
    output_ports: Set[ScopedPort] = Field(default_factory=set)

    # Links to other containers
    outbound_wires: List[ScopedWire] = Field(default_factory=list)
    inbound_wires: List[ScopedWire] = Field(default_factory=list)

    def __init__(self, **data):
        super().__init__(**data)
        self._populate_ports()

    def _populate_ports(self) -> None:
        """Populate scoped ports from definition"""
        if isinstance(self.definition, CompositeDefinition):
            self.input_ports = self.definition.boundary_inputs
            self.output_ports = self.definition.boundary_outputs
        else:
            # Regular Definition - convert to ScopedPorts
            for inp_name in self.definition.inputs:
                self.input_ports.add(ScopedPort(
                    name=inp_name,
                    direction=PortDirection.INPUT,
                    recursion_level=self.recursion_level
                ))
            for out_name in self.definition.outputs:
                self.output_ports.add(ScopedPort(
                    name=out_name,
                    direction=PortDirection.OUTPUT,
                    recursion_level=self.recursion_level
                ))
```

---

## 5. Integration Example

```python
from typing import List

def build_composite_from_containers(
    containers: List[ContainerNode],
    wires: List[ScopedWire],
    recursion_level: int
) -> CompositeDefinition:
    """
    Build CompositeDefinition from container topology
    Automatically derives boundary with scope awareness
    """
    composite = CompositeDefinition(
        name=f"Composite@R{recursion_level}",
        recursion_level=recursion_level,
        internal_containers=containers,
        internal_wires=wires
    )

    # Boundary derivation happens automatically via computed fields
    # All three methods (operad, unsatisfied, dataflow) execute and validate

    print(f"Derived Boundary Inputs: {composite.boundary_inputs}")
    print(f"Derived Boundary Outputs: {composite.boundary_outputs}")
    print(f"Promoted Ports: {composite.promoted_ports}")

    # Generate dynamic Pydantic model
    DynamicDef = composite.to_pydantic_model()

    return composite

# Example usage
if __name__ == "__main__":
    # R=1 containers
    container_a = ContainerNode(
        id="A",
        definition=some_definition_a,
        recursion_level=1
    )

    container_b = ContainerNode(
        id="B",
        definition=some_definition_b,
        recursion_level=1
    )

    # Wire A.output → B.input
    wire = ScopedWire(
        source=ScopedPort(name="data", direction=PortDirection.OUTPUT, recursion_level=1),
        target=ScopedPort(name="input", direction=PortDirection.INPUT, recursion_level=1)
    )

    # Build R=0 composite
    composite_def = build_composite_from_containers(
        containers=[container_a, container_b],
        wires=[wire],
        recursion_level=0
    )

    # Use in Container
    composite_container = ContainerNode(
        id="Composite",
        definition=composite_def,
        recursion_level=0
    )
```

---

## 6. pydantic-graph Integration

```python
from pydantic_graph import BaseNode, Graph

class CompositeGraphNode(BaseNode):
    """Node for pydantic-graph DAG execution with scope isolation"""

    container: ContainerNode

    def run(self, **inputs):
        """Execute container with scope-aware I/O"""
        # Map inputs to scoped ports
        scoped_inputs = {}
        for port in self.container.input_ports:
            if port.scope_boundary_crossed:
                # Handle promoted port
                original_port = port.promoted_from
                scoped_inputs[original_port.name] = inputs.get(port.name)
            else:
                scoped_inputs[port.name] = inputs.get(port.name)

        # Execute definition
        result = self.container.definition.execute(**scoped_inputs)

        # Map outputs
        return result

def build_execution_graph(composite: CompositeDefinition) -> Graph:
    """Convert CompositeDefinition to pydantic-graph for execution"""
    nodes = []

    for container in composite.internal_containers:
        node = CompositeGraphNode(container=container)
        nodes.append(node)

    # Build edges from wires
    graph = Graph()
    for node in nodes:
        graph.add_node(node)

    for wire in composite.internal_wires:
        source_node = graph.get_node(wire.source.container_id)
        target_node = graph.get_node(wire.target.container_id)
        graph.add_edge(source_node, target_node, port_map={
            wire.source.name: wire.target.name
        })

    return graph
```

---

## Summary

**Models Delivered**:

1. ✅ `ScopedPort` - Port with recursion level & promotion tracking
2. ✅ `ScopedWire` - Cross-scope wiring
3. ✅ `CompositeDefinition` - Recursive boundary derivation with tri-method validation
4. ✅ `ScopedCFG` - Data flow analysis across scopes
5. ✅ `ContainerNode` - Scope-aware container instances

**Key Features**:

- **Port Promotion**: `port.promote_to_level(R)` as functorial lifting
- **Tri-Method Validation**: Operad + Unsatisfied + DataFlow all agree
- **Scope-Aware Wiring**: `ScopedWire` validates scope crossing rules
- **Dynamic Models**: `create_model()` generates concrete Definitions
- **pydantic-graph Ready**: Direct integration for DAG execution

**Next**: Implement in `shared/models/` with tests validating boundary derivation correctness.

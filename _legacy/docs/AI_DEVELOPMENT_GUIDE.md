# Agent Factory: AI Development Guide

> [!IMPORTANT]
> **This is a Category-Theoretic Compiler.**
> Code in this repository MUST adhere to strict mathematical properties.
> We do NOT just write "classes"; we implement **Functors** and **Morphisms**.

## 1. The Core Mental Model

The Factory produces **Containers** (agents, tools, data).
These Containers are nodes in a Graph.
We use Category Theory to ensure these graphs are composable and verifiable.

- **Object**: A `Container` (or `UserObject`). Has Identity (UUID).
- **Morphism**: A `Link` or `Wire`. Maps Output $A$ to Input $B$.
- **Functor**: A `Definition`. It maps an Abstract Schema to a Concrete Container.
  - $F: C_{Abstract} \to C_{Concrete}$

## 2. Core Library: `agent_factory.models_v2`

You MUST use these base classes. Do not invent your own.

| Class                 | Type                 | Purpose                                                       |
| :-------------------- | :------------------- | :------------------------------------------------------------ |
| `Definition`          | Functor              | Abstract Interface. Defines `input_ports` and `output_ports`. |
| `AtomicDefinition`    | Functor              | A single executable unit (e.g., a PydanticAI Agent).          |
| `CompositeDefinition` | **Quotient Functor** | A graph of definitions collapsed into a single interface.     |
| `Link`                | Morphism             | Structural connection between Containers (Parent-Child).      |
| `Wire`                | Morphism             | Data flow connection between Ports.                           |
| `ScopedPort`          | Type Info            | A Port with Scope Depth (R) awareness.                        |

## 3. The Rules of Engagement

### Rule 1: The Tri-Method Boundary

When creating a `CompositeDefinition`, you NEVER manually set the input/output ports.
You MUST calculate them using `_derive_boundary()`.
This method uses three algorithms that must agree:

1.  **Operad**: All Inputs - Wired Inputs.
2.  **Set Theoretic**: Operad + Promoted Ports.
3.  **Data Flow**: Reaching Definitions.

### Rule 2: Recursiveness is Physical

We do not just "reference" other agents. We "embed" them.

- Depth $R$: The current container.
- Depth $R+1$: The children containers.
- **Port Promotion**: To expose a child's port to the parent's boundary, you must use `PortPromotionFunctor` to lift it ($R+1 \to R$).

### Rule 3: Semantics are First-Class

Every Container has a Vector Embedding.
$V_{Container} = \Sigma V(Child_i) + V(Topology)$

- Use `agent_factory.models_v2.semantic` mixins.
- Ensure embeddings are updated when topology changes.

## 4. Workflows

### Creating a New Component

1.  Define the **AtomicDefinitions** (the leaf nodes).
2.  Define the **CompositeDefinition** (the graph).
    - Add Attributes (internal definitions).
    - Add Links (structure).
    - Add Wires (data flow).
3.  Call `derive_boundary()`.
4.  Export to `agent_factory/parts/catalog.py`.

### Generating a Tool

1.  Load `Definition` from Catalog.
2.  Call `to_pydantic_model()` (Dynamic Generator).
3.  Pass the resulting class to the Agent.

# The Four Morphisms

## The Only Operations

There are exactly four morphisms. Everything the system does decomposes into
sequences of these. There is no fifth operation.

| Morphism | Signature                    | Category-Theoretic Role |
| -------- | ---------------------------- | ----------------------- |
| ADD      | ∅ → Container                | Object creation         |
| LINK     | Container × Container → Wire | Morphism creation       |
| MUTATE   | Container → Container        | Endomorphism            |
| UNLINK   | Wire → ∅                     | Morphism deletion       |

## Natural Transformations

Each morphism is a **natural transformation** — it commutes with every functor
applied to the graph. When you ADD a container:

- The FileSystem functor sees a new entry in the manifest
- The UI_Lens functor renders a new node in the graph view
- The Protocol functor exposes a new API endpoint
- The Embedding functor generates a new vector

No functor needs to know HOW the ADD happened. The naturality condition guarantees
that the output of each functor is consistent with the graph operation.

## Composition Rules

Operations compose left-to-right in execution order:

```
Create a wired model:
  ADD(model_container) ; LINK(root, model_container) ; MUTATE(model_container, config)

Remove a tool:
  UNLINK(runner, tool) ; UNLINK(tool, targets...) ; (container remains, unwired)

Migrate ownership:
  LINK(new_owner, container, OWNS) ; UNLINK(old_owner, container, OWNS)
```

The semicolon is sequential composition. Operations within a sequence are
**atomic per morphism** — each ADD/LINK/MUTATE/UNLINK is one transaction.
A sequence of morphisms may span multiple transactions.

## Atomicity

Each morphism is **atomic and independent**:

- No internal wiring (a LINK does not trigger a cascade of other LINKs)
- No split edges (one wire connects exactly one source to one target)
- No implicit side effects (ADD creates a container, nothing else)

This is the "atomic morphisms without dependencies" principle. The kernel executes
one morphism at a time. Composition of morphisms happens at the pipeline level,
not inside the morphism executor.

If a complex operation requires multiple steps (e.g., create a workspace with
children), the pipeline decomposes it into individual ADD/LINK/MUTATE calls. Each
call succeeds or fails independently. The pipeline handles rollback by issuing
compensating morphisms (UNLINK to reverse a LINK, etc.).

## Morphism Log

Every morphism is recorded in `morphism_log`:

```sql
INSERT INTO morphism_log (morphism_type, actor_urn, target_urn, previous_state, new_state)
VALUES ('MUTATE', 'urn:moos:identity:user:alice', 'urn:moos:data:doc:123',
        '{"title": "old"}', '{"title": "new"}');
```

The log is the **ground truth**. The containers table is a cache. The wires table
is a cache. Everything can be rebuilt from the morphism log.

## Mapping to Superset Ontology

The superset ontology's 8 named morphisms map to compositions of the four:

| Ontology Morphism  | Decomposition                            |
| ------------------ | ---------------------------------------- |
| OWNS               | LINK(owner, target, port: "owns")        |
| CAN_HYDRATE        | LINK(source, target, port: "hydrate")    |
| PRE_FLIGHT_CONFIG  | MUTATE(container, config_payload)        |
| SYNC_ACTIVE_STATE  | MUTATE(container, runtime_state)         |
| ADD_NODE_CONTAINER | ADD(container) ; LINK(parent, container) |
| LINK_NODES         | LINK(source, target)                     |
| UPDATE_NODE_KERNEL | MUTATE(container, kernel_config)         |
| DELETE_EDGE        | UNLINK(wire)                             |
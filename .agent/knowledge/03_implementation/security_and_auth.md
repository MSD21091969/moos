# Security and Authentication

## Two Access Domains

The system has two separate access control surfaces. They are NOT the same graph.
They share the same database but operate under different rules.

### Domain 1: Node Access (Identity Ownership)

**Who can see/own this container?**

Node access is identity-based. An authenticated user has a URN. That URN either
has an OWNS wire to a container or it doesn't. Ownership is binary and transitive
(OWNS chains propagate automatically).

```
Alice (urn:moos:identity:user:alice)
  ├── OWNS → Workspace A
  │     ├── OWNS → Tool X        ← Alice transitively owns this
  │     └── OWNS → Document Y    ← Alice transitively owns this
  └── OWNS → Workspace B
```

Node access answers: "does a path of OWNS wires exist from this user to this
container?" This is a reachability query on the ownership subgraph.

The user IS a key. The user has access to what the key unlocks (containers with
OWNS wires from the user's URN). The user is otherwise no different from any other
container — just metadata on the node it owns, consisting of the edges it uses to
pass state.

### Domain 2: Edge Access (System Policy)

**What rules govern this morphism / this wire?**

Edge access is system-controlled. ANY rule is possible:

- **Global**: all users can traverse this wire (public read)
- **Local**: only the owning user can traverse this wire (private)
- **Temporal**: this wire is only active between timestamp A and B
- **Environmental**: this wire only exists in production / staging / dev
- **Role-based**: this wire requires a specific `type_id` on the actor container
- **Conditional**: this wire requires `state_payload.status == 'active'` on target
- **Rate-limited**: this wire allows N traversals per time window

Edge rules live in `wire_config` JSONB on the wires table. The kernel evaluates
these rules at traversal time. Different wires can have completely different rule
types — there is no single permission model.

### Why Two Domains?

| Aspect       | Node Access            | Edge Access                |
| ------------ | ---------------------- | -------------------------- |
| Question     | "Who owns this?"       | "What rules govern this?"  |
| Granularity  | Container level        | Wire level                 |
| Transitivity | Always (OWNS chains)   | Declared per-wire          |
| Controller   | Identity graph         | Policy graph               |
| Typical rule | Existence of OWNS wire | JSONB match on wire_config |
| Default      | No access (no wire)    | No traversal (no wire)     |

Both are discoverable. Both carry metadata properties that can be indexed and
matched against semantic content. But they answer different questions and use
different resolution mechanisms.

## Least Privilege via Wire Absence

The default state is: no wire = no access. A new container has no wires (except
the OWNS wire from its creator). Access is granted by creating LINK morphisms.
Access is revoked by UNLINK morphisms.

There are no "deny" rules. Access control is purely additive: you have access
because a wire exists, not because a deny rule is absent. This makes the
permission model monotonic and auditable — to understand why someone has access,
trace the wire graph. To revoke access, find and remove the wire.

## Authentication Flow

```
1. External auth (OAuth / API key) → verified identity
2. Map identity to URN: urn:moos:identity:user:{subject}
3. All subsequent operations carry actor_urn = that URN
4. Every morphism request is: "actor X wants to MUTATE container Y"
5. Kernel checks: does a wire from X's ownership subgraph reach Y?
6. If yes → execute. If no → 403.
```

Authentication is external (JWT verification, API key lookup). Authorization is
internal (wire existence check). The kernel does not manage passwords or tokens.
It only answers: "given this URN, is there a path to that container?"

## OWNS Transitivity

```sql
-- Recursive CTE to check transitive ownership
WITH RECURSIVE ownership AS (
    SELECT target_urn FROM wires
    WHERE source_urn = 'urn:moos:identity:user:alice'
      AND source_port = 'owns'
    UNION ALL
    SELECT w.target_urn FROM wires w
    JOIN ownership o ON w.source_urn = o.target_urn
    WHERE w.source_port = 'owns'
)
SELECT target_urn FROM ownership;
```

This returns everything Alice transitively owns. It walks the OWNS subgraph
depth-first until no more OWNS wires are found.

## CAN_HYDRATE Transitivity

```sql
-- Only follow transitive CAN_HYDRATE wires
WITH RECURSIVE hydration AS (
    SELECT target_urn, wire_config FROM wires
    WHERE source_urn = 'urn:moos:infra:workspace:ffs0'
      AND source_port = 'hydrate'
    UNION ALL
    SELECT w.target_urn, w.wire_config FROM wires w
    JOIN hydration h ON w.source_urn = h.target_urn
    WHERE w.source_port = 'hydrate'
      AND (h.wire_config->>'transitive')::boolean = true
)
SELECT target_urn FROM hydration;
```

CAN_HYDRATE only chains when the parent wire has `transitive: true`. The manifest
is the declaration surface for this flag — each workspace chooses what propagates.
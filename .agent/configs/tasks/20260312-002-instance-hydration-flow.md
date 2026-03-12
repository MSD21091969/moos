# Task: Instance Hydration Flow (Tier 2 Bootstrap)

**Status:** pending
**Priority:** p0
**Delegated:** 2026-03-12
**Depends on:** 001-kb-aware-boot

## Objective

Wire `POST /hydration/materialize` to consume `instances/*.json` files and
generate Programs (ordered envelope sequences) per the install specification.
Add `--hydrate` boot flag that auto-applies Tier 2 Programs after seed.

## SOT References

- **Install spec (Programs 5–11):** `.agent/knowledge_base/doctrine/install.md`
- **Hydration lifecycle:** `.agent/knowledge_base/doctrine/hydration.md`
- **Ontology (valid type_ids, morphisms, source/target constraints):** `.agent/knowledge_base/superset/ontology.json`
- **Instance files:** `.agent/knowledge_base/instances/*.json`
- **Current hydration code:** `platform/kernel/internal/hydration/materialize.go`

## Key Constraints (from ontology)

All morphism decompositions, source/target constraints, and port names are
defined in `ontology.json`. Do not hardcode — read from the registry.
Wire directions follow ontology exactly (e.g. CAN_ROUTE sources from
`protocol.ProtocolAdapter`, not from tools).

## Acceptance Criteria

- Each instance file produces a valid Program per install.md
- `POST /hydration/materialize {"source": "instances/providers.json"}` works
- `--hydrate` auto-applies all instance files on boot (idempotent via SeedIfAbsent)
- `GET /state` after hydration shows nodes for all populated kinds
- All morphisms respect ontology source/target constraints
- `go test ./...` green

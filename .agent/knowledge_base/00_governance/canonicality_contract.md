# Canonicality Contract

## Purpose

Define the role of each knowledge-base layer and prevent category drift.

## Role model

- `00_governance/` — canonical process and authority rules
- `01_foundations/` — canonical ontology and invariants
- `02_architecture/` — canonical system realization patterns
- `03_semantics/` — canonical interpretation and separation discipline
- `04_value_layer/` — contingent graph instances and environment facts
- `05_reference/` — non-canonical but promotable source interpretations
- `superset/` — canonical structured registry
- `_legacy/` — archived provenance, not live canon

## Canonicality rules

1. One concept has one canonical home.
2. Doctrine is written in Markdown.
3. Structured typed references belong in JSON.
4. CSV must not introduce semantics absent from Markdown or JSON.
5. Raw source files are never canonical by themselves.
6. Architecture may consume foundations but may not redefine them.
7. Value-layer files may instantiate canonical concepts but may not redefine them.
8. Direct citations to legacy source paths are allowed only in `00_governance/`, `05_reference/`, and `_legacy/`.
9. Canonical doctrine and structured registries must reference either canonical KB locations or governance provenance records, not legacy file paths.

## Identity rule

- The abstract actor or user belongs to canon and the registry.
- Concrete bindings such as `userId` belong to `04_value_layer/identities.json`.
- A contingent identity binding is a graph instance, not a redefinition of ontology.

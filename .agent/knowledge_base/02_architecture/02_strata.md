# Strata

## Purpose

Describe the layered realization model of authored, validated, materialized, evaluated, and projected structure.

## Canonicality

Canonical for strata realization.

## Seed scope

- S0 through S4
- authored vs materialized distinction
- promotion thresholds
- lifecycle alignment with hydration

## Canonical strata

| Stratum | Name         | Meaning                                                             |
| ------- | ------------ | ------------------------------------------------------------------- |
| S0      | Authored     | Declared syntax, manifests, and references before validation        |
| S1      | Validated    | Schema-checked authored material that is admissible for realization |
| S2      | Materialized | Graph-ready programs and structures derived from validated inputs   |
| S3      | Evaluated    | Contingent state after execution, hydration, or replay              |
| S4      | Projected    | Views, lenses, embeddings, and metrics derived from evaluated state |

## Discipline

- Higher strata may depend on lower strata through explicit inclusion.
- Lower strata must not depend on higher strata for meaning.
- S4 is never canonical truth; it is a projection over evaluated state.
- Hydration stages align one-for-one with the canonical strata in this file.

## Migration source

Strata-source provenance is recorded in `00_governance/migration_map.md`.
This file should express promoted strata doctrine without direct legacy file references.

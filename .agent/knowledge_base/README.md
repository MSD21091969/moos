# Knowledge Base Index

This directory is the canonical knowledge surface for the repository.

## Purpose

- hold the controlled vNext canon
- separate ontology, architecture, semantics, runtime facts, and reference material
- preserve provenance without letting legacy inputs redefine active knowledge

## Layer Summary

| Layer              | Role                                                                                                      | Canonicality                                               |
| ------------------ | --------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| `00_governance/`   | Canonicality rules, read order, promotion, configuration and secret boundaries, migration mapping         | Canonical for process and authority                        |
| `01_foundations/`  | Axioms, primitives, category language, and invariant rules                                                | Canonical for foundations                                  |
| `02_architecture/` | Kernel realization, strata, functors, governance architecture                                             | Canonical for architecture                                 |
| `03_semantics/`    | Hydration, normalization, syntax/semantics, interpretation discipline                                     | Canonical for semantics                                    |
| `04_value_layer/`  | Runtime-contingent graph instances, providers, preferences, identities, workstation and environment facts | Canonical for runtime and deployment facts, not ontology   |
| `05_reference/`    | Paper digests, transcript digests, raw sources, and supporting reference material                         | Non-canonical; promotable only through governance          |
| `superset/`        | Structured registry and derivative exports                                                                | `ontology.json` is canonical; `ontology.csv` is derivative |
| `_legacy/`         | Pre-migration provenance snapshots and archived source structures                                         | Archive only; non-canonical                                |

## Registry Files

- `superset/ontology.json` is the canonical machine-readable registry.
- `superset/ontology.csv` is a derivative export.
- `superset/value_layer_schema.json` and `superset/promotion_log.json` are registry-support artifacts and therefore live in `superset/`, not `04_value_layer/`.

## Rules

- Treat this directory as the single indexed entry point for the knowledge base.
- Do not add per-layer `README.md` files.
- Promote material from reference or legacy layers only through governance rules in `00_governance/`.

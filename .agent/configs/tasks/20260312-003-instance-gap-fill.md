# Task: Fill Instance Gaps (21/21 Kind Coverage)

**Status:** done
**Priority:** p1
**Delegated:** 2026-03-12

## Objective

Create instance entries for the 6 ontology kinds that currently have zero
instances. After this, every `type_id` in `ontology.json` has ≥1 entry
across `instances/`.

## Current Gaps

| type_id            | Kind  | Needs                              |
| ------------------ | ----- | ---------------------------------- |
| `collider_admin`   | OBJ02 | Add to identities.json             |
| `app_template`     | OBJ04 | New file or add to existing        |
| `node_container`   | OBJ05 | Exemplar container                 |
| `compute_resource` | OBJ10 | GPU + cloud exemplars              |
| `infra_service`    | OBJ12 | Postgres + filesystem exemplars    |
| `memory_store`     | OBJ13 | Vector store + conversation buffer |

## SOT References

- **Ontology (allowed_strata, source/target_connections per kind):** `.agent/knowledge_base/superset/ontology.json`
- **Existing instances (format/conventions):** `.agent/knowledge_base/instances/*.json`
- **Concept map:** `.agent/knowledge_base/design/concept-instance-map.md`

## Constraints

- Follow existing instance file format exactly (URN patterns, payload structure)
- Respect `allowed_strata` from ontology for each kind
- Include wire specifications where ontology defines `target_connections`
  (e.g. `compute_resource` is target of OWNS and CAN_SCHEDULE)
- Do not invent morphism types — only use MOR01–MOR16 from ontology

## Acceptance Criteria

- All 21 type_ids have ≥1 instance across `instances/`
- All new entries are consistent with ontology constraints
- Task 002 hydration can consume all new files

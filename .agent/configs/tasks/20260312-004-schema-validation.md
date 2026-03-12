# Task: JSON Schema for Instance Validation

**Status:** pending
**Priority:** p1
**Delegated:** 2026-03-12
**Depends on:** 003-instance-gap-fill

## Objective

Create `superset/schema.json` (JSON Schema draft-07) that validates all
`instances/*.json` files. Add a test that loads every instance file and
validates against the schema.

## What the Schema Should Enforce

- Required fields: `urn`, `type_id`, `stratum`
- `type_id` enum: the 21 values from `ontology.json` objects[].type_id
- `stratum` enum: S0, S1, S2, S3, S4
- Cross-check: stratum within `allowed_strata` for that type_id (from ontology)

## SOT References

- **Ontology (canonical type_ids + allowed_strata):** `.agent/knowledge_base/superset/ontology.json`
- **Instance files to validate:** `.agent/knowledge_base/instances/*.json`

## Acceptance Criteria

- All existing instance files pass validation
- Schema rejects invalid type_id, missing URN, wrong stratum
- Test in kernel test suite validates every instance file

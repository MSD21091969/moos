# Container-Graph Logic JSON Schema v0

## Scope

- Canonical FFS0 draft for container-graph logic expressed as JSON.
- Authoring and validation reference only.
- No runtime edits in this document; runtime behavior remains in service code and contracts.

## Purpose

- Define a stable, minimal JSON shape for container/graph logic across FFS0/FFS1 tooling.
- Keep authoring format editable in filesystem/IDE while remaining directly compilable into runtime registry structures.
- Provide one canonical reference for seeder validation and alias compatibility decisions.

## Design Principles

- JSON should be both editable and runnable through the existing compile path.
- Keep semantic layering minimal and explicit.
- Favor canonical keys with narrow alias tolerance at ingestion boundaries.
- Separate schema shape from execution/protocol implementation.

## Precedence Order

When conflicting guidance is encountered, resolve in this order:

1. `rules`
2. `tools` / `workflows`
3. `instructions`
4. `knowledge`

## Schema v0 (fields only)

Top-level object keys:

- `contract_version`
- `ids`
- `graph`
- `rbac`
- `layers`
- `runtime_policy`
- `provenance`

Field intent (shape-level summary):

- `contract_version`: schema contract tag for compatibility checks.
- `ids`: canonical identifiers (`app_id`, node/container ids, optional aliases).
- `graph`: node/edge metadata needed for compile and link generation.
- `rbac`: role/permission declarations used by read/edit/execute/register checks.
- `layers`: layered payload buckets (`instructions`, `rules`, `skills`, `tools`, `workflows`).
- `runtime_policy`: compile/runtime control flags and constraints (non-protocol).
- `provenance`: source and trace metadata for authoring, seeding, and compiled outputs.

## Layer Semantics

- `instructions`: compact intent framing and operational context.
- `rules`: hard constraints and guardrails; highest precedence.
- `skills`: optional reusable capability bundles.
- `tools`: atomic executable contracts and schema-defined invocations.
- `workflows`: composed executable contracts that orchestrate tools and steps.

## Container -> Graph Compile Flow

1. Filesystem/IDE JSON authoring (canonical v0 shape).
2. Seeder validates shape, aliases, and minimal invariants.
3. Persist validated payload as DB `NodeContainer` canonical runtime record.
4. Registry compile materializes runtime-facing tool/workflow references.
5. Frontend link generation resolves graph relations and container references.

## RBAC Hooks

RBAC integrates at these decision points:

- `read`: view/access container and compiled graph artifacts.
- `edit`: mutate authoring JSON and container metadata.
- `execute`: run tools/workflows derived from compiled layers.
- `register`: publish/update registries for executable surfaces.

## Compatibility / Aliases

- `app_id` is canonical.
- `application_id` is tolerated as ingest alias.
- Normalization should occur during validation/compile ingestion, not at runtime call sites.

## Non-goals

- No execution code in this spec.
- No protocol transport changes in v0.
- No expansion into full runtime implementation details.

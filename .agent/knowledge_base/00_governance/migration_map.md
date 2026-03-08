# Migration Map

## Purpose

Track the migration from `.agent/knowledge/` into `.agent/knowledge_base/`.

## Source to destination crosswalk

| Source                                                           | Destination                                                                                                                                   | Status  | Notes                                                                   |
| ---------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- | ------- | ----------------------------------------------------------------------- |
| `.agent/knowledge/01_foundations/foundations.md`                 | `01_foundations/01_axioms.md`, `01_foundations/02_primitives.md`, `01_foundations/03_category_language.md`, `01_foundations/04_invariants.md` | planned | Primary doctrinal source                                                |
| `.agent/knowledge/02_architecture/architecture.md`               | `02_architecture/*`                                                                                                                           | planned | Primary architecture source                                             |
| `.agent/knowledge/05_moos_design/kernel_specification.md`        | `02_architecture/01_kernel.md`, `03_semantics/*`                                                                                              | planned | Candidate source                                                        |
| `.agent/knowledge/05_moos_design/hydration_lifecycle.md`         | `03_semantics/01_hydration_pipeline.md`                                                                                                       | planned | Candidate source                                                        |
| `.agent/knowledge/05_moos_design/strata_and_authoring.md`        | `02_architecture/02_strata.md`, `03_semantics/*`                                                                                              | planned | Candidate source                                                        |
| `.agent/knowledge/05_moos_design/normalization_and_migration.md` | `03_semantics/04_normalization_rules.md`                                                                                                      | planned | Candidate source                                                        |
| `.agent/knowledge/datasets/providers.json`                       | `04_value_layer/providers.json`                                                                                                               | planned | Contingent instances                                                    |
| `.agent/knowledge/datasets/benchmarks.json`                      | `04_value_layer/benchmarks.json`                                                                                                              | planned | Contingent instances                                                    |
| `.agent/knowledge/datasets/preferences.json`                     | `04_value_layer/preferences.json`                                                                                                             | planned | Contingent instances                                                    |
| `.agent/knowledge/datasets/workstation.json`                     | `04_value_layer/workstation.json`                                                                                                             | planned | Contingent instances                                                    |
| `.agent/knowledge/papers/*`                                      | `05_reference/papers/*`                                                                                                                       | planned | Digest/reference layer                                                  |
| `.agent/knowledge/transcripts/*`                                 | `05_reference/transcripts/*`                                                                                                                  | planned | Digest + raw reference layer                                            |
| `.agent/knowledge/superset/ontology_v3.json`                     | `superset/ontology.json`                                                                                                                      | planned | Auxiliary structured registry remains in place outside the canonical KB |
| `.agent/knowledge/superset/ontology_v3.csv`                      | `superset/ontology.csv`                                                                                                                       | planned | Auxiliary derivative export remains in place outside the canonical KB   |

## Migration priority

1. Seed foundations and architecture canon.
2. Seed semantics rules.
3. Move contingent value data.
4. Populate registry.
5. Populate reference digests and raw sources.
6. Archive legacy tree under `_legacy/`.

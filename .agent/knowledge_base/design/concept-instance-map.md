# Concept-to-Instance Map

Maps each formal concept to concrete instances, showing how superset types relate to instance files, industry sources, URN patterns, skills, and the Programs that hydrate them.

---

## Object Types → Instances

| Concept            | Superset Type           | Instance File                     | Example URN                                       | Industry Source          | Hydration Program        | Related Skills                                       |
| ------------------ | ----------------------- | --------------------------------- | ------------------------------------------------- | ------------------------ | ------------------------ | ---------------------------------------------------- |
| User               | OBJ01 User              | instances/identities.json         | `urn:moos:user:demo-seeder`                       | —                        | Program 4 (Tier 1)       | —                                                    |
| Admin              | OBJ02 ColliderAdmin     | instances/identities.json         | (future)                                          | —                        | (future)                 | —                                                    |
| Root Admin         | OBJ03 SuperAdmin        | instances/identities.json         | (future)                                          | —                        | (future)                 | —                                                    |
| App Template       | OBJ04 AppTemplate       | (none yet)                        | (future)                                          | industry/frameworks.json | (future)                 | react-expert, nextjs-developer, vue-expert           |
| Container          | OBJ05 NodeContainer     | (implicit — root, kernel)         | `urn:moos:root`                                   | —                        | Programs 1, 3 (Tier 1)   | —                                                    |
| AI Model           | OBJ06 AgnosticModel     | instances/providers.json (nested) | `urn:moos:model:gemini:gemini-3.1-pro`            | industry/providers.json  | Program 5 (Tier 2)       | —                                                    |
| Tool               | OBJ07 SystemTool        | instances/tools.json              | `urn:moos:tool:category-master`                   | industry/tools.json      | Program 8 (Tier 2)       | (each skill IS a tool)                               |
| UI Surface         | OBJ08 UI_Lens           | instances/surfaces.json           | `urn:moos:surface:explorer-ui`                    | —                        | Program 6 (Tier 2)       | —                                                    |
| Runtime Surface    | OBJ09 RuntimeSurface    | instances/surfaces.json           | `urn:moos:surface:kernel-http`                    | industry/protocols.json  | Programs 2, 6 (Tier 1+2) | rest-api-design-patterns, golang-backend-development |
| Compute Resource   | OBJ10 ComputeResource   | (none yet)                        | (future)                                          | industry/compute.json    | (future)                 | kubernetes-specialist, docker-compose-orchestration  |
| Protocol Adapter   | OBJ11 ProtocolAdapter   | instances/surfaces.json           | `urn:moos:surface:mcp-sse`                        | industry/protocols.json  | Program 6 (Tier 2)       | mcp-integration-expert, websocket-engineer           |
| Infra Service      | OBJ12 InfraService      | (none yet)                        | (future)                                          | industry/compute.json    | (future)                 | terraform-engineer, cloud-architect                  |
| Memory Store       | OBJ13 MemoryStore       | (none yet)                        | (future)                                          | —                        | (future)                 | rag-architect                                        |
| Platform Config    | OBJ14 PlatformConfig    | instances/distribution.json       | `urn:moos:config:platform`                        | —                        | Program 11 (Tier 2)      | —                                                    |
| Workstation Config | OBJ15 WorkstationConfig | instances/workstation.json        | `urn:moos:config:workstation`                     | —                        | Program 11 (Tier 2)      | —                                                    |
| Preference         | OBJ16 Preference        | instances/preferences.json        | `urn:moos:pref:model.default_provider`            | —                        | Program 7 (Tier 2)       | —                                                    |
| Provider           | OBJ17 Provider          | instances/providers.json          | `urn:moos:provider:anthropic`                     | industry/providers.json  | Program 5 (Tier 2)       | —                                                    |
| Benchmark Suite    | OBJ18 BenchmarkSuite    | instances/benchmarks.json         | `urn:moos:benchmark:suite:morphism-extraction-v1` | industry/benchmarks.json | Program 10 (Tier 2)      | —                                                    |
| Benchmark Task     | OBJ19 BenchmarkTask     | instances/benchmarks.json         | `urn:moos:benchmark:task:single-add`              | industry/benchmarks.json | Program 10 (Tier 2)      | —                                                    |
| Benchmark Score    | OBJ20 BenchmarkScore    | instances/benchmarks.json         | `urn:moos:benchmark:score:example-001`            | industry/benchmarks.json | Program 10 (Tier 2)      | —                                                    |
| Agent Spec         | OBJ21 AgentSpec         | instances/agents.json             | `urn:moos:agent:copilot-interim`                  | —                        | Program 9 (Tier 2)       | —                                                    |

---

## Operational Binding Layer: .agent/configs/

The `.agent/configs/` surface is the **human-edited operational binding layer** — YAML files that provide runtime settings, auth contracts, and identity governance. It is NOT classified by the ontology (not an OBJ), but serves as the authoritative source for contingent operational data that instances/ entries reference.

| Config File             | Binds To Instance(s)                           | Authority Over                                       |
| ----------------------- | ---------------------------------------------- | ---------------------------------------------------- |
| api_providers.yaml      | instances/providers.json (config_source field) | Provider registry, auth contracts, model catalogs    |
| workspace_defaults.yaml | instances/agents.json (config_source field)    | Agent defaults (model, temperature), feature flags   |
| users.yaml              | instances/identities.json                      | Identity archetypes, auth profiles, access morphisms |

**Relationship**: configs/ → (classifying functor) → instances/ → (hydration) → kernel graph state.

---

## Morphisms → Instance Wires

| Morphism           | ID    | Example Wire                                                       | Programs Using It   |
| ------------------ | ----- | ------------------------------------------------------------------ | ------------------- |
| OWNS               | MOR01 | `root → provider:anthropic` (owns/child)                           | All Programs (1-11) |
| CAN_HYDRATE        | MOR02 | `user:demo-seeder → root` (can_hydrate/hydrate)                    | Programs 4, 9       |
| PRE_FLIGHT_CONFIG  | MOR03 | (future — admin → surface config)                                  | —                   |
| SYNC_ACTIVE_STATE  | MOR04 | `explorer-ui → container` (sync)                                   | —                   |
| ADD_NODE_CONTAINER | MOR05 | (composed — used internally)                                       | Programs 1, 3       |
| LINK_NODES         | MOR06 | (general wiring)                                                   | —                   |
| UPDATE_NODE_KERNEL | MOR07 | (kernel state updates)                                             | —                   |
| UNLINK_EDGE        | MOR08 | (edge removal)                                                     | —                   |
| CAN_SCHEDULE       | MOR09 | (future — kernel → GPU)                                            | —                   |
| CAN_ROUTE          | MOR10 | `tool:category-master → surface:kernel-http` (can_route/transport) | Programs 8, 9       |
| CAN_PERSIST        | MOR11 | (future — container → postgres)                                    | —                   |
| CAN_FEDERATE       | MOR12 | (future — kernel_a → kernel_b)                                     | —                   |
| CAN_FORK           | MOR13 | (future — state → GPU VRAM)                                        | —                   |
| SCORED_ON          | MOR14 | `score:example-001 → model:anthropic:claude-sonnet-4-6`            | Program 10          |
| EVALUATES_TASK     | MOR15 | `score:example-001 → task:single-add`                              | Program 10          |
| BENCHMARKED_BY     | MOR16 | `score:example-001 → suite:morphism-extraction-v1`                 | Program 10          |

---

## Industry → Superset Classification Map

| Industry File            | Industry Count                    | Classifies To                    | Superset Type |
| ------------------------ | --------------------------------- | -------------------------------- | ------------- |
| industry/providers.json  | 15 providers                      | Provider + Model                 | OBJ17, OBJ06  |
| industry/protocols.json  | 11 protocols                      | ProtocolAdapter / RuntimeSurface | OBJ11, OBJ09  |
| industry/tools.json      | 5 paradigms + 100 skills          | SystemTool                       | OBJ07         |
| industry/frameworks.json | 30+ frameworks                    | AppTemplate                      | OBJ04         |
| industry/compute.json    | 6 GPU + 6 cloud + 3 edge + 3 orch | ComputeResource                  | OBJ10         |
| industry/features.json   | 25+ capabilities                  | (cross-cutting)                  | —             |
| industry/benchmarks.json | 5 suites + 13 scores              | BenchmarkSuite + BenchmarkScore  | OBJ18, OBJ20  |

---

## Tier Coverage

| Tier | Programs     | Objects Created                                                             | Status                           |
| ---- | ------------ | --------------------------------------------------------------------------- | -------------------------------- |
| 0    | (file reads) | Registry + Config                                                           | Implemented (loader.go, main.go) |
| 1    | 1-4          | Root, Surface, Kernel, User                                                 | Implemented (seedKernel)         |
| 2    | 5-11         | Providers, Models, Surfaces, Preferences, Tools, Agents, Benchmarks, Config | Spec'd in doctrine/install.md    |

---

## Gap Analysis

Objects with **no instance file yet** (future work):

| Object                | Type             | Blocked By             | Notes                                  |
| --------------------- | ---------------- | ---------------------- | -------------------------------------- |
| OBJ04 AppTemplate     | app_template     | Design needed          | Templates = reusable subgraph patterns |
| OBJ10 ComputeResource | compute_resource | Hardware allocation    | GPU/cloud binding                      |
| OBJ12 InfraService    | infra_service    | Postgres mode optional | Live when `MOOS_KERNEL_STORE=postgres` |
| OBJ13 MemoryStore     | memory_store     | Embedding pipeline     | Depends on FUN03 Embedding functor     |

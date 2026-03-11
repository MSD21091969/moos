# De Novo Install — Fields as Programs

Every field that a fresh `git clone` + `go build` + boot produces is created by a **Program** — a composed sequence of ADD/LINK/MUTATE/UNLINK envelopes submitted to the kernel's 3 write endpoints.

This document is the canonical reference for the install-as-Programs specification.

---

## Boot Sequence

```
git clone <repo> && cd moos
go build -o moos platform/kernel/cmd/kernel
./moos --kb .agent/knowledge_base
```

---

## Tier 0 — File Reads (Pre-boot, Not Programs)

These are file reads that build the in-memory type system and configuration **before** any Programs execute.

| Step | File                          | Purpose                                                      | Go Location                                        |
| ---- | ----------------------------- | ------------------------------------------------------------ | -------------------------------------------------- |
| T0.1 | `superset/ontology.json`      | Build Registry — 21 TypeSpecs, mutable flags, allowed strata | `internal/operad/loader.go → DeriveFromOntology()` |
| T0.2 | `instances/distribution.json` | Extract config — port, store_mode, log_path, registry_path   | `cmd/kernel/main.go → loadConfig()`                |

After Tier 0, the kernel has:

- A populated `operad.Registry` with all 21 object types
- Runtime configuration (port 8000, file store, JSONL log path)
- HTTP server ready but graph state is empty

---

## Tier 1 — Seed Programs (Kernel Self-Hydration)

These Programs execute automatically on first boot when the graph state is empty (`SeedIfAbsent`).

### Program 1: Root Container

```
ADD(urn:moos:root, type=node_container, stratum=S2)
```

Creates the ownership root. All other containers wire here via OWNS.

### Program 2: Kernel Surface Node

```
ADD(urn:moos:surface:kernel-http, type=runtime_surface, stratum=S2, payload={port:8000, protocol:"HTTP"})
LINK(urn:moos:root, 'owns', urn:moos:surface:kernel-http, 'child')
```

Creates the kernel's own HTTP surface and wires it to root.

### Program 3: Kernel Node

```
ADD(urn:moos:kernel:wave-0, type=node_container, stratum=S2, payload={kind:"Kernel"})
LINK(urn:moos:root, 'owns', urn:moos:kernel:wave-0, 'child')
```

Creates the kernel identity node with Feature edges.

### Program 4: Demo User (from identities.json)

```
ADD(urn:moos:user:demo-seeder, type=user, stratum=S2)
LINK(urn:moos:root, 'owns', urn:moos:user:demo-seeder, 'child')
```

Creates the local-dev actor for seeding and testing.

**Source**: `cmd/kernel/main.go → seedKernel()`

---

## Tier 2 — Bootstrap Programs (On-Demand via API)

These Programs are submitted via `POST /programs` or `POST /hydration/materialize` after boot. They transform KB instance data into graph state.

### Program 5: Register Providers (from instances/providers.json)

```
For each provider:
  ADD(urn:moos:provider:<name>, type=provider, stratum=S2, payload={adapter_type, api_base_url, auth_pattern, rate_limits})
  LINK(urn:moos:root, 'owns', urn:moos:provider:<name>, 'child')

  For each model in provider.models:
    ADD(urn:moos:model:<provider>:<model>, type=agnostic_model, stratum=S2, payload={capabilities, context_window, cost})
    LINK(urn:moos:provider:<name>, 'owns', urn:moos:model:<provider>:<model>, 'child')
```

**Morphisms used**: ADD, LINK (via OWNS → MOR01)

### Program 6: Register Surfaces (from instances/surfaces.json)

```
For each surface:
  ADD(urn, type=runtime_surface|protocol_adapter|ui_lens, stratum=S2, payload={port, protocol, entrypoints})
  LINK(urn:moos:root, 'owns', urn, 'child')
```

**Morphisms used**: ADD, LINK (via OWNS → MOR01)

### Program 7: Register Preferences (from instances/preferences.json)

```
For each preference:
  ADD(urn:moos:pref:<key>, type=preference, stratum=S2, payload={key, value, scope, default})
  LINK(urn:moos:user:demo-seeder, 'owns', urn:moos:pref:<key>, 'child')
```

**Morphisms used**: ADD, LINK (via OWNS → MOR01)

### Program 8: Register Tools (from instances/tools.json)

```
For each tool:
  ADD(urn:moos:tool:<name>, type=system_tool, stratum=S2, payload={capabilities, source})
  LINK(urn:moos:root, 'owns', urn:moos:tool:<name>, 'child')
  LINK(urn:moos:tool:<name>, 'can_route', urn:moos:surface:kernel-http, 'transport')
```

**Morphisms used**: ADD, LINK (via OWNS → MOR01, CAN_ROUTE → MOR10)

### Program 9: Create Agent Spec (from instances/agents.json)

```
ADD(urn:moos:agent:copilot-interim, type=agent_spec, stratum=S2, payload={model_binding, temperature, max_tokens})
LINK(urn:moos:user:demo-seeder, 'owns', urn:moos:agent:copilot-interim, 'child')
LINK(urn:moos:agent:copilot-interim, 'can_route', urn:moos:tool:category-master, 'transport')
LINK(urn:moos:agent:copilot-interim, 'can_route', urn:moos:tool:mcp-integration-expert, 'transport')
LINK(urn:moos:agent:copilot-interim, 'can_route', urn:moos:tool:golang-backend-development, 'transport')
... (each routed tool)
```

**Morphisms used**: ADD, LINK (via OWNS → MOR01, CAN_ROUTE → MOR10)

### Program 10: Register Benchmarks (from instances/benchmarks.json)

```
Suite:
  ADD(urn:moos:benchmark:suite:morphism-extraction-v1, type=benchmark_suite, stratum=S2, payload={description, tasks})
  LINK(urn:moos:root, 'owns', suite, 'child')

For each task:
  ADD(urn:moos:benchmark:task:<name>, type=benchmark_task, stratum=S2, payload={prompt_template, expected_morphisms, difficulty})
  LINK(suite, 'owns', task, 'child')

For each score:
  ADD(urn:moos:benchmark:score:<id>, type=benchmark_score, stratum=S3, payload={dimensions})
  LINK(score, 'scored_on', model, 'result')           → MOR14
  LINK(score, 'evaluates_task', task, 'evaluation')    → MOR15
  LINK(score, 'benchmarked_by', suite, 'membership')   → MOR16
```

**Morphisms used**: ADD, LINK (via OWNS → MOR01, SCORED_ON → MOR14, EVALUATES_TASK → MOR15, BENCHMARKED_BY → MOR16)

### Program 11: Register Platform Config (from instances/distribution.json + workstation.json)

```
ADD(urn:moos:config:platform, type=platform_config, stratum=S2, payload={workspace_root, active_platform_root, kernel_module, default_store})
LINK(urn:moos:root, 'owns', urn:moos:config:platform, 'child')

ADD(urn:moos:config:workstation, type=workstation_config, stratum=S2, payload={os, http_port, reserved_ports, optional_services})
LINK(urn:moos:root, 'owns', urn:moos:config:workstation, 'child')
```

**Morphisms used**: ADD, LINK (via OWNS → MOR01)

---

## Summary: Programs × Tiers

| Tier | Programs     | Trigger                                           | Source Files                                                                           |
| ---- | ------------ | ------------------------------------------------- | -------------------------------------------------------------------------------------- |
| 0    | (file reads) | Build-time                                        | ontology.json, distribution.json                                                       |
| 1    | 1-4          | `SeedIfAbsent` on first boot                      | identities.json (hardcoded in main.go)                                                 |
| 2    | 5-11         | `POST /programs` or `POST /hydration/materialize` | providers, surfaces, preferences, tools, agents, benchmarks, distribution, workstation |

**Total graph operations for full bootstrap**: ~50-80 ADD + LINK envelopes depending on active tool/model count.

---

## OS/Program Boundary

The 12 HTTP routes ARE the OS. Programs compose over 3 write endpoints:

| Write Endpoint                | NTs Used                  | Programs Using It              |
| ----------------------------- | ------------------------- | ------------------------------ |
| `POST /state`                 | ADD, LINK, MUTATE, UNLINK | All Programs                   |
| `POST /programs`              | Composed sequences        | Programs 5-11                  |
| `POST /hydration/materialize` | Manifest → Programs       | Explorer demo, batch hydration |

Everything that is not these 12 routes is a Program.

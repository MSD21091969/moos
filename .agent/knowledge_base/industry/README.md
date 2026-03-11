# Industry Layer

The **industry layer** (𝓘) is the curated, independently-maintained external technology landscape that the superset classifies.

## Relationship to Superset

The superset (𝓞_Superset) is a **slice category** over the industry layer. The classifying functor:

```
classify : 𝓘 → 𝓞_Superset
```

maps industry entities to superset `type_id` values. For example:

- Industry entity "Anthropic" → `type_id: "provider"` (OBJ17)
- Industry entity "Claude 3.7 Sonnet" → `type_id: "agnostic_model"` (OBJ06)
- Industry entity "MCP" → `type_id: "protocol_adapter"` (OBJ11)

## Two Independent Change Drivers

1. **Superset evolves** from hypergraph growth — new object kinds, morphisms, categories added as the categorical structure matures.
2. **Industry evolves** independently from the real world — new providers launch, models release, protocols emerge, tools change.

Neither is a subset of the other. The superset TYPES the industry; the industry INSTANCES the types.

## Update Protocol

- **Manual curation**: reviewing new providers, models, protocols
- **Agent-assisted**: skills directory scanning, capability extraction
- **Periodic review**: quarterly refresh of provider/model landscape

## What This Is NOT

- Not mo:os types — those live in `superset/ontology.json`
- Not active instances — those live in `instances/*.json`
- Not runtime config — that's in `instances/distribution.json` and `instances/workstation.json`

This directory stores the raw, curated **tech landscape data** that the superset classifies and instances activate.

## Files

| File            | Content                                 | Superset Types                              |
| --------------- | --------------------------------------- | ------------------------------------------- |
| providers.json  | LLM/AI providers and their capabilities | OBJ17 Provider, OBJ06 AgnosticModel         |
| protocols.json  | API/communication protocols             | OBJ11 ProtocolAdapter, OBJ09 RuntimeSurface |
| tools.json      | Tool paradigms + 100 skills             | OBJ07 SystemTool                            |
| frameworks.json | Development frameworks by domain        | OBJ04 AppTemplate                           |
| compute.json    | Compute resources (GPU, cloud, edge)    | OBJ10 ComputeResource                       |
| features.json   | AI/tech capabilities and patterns       | (cross-cutting)                             |

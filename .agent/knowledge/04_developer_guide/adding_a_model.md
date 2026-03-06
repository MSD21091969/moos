# Adding a Model

## Model as Morphism from Root

A model in mo:os is an `AgnosticModel` container. "Agnostic" means the model
container holds adapter configuration, not the model binary. The kernel does not
load ML weights — it dispatches to an external provider (Gemini, Anthropic,
OpenAI) via the adapter wire.

## Step-by-Step

### 1. ADD the Model Container

```
Morphism: ADD
Target:   urn:moos:model:gemini-pro
Payload:  {
  "type_id": "agnostic_model",
  "state_payload": {
    "provider": "gemini",
    "model_id": "gemini-1.5-pro",
    "adapter": "gemini_chi_adapter",
    "max_tokens": 8192,
    "temperature": 0.7
  }
}
```

This creates a container. It has no wires yet — it is an isolated node.

### 2. LINK to Root Container

```
Morphism: LINK
Source:   urn:moos:system:root
Target:   urn:moos:model:gemini-pro
Port:     can_hydrate
Config:   { "transitive": true }
```

Now the model is discoverable from the root. Any workspace that traverses
CAN_HYDRATE wires from root will find this model (subject to transitivity
declarations on intermediate wires).

### 3. LINK to Adapter/Dispatch Target

```
Morphism: LINK
Source:   urn:moos:model:gemini-pro
Target:   urn:moos:system:adapter:gemini
Port:     dispatches_to
Config:   { "protocol": "http", "endpoint": "https://generativelanguage.googleapis.com/v1beta" }
```

This wire tells the kernel: when someone invokes this model, route the request
through the Gemini adapter. The adapter itself is a container with its own wires
to runtime surfaces.

### 4. Configure Adapter Dispatch

The model container's `state_payload` holds the config. The wire's `wire_config`
holds the dispatch routing. Together they compose the full invocation path:

```
Agent → CAN_HYDRATE → Model Container → DISPATCHES_TO → Adapter → HTTP → Provider
```

### 5. Verify

Query the graph to confirm the model is wired:

```sql
SELECT w.source_urn, w.target_urn, w.source_port, w.wire_config
FROM wires w
WHERE w.source_urn = 'urn:moos:model:gemini-pro'
   OR w.target_urn = 'urn:moos:model:gemini-pro';
```

Expected: at least 2 wires (one incoming from root, one outgoing to adapter).

## Switching Providers

To switch from Gemini to Anthropic:

```
UNLINK(model, gemini_adapter)
LINK(model, anthropic_adapter, port: dispatches_to, config: {endpoint: "..."})
MUTATE(model, state_payload: {provider: "anthropic", model_id: "claude-sonnet-4-20250514"})
```

Three morphisms. No code change. No redeployment. The graph reconfigures itself.

## Adding a Second Model

Repeat steps 1-3 with a new URN. Wire both models to root. Now the agent has two
models to choose from — discovered by graph traversal, selected by
`state_payload.provider` or `state_payload.model_id` matching.
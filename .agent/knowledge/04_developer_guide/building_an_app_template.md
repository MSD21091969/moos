# Building an App Template

## App = Composite Container with template:true

An application template is a container whose `state_payload` includes
`"template": true`. It serves as a blueprint: when a user instantiates it, the
system clones the template's subgraph (its child containers and their wires) into
a new workspace.

## Step-by-Step

### 1. Create the Template Container

```
Morphism: ADD
Target:   urn:moos:template:basic-workspace
Payload:  {
  "type_id": "app_template",
  "state_payload": {
    "template": true,
    "name": "Basic Workspace",
    "description": "A workspace with one model and one tool",
    "version": "1.0.0"
  }
}
```

### 2. Seed Node Containers

Add the child containers that the template includes:

```
ADD(urn:moos:template:basic-workspace:model-slot)
  type_id: "agnostic_model"
  state_payload: { "provider": "gemini", "model_id": "gemini-1.5-pro" }

ADD(urn:moos:template:basic-workspace:tool-slot)
  type_id: "system_tool"
  state_payload: { "command": "echo", "description": "Hello tool" }
```

### 3. Wire CAN_HYDRATE

Connect template to its contents:

```
LINK(urn:moos:template:basic-workspace, model-slot, port: can_hydrate, transitive: true)
LINK(urn:moos:template:basic-workspace, tool-slot, port: can_hydrate, transitive: true)
```

### 4. Wire Template to Root

Make the template discoverable:

```
LINK(urn:moos:system:root, urn:moos:template:basic-workspace, port: can_hydrate)
```

## Instantiation

When a user creates a new workspace from this template:

```
1. ADD(urn:moos:workspace:user-alice:ws-1)     — new workspace container
2. For each child in template:
   a. ADD(urn:moos:workspace:user-alice:ws-1:model-1)  — clone model-slot
   b. MUTATE(model-1, copy state_payload from template's model-slot)
   c. LINK(ws-1, model-1, port: can_hydrate)
3. LINK(alice, ws-1, port: owns)               — assign ownership
4. LINK(ws-1, adapter, port: dispatches_to)    — wire runtime
```

The template itself is never modified. It is a read-only blueprint. Each
instantiation creates new containers and new wires — independent subgraphs that
share no mutable state with the template.

## Template vs Instance

| Aspect        | Template                        | Instance                       |
| ------------- | ------------------------------- | ------------------------------ |
| Mutability    | Read-only after initial setup   | Fully mutable                  |
| Ownership     | Owned by system/admin           | Owned by user                  |
| Wires         | CAN_HYDRATE to slot containers  | CAN_HYDRATE + OWNS + custom    |
| URN pattern   | urn:moos:template:{name}:{slot} | urn:moos:workspace:{user}:{id} |
| state_payload | template: true                  | template: false (or absent)    |

## Updating a Template

Templates are versioned through `state_payload.version`. To update:

```
MUTATE(template_container, state_payload: { ...current, version: "1.1.0" })
```

Existing instances are NOT affected — they are independent subgraphs. New
instances will clone from the updated template.
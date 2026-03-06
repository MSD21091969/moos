# MCP and Tooling

## Tools Are Morphisms

A tool in mo:os is not an object. It has no methods, no class hierarchy, no
inheritance. A tool is a **container wired to dispatch targets**:

```
urn:moos:system:tool:git-commit
  ├── LINK → urn:moos:system:runner:cli     (execution target)
  ├── LINK → urn:moos:system:port:stdin      (input port)
  └── LINK → urn:moos:system:port:stdout     (output port)
```

The tool container's `state_payload` holds configuration (command template,
environment variables, timeout). The wires define what the tool connects to. The
kernel dispatches to the tool by traversing: find tool → follow wire to runner →
execute through runner.

## SystemTool Pattern

The superset ontology defines `SystemTool` as one of the 9 object types. A
SystemTool is:

1. A container with `type_id = 'system_tool'`
2. Wired to one or more `RuntimeSurface` containers via LINK
3. Configured via `state_payload` (JSON: command, args, env, schema)
4. Discovered via graph traversal (agents find tools by walking wires from their
   workspace, not by searching a tool registry)

Discovery is graph-native: "which tools are available?" = "from my workspace
container, traverse CAN_HYDRATE wires to find containers of type system_tool."

## MCP as Protocol Morphism

MCP (Model Context Protocol) is a specific protocol functor surface:

```
F_mcp : tool containers × wires → SSE endpoint at :8080/mcp/sse
```

The MCP server reads tool containers from the graph, constructs the MCP tool
schema from `state_payload`, and exposes them over Server-Sent Events. An MCP
client (Claude Desktop, VS Code Copilot) connects and discovers tools through
the MCP protocol.

MCP does not change the graph model. It is a functor — a read-only projection of
graph state into a protocol format. Tools are added to the graph via ADD/LINK.
MCP just makes them visible over a network protocol.

## Tool Lifecycle

```
Creating a tool:
  ADD(tool_container, type_id='system_tool', state_payload={...config...})
  LINK(workspace, tool_container, port='can_hydrate')
  LINK(tool_container, runner, port='executes_on')

Updating a tool's config:
  MUTATE(tool_container, state_payload={...new_config...})

Removing a tool from a workspace:
  UNLINK(workspace, tool_container)
  (container stays — might be wired to other workspaces)

Deleting a tool entirely:
  UNLINK(all wires involving tool_container)
  (container becomes orphaned — garbage collection optional)
```

There is no `DELETE` morphism for containers. Containers are never destroyed —
only unwired. An unwired container is inert: no edges, no reachability, no effect.
This preserves the morphism log's integrity (log entries reference container URNs
that must continue to exist).

## Agent Tool Discovery

An LLM agent discovers tools through the same graph traversal as everything else:

1. Agent session has a workspace URN
2. Traverse CAN_HYDRATE wires from workspace
3. Filter for containers where `type_id = 'system_tool'`
4. Read `state_payload` for each tool (name, description, input schema)
5. Present to LLM as available functions

No tool registry. No hardcoded list. The graph IS the registry.
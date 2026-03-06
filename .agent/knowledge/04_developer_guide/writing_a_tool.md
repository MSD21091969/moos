# Writing a Tool

## Tool = Container + Dispatch Wire

A tool is a container of type `system_tool` with at least one wire to a runtime
surface (a runner that can execute the tool). Tools have no methods, no class
hierarchy. They are data in the graph — discovered by traversal, configured by
`state_payload`, executed by dispatch.

## Step-by-Step

### 1. ADD the Tool Container

```
Morphism: ADD
Target:   urn:moos:tool:file-reader
Payload:  {
  "type_id": "system_tool",
  "state_payload": {
    "name": "file_reader",
    "description": "Read contents of a file by path",
    "input_schema": {
      "type": "object",
      "properties": {
        "path": { "type": "string", "description": "File path to read" }
      },
      "required": ["path"]
    },
    "output_schema": {
      "type": "object",
      "properties": {
        "content": { "type": "string" },
        "size": { "type": "integer" }
      }
    }
  }
}
```

### 2. LINK to Runner

Wire the tool to the execution target:

```
Morphism: LINK
Source:   urn:moos:tool:file-reader
Target:   urn:moos:system:runner:cli
Port:     executes_on
Config:   { "command": "cat", "timeout_ms": 5000 }
```

The runner container knows how to execute CLI commands. The wire's `wire_config`
holds the command template and execution constraints.

### 3. LINK to Workspace

Make the tool discoverable from a workspace:

```
Morphism: LINK
Source:   urn:moos:infra:workspace:ffs0
Target:   urn:moos:tool:file-reader
Port:     can_hydrate
Config:   { "transitive": true }
```

Now any workspace that inherits from FFS0 (and has transitive CAN_HYDRATE) will
discover this tool.

### 4. Port Type-Checking

The tool's `input_schema` and `output_schema` in `state_payload` define its port
types. When the kernel dispatches a request to this tool, it validates:

- Input matches `input_schema` (JSON Schema validation)
- Output matches `output_schema` (on return)

Port type-checking is a MUTATE-time validation — the same mechanism as schema
validation for any container. Schemas are containers in the graph, not code.

## Tool Dispatch Flow

```
Agent request: "read file at /etc/hostname"
  ↓
Kernel receives morphism request (actor=agent_session, target=tool)
  ↓
Kernel traverses: tool_container → wire(executes_on) → runner_container
  ↓
Runner reads wire_config.command + request payload
  ↓
Runner executes: cat /etc/hostname
  ↓
Runner returns output → Kernel validates against output_schema
  ↓
Kernel logs morphism (MUTATE on the tool container's invocation log)
  ↓
Result returned to agent
```

## MCP Exposure

If the MOOS MCP server (:8080) is running, tools are automatically exposed over
MCP/SSE. The MCP server applies the Protocol functor:

```
F_mcp(tool_container) → MCP tool definition (name, description, inputSchema)
```

The MCP client (Claude Desktop, VS Code) discovers the tool and can invoke it
through the standard MCP protocol. No additional configuration needed — the tool
exists in the graph, the functor projects it.

## Example: Adding a Postgres Query Tool

```
ADD(urn:moos:tool:pg-query, type_id=system_tool, state_payload={
  name: "pg_query",
  description: "Run a read-only SQL query",
  input_schema: { properties: { sql: { type: "string" } }, required: ["sql"] },
  output_schema: { properties: { rows: { type: "array" } } }
})

LINK(pg-query → urn:moos:system:runner:sql, port: executes_on,
     config: { connection: "DATABASE_URL", read_only: true, timeout_ms: 10000 })

LINK(ffs0 → pg-query, port: can_hydrate, config: { transitive: false })
```

Three morphisms. Tool exists, is wired to a runner, is discoverable from FFS0
(but NOT transitively — child workspaces must explicitly wire their own access).
The `read_only: true` in `wire_config` is an edge access rule — the system
policy surface controlling what this wire permits.
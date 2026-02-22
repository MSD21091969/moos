# Collider SDK

> Python SDK components for the Collider ecosystem — seeder, tools, and agent utilities.

## Structure

```text
sdk/
├── seeder/                   # Filesystem → DB sync
│   ├── agent_walker.py       # Walks .agent/ directories, builds NodeContainer objects
│   ├── node_upserter.py      # Upserts nodes to DataServer + registers tools to GraphToolServer
│   └── cli.py                # CLI entry point
└── tools/
    └── collider_tools/       # Atomic tool implementations (code behind ToolDefinition.code_ref)
        ├── _client.py        # Shared httpx client (reads COLLIDER_* env vars)
        ├── nodes.py          # create_node, update_node, get_node, list_nodes, delete_node
        ├── apps.py           # create_app, list_apps, get_app
        ├── permissions.py    # grant_permission, assign_role, list_access_requests
        ├── agent_bootstrap.py # bootstrap_node, discover_skills, list_skills
        └── graph.py          # discover_tools, register_tool
```

## Seeder

Syncs the `.agent/` filesystem hierarchy into Collider DataServer nodes, then registers each
node's tools with GraphToolServer.

```bash
# From repo root
uv run python -m sdk.seeder.cli \
  --root D:/FFS0_Factory \
  --app-id <application-uuid>

# Environment variables (or set in secrets/api_keys.env)
COLLIDER_DATA_SERVER_URL=http://localhost:8000
COLLIDER_USERNAME=Sam
COLLIDER_PASSWORD=Sam
COLLIDER_GRAPH_SERVER_URL=http://localhost:8001   # optional, for tool registration
```

### What the seeder does

1. Walks the filesystem from `--root`, finds every `.agent/manifest.yaml`
2. Reads `instructions/`, `rules/`, `knowledge/`, `skills/`, `tools/` from each `.agent/` directory
3. Builds a `NodeContainer` from the collected content
4. Upserts the node to DataServer (`POST /api/v1/apps/{app_id}/nodes`)
5. For each tool in the node's `NodeContainer.tools`, calls GraphToolServer to register it
   (`POST /api/v1/registry/tools`) so it appears in tool discovery and MCP

### Tool definition format (`.agent/tools/*.json`)

```json
[
  {
    "name": "create_node",
    "description": "Create a new workspace node in the Collider graph",
    "params_schema": {
      "type": "object",
      "properties": {
        "path": { "type": "string" },
        "parent_id": { "type": "string" }
      },
      "required": ["path"]
    },
    "code_ref": "sdk.tools.collider_tools.nodes:create_node",
    "visibility": "global"
  }
]
```

## Tools (`sdk/tools/collider_tools/`)

Atomic Python functions executed by GraphToolServer's `ToolRunner` via `importlib`:

```python
module = importlib.import_module("sdk.tools.collider_tools.nodes")
fn = getattr(module, "create_node")
result = await fn(**inputs)
```

All functions are `async def` and return a `dict`. Authentication token is injected at
call time via the `_client.py` shared httpx client.

### Available tools

| Module            | Functions                                                                    |
| ----------------- | ---------------------------------------------------------------------------- |
| `nodes`           | `create_node`, `update_node`, `get_node`, `list_nodes`, `delete_node`        |
| `apps`            | `create_app`, `list_apps`, `get_app`                                         |
| `permissions`     | `grant_permission`, `assign_role`, `list_access_requests`, `approve_request` |
| `agent_bootstrap` | `bootstrap_node`, `discover_skills`, `list_skills`                           |
| `graph`           | `discover_tools`, `register_tool`                                            |

---
name: collider-mcp
description: >
  Execute Collider platform tools via MCP. Node CRUD, app management,
  permissions, workflows available through the collider-tools MCP server.
---

# Collider Tools via MCP

All Collider platform tools are available through the pre-configured MCP server
(see `.mcp.json` in the workspace root). You do not need separate gRPC calls.

## Available Tool Categories

### Node Operations

- `list_nodes` — List all nodes in an application
- `get_node` — Get a single node by ID
- `get_node_tree` — Get a node and its subtree
- `create_node` — Create a new node
- `update_node` — Update node properties
- `delete_node` — Delete a node

### Application Operations

- `list_apps` — List all applications
- `get_app` — Get application details
- `create_app` — Create a new application

### Permissions

- `list_permissions` — List permissions for a node
- `grant_permission` — Grant permission to a user/role
- `update_permission` — Update existing permission

### Execution

- `execute_workflow` — Execute a named workflow with parameters
- `execute_tool` — Execute a registered tool with parameters

## Usage

Tools are auto-discovered by Claude Code from the MCP server. Simply state what
you want to do and the appropriate tool will be called automatically.

Example: "List all nodes in the current application" will invoke `list_nodes`
via the MCP connection.

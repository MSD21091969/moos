---
name: collider-context
description: >
  Load agent identity, rules, tools, and skills from the Collider DataServer.
  The NodeContainer at COLLIDER_NODE_ID defines who this agent is and what it can do.
version: 1.0.0
metadata:
  {
    "openclaw":
      {
        "emoji": "🕸️",
        "requires":
          {
            "env": ["COLLIDER_URL", "COLLIDER_NODE_ID", "COLLIDER_TOKEN"],
            "anyBins": ["curl", "wget"],
          },
        "install":
          [
            {
              "id": "bootstrap",
              "kind": "custom",
              "label": "Run ./bootstrap.sh to hydrate workspace files from Collider",
            },
          ],
      },
  }
---

# Collider Context Skill

Connects an OpenClaw agent workspace to a running Collider DataServer. On
startup, the agent's identity, guardrails, knowledge, and available tools are
pulled from a `NodeContainer` stored in Collider's node graph.

## When to Use

✅ When this agent's identity and tools are managed in a Collider NodeContainer
✅ To keep the OpenClaw workspace in sync with Collider on session start
✅ In multi-agent setups where Collider distributes context across the tree

## When NOT to Use

❌ When running fully local without a Collider backend
❌ When the NodeContainer is empty (no instructions, tools, or skills defined)

## Setup

1. Set the required environment variables in your shell or OpenClaw config:

   ```bash
   export COLLIDER_URL=http://localhost:8000
   export COLLIDER_NODE_ID=<your-node-uuid>
   export COLLIDER_TOKEN=<jwt-from-login>
   ```

2. Run the bootstrap script once to hydrate the workspace:

   ```bash
   ./bootstrap.sh
   ```

   This writes `AGENTS.md`, `SOUL.md`, `TOOLS.md` and per-skill SKILL.md files
   into `~/.openclaw/workspace/` (or `$OPENCLAW_WORKSPACE_DIR`).

3. Start OpenClaw — it will pick up the hydrated workspace automatically:

   ```bash
   openclaw gateway
   ```

## Execute a Workflow

Ask the agent: `"run workflow <name>"` — the agent will call:

```
POST $COLLIDER_URL/execution/workflow/<name>
Authorization: Bearer $COLLIDER_TOKEN
```

## Re-sync Context

The workspace is static after bootstrap. To pull fresh context from Collider:

```bash
./bootstrap.sh
```

Future: subscribe to `$COLLIDER_URL/sse` for live container updates.

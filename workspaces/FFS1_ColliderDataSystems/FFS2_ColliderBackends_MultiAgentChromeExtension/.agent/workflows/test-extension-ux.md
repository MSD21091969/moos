---
description: Test the Multi-Agent Chrome Extension sidepanel, NanoClawBridge WebSocket flow, and runtime modes (anthropic/pi/pi-shadow)
---

# Testing the Chrome Extension Sidepanel

This workflow verifies sidepanel session composition, WebSocket streaming, and runtime behavior for `anthropic`, `pi`, and `pi-shadow`.

## Prerequisites

Required services:

1. `ColliderDataServer` (:8000)
2. `ColliderGraphToolServer` (:8001)
3. `ColliderAgentRunner` (:8004)
4. `NanoClawBridge` (:18789)
5. `ffs4` or `ffs6` frontend (typically :4201/:4200)

Use the parent workflow: `FFS1/.agent/workflows/dev-start.md`.

## Runtime Mode Setup

Set runtime before launching `NanoClawBridge`:

- `COLLIDER_AGENT_RUNTIME=anthropic` (baseline)
- `COLLIDER_AGENT_RUNTIME=pi` (PI active)
- `COLLIDER_AGENT_RUNTIME=pi-shadow` (Anthropic primary + PI shadow validation)

For pre-prod validation, use `pi-shadow` and keep `PI_SHADOW_SAMPLE_TARGET=20`.

## UI Verification

1. Open service endpoints:
   - `http://localhost:8000/docs`
   - `http://localhost:8001/docs`
   - `http://localhost:8004/docs`
   - `http://localhost:4201/` (ffs4) or `http://localhost:4200/` (ffs6)

2. Open the browser sidepanel and select the Collider extension.

3. In **Tree** tab:
   - select an application
   - select one or more nodes

4. In **Agent** tab:
   - start a session
   - send a test message (`hello runtime`)

5. Expected behavior:
   - user message appears immediately
   - agent response streams with `text_delta`
   - session ends with `message_end`

6. Tool execution test:
   - send `/tool <known_tool> {}`
   - expect `tool_use_start` then `tool_result`

## Runtime-Specific Checks

- `anthropic`: standard response behavior.
- `pi`: PI adapter emits canonical event classes.
- `pi-shadow`: client sees Anthropic stream; shadow KPI checkpoints appear in NanoClawBridge logs.

## Troubleshooting

- Session not created: verify app/node selection and AgentRunner availability.
- No streamed response: check NanoClawBridge logs for `error` events.
- Tool command fails: confirm tool exists in `tool_schemas` for the composed context.
- `pi-shadow` not reporting KPIs: verify `COLLIDER_AGENT_RUNTIME=pi-shadow` in NanoClawBridge environment.

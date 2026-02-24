---
description: Mandatory cross-service validation gates for runtime, context, and tooling changes
---

# Cross-Service Validation Gates

Use this workflow after changes to runtime adapters, context composition, prompt building, tool execution, or websocket event mapping.

## Gate Order

1. **NanoClawBridge tests**

```powershell
cd D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\NanoClawBridge
npm run build
npm test
```

2. **AgentRunner tests**

```powershell
cd D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\ColliderAgentRunner
uv run pytest -q
```

3. **DataServer execution API contract tests**

```powershell
cd D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\ColliderDataServer
uv run pytest tests/test_execution_api.py -q
```

4. **Frontend appnode build gate**

```powershell
cd D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS3_ColliderApplicationsFrontendServer
pnpm nx build ffs4 --verbose
```

## Expected Results

- NanoClawBridge build succeeds and test suite is green (integration skips are acceptable when explicitly gated).
- AgentRunner suite is green.
- DataServer `test_execution_api.py` is green.
- `ffs4` build succeeds.

## pi-shadow Pre-Prod Requirement

When promoting runtime changes beyond dev:

- Set `COLLIDER_AGENT_RUNTIME=pi-shadow`.
- Collect at least 20 representative sessions (`PI_SHADOW_SAMPLE_TARGET=20` default).
- Ensure KPI thresholds stay within targets:
  - Event parity >= 99%
  - Task completion delta <= 10%
  - Tool error rate delta <= 5%
  - Token usage delta <= 15%
  - Critical policy bypasses = 0

Reference:

- `D:/FFS0_Factory/.agent/knowledge/architecture/phase9_shadow_validation_snapshot.md`

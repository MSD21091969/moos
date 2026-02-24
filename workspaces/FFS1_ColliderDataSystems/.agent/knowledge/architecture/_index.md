# FFS1 Architecture Index

Operational architecture index for Collider Data Systems (FFS1).

## Canonical Strategy (FFS0)

- [Collider Skills + Runtime Integration](../../../../../.agent/knowledge/architecture/collider-skills-runtime-integration.md)
- [Phase 5 MVP Execution Checklist](../../../../../.agent/knowledge/architecture/phase5_mvp_execution_checklist.md)
- [Phase 9 Shadow Validation Snapshot](../../../../../.agent/knowledge/architecture/phase9_shadow_validation_snapshot.md)

## FFS1 Operational Architecture Docs

1. [FFS2 Backend Services](01_ffs2_backend_services.md)
2. [FFS2 Chrome Extension](02_ffs2_chrome_extension.md)
3. [FFS3 Frontend Appnodes](03_ffs3_frontend_appnodes.md)
4. [Communication Protocols](04_communication_protocols.md)

## Runtime Modes

- `COLLIDER_AGENT_RUNTIME=anthropic` — baseline runtime.
- `COLLIDER_AGENT_RUNTIME=pi` — PI runtime.
- `COLLIDER_AGENT_RUNTIME=pi-shadow` — Anthropic primary + PI shadow validation.

## Required Validation Gates

See [Cross-Service Validation Gates](../../workflows/cross-service-validation-gates.md).

Minimum gate set:

- NanoClawBridge: `npm test`
- AgentRunner: `uv run pytest -q`
- DataServer execution API: `uv run pytest tests/test_execution_api.py -q`
- FFS3 appnode build: `pnpm nx build ffs4 --verbose`

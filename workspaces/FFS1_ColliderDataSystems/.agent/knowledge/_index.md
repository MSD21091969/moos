# Collider Data Systems — Knowledge Index

Operational knowledge hub for FFS1.  
Canonical architecture strategy lives in FFS0 and is linked here.

## Start Here

1. [Architecture Index](architecture/_index.md)
2. [Start Dev Environment](../workflows/dev-start.md)
3. [Cross-Service Validation Gates](../workflows/cross-service-validation-gates.md)

## Runtime Canonical References (FFS0)

- [Collider Skills + Runtime Integration](../../../../.agent/knowledge/architecture/collider-skills-runtime-integration.md)
- [Phase 5 MVP Execution Checklist](../../../../.agent/knowledge/architecture/phase5_mvp_execution_checklist.md)
- [Phase 9 Shadow Validation Snapshot](../../../../.agent/knowledge/architecture/phase9_shadow_validation_snapshot.md)

## Current Operational Truth (FFS1)

- [FFS2 Backend Services](architecture/01_ffs2_backend_services.md)
- [FFS2 Chrome Extension](architecture/02_ffs2_chrome_extension.md)
- [FFS3 Frontend Appnodes](architecture/03_ffs3_frontend_appnodes.md)
- [Communication Protocols](architecture/04_communication_protocols.md)

## Runtime Status (2026-02-24)

- PI adapter path implemented with context/tools/policy/widget/team extensions.
- Prompt-builder structured workspace context + token budget enforcement implemented.
- `pi-shadow` runtime mode implemented with KPI validation thresholds and reporting.
- Latest local compatibility gates are green across NanoClawBridge, AgentRunner, DataServer, and `ffs4` build.

## Governance

- FFS0 owns architecture strategy/spec and phase snapshots.
- FFS1 owns operational state and runbooks.
- FFS2/FFS3 `.agent` docs are workspace overlays only.
- Update cadence: phase-close updates within 24h + weekly doc sync.

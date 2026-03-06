# FFS0 Factory - Agent Context

Root governance layer for inheritance into FFS1 and downstream workspaces.

## Structure

- `instructions/` — base intent contract (agent_system.md)
- `rules/` — global constraints (sandbox, code_patterns, versioning, env_and_secrets, public_repo_safety)
- `configs/` — shared settings (api_providers, users, workspace_defaults)
- `knowledge/` — canonical architecture references and research papers
- `workflows/` — runbooks for rehydration, db-sync, git collab, pre-public readiness
- `skills/`, `tools/` — reserved for future wiring

## Inheritance Chain

`FFS0 .agent` → `FFS1 .agent` → `FFS2/FFS3 .agent` → app-level `.agent` stubs (`ffs4/ffs5/ffs6`)

Strategy: `deep_merge` at every level.

## Canonical References

### Workflows
- [Conversation Rehydration Runbook](workflows/conversation-state-rehydration.md)
- [Git Collaboration Policy](workflows/git-collaboration-policy.md)
- [Workspace-to-DB Sync Contract](workflows/db-sync-contract.md)
- [Pre-Public Readiness Checklist](workflows/pre-public-readiness-checklist.md)

### Knowledge — Foundations
- [The One Axiom](knowledge/01_foundations/the_one_axiom.md)
- [Categorical Foundations](knowledge/01_foundations/categorical_foundations.md)
- [System 3 Reasoning](knowledge/01_foundations/system_3_reasoning.md)
- [Field Research 2026](knowledge/01_foundations/field_research_2026.md)
- [Pike RAG Integration](knowledge/01_foundations/pike_rag_integration.md)

### Knowledge — Architecture
- [The Four Morphisms](knowledge/02_architecture/the_four_morphisms.md)
- [Kernel Architecture](knowledge/02_architecture/kernel_architecture.md)
- [Functorial Surfaces](knowledge/02_architecture/functorial_surfaces.md)
- [MCP and Tooling](knowledge/02_architecture/mcp_and_tooling.md)

### Knowledge — Implementation
- [Database Schema](knowledge/03_implementation/database_schema.md)
- [Implementation Details](knowledge/03_implementation/implementation_details.md)
- [Security and Auth](knowledge/03_implementation/security_and_auth.md)

### Knowledge — Developer Guide
- [Local Setup](knowledge/04_developer_guide/local_setup.md)
- [Adding a Model](knowledge/04_developer_guide/adding_a_model.md)
- [Building an App Template](knowledge/04_developer_guide/building_an_app_template.md)
- [Writing a Tool](knowledge/04_developer_guide/writing_a_tool.md)

### Knowledge — Superset & Plans
- [MANIFESTO](knowledge/MANIFESTO.md)
- [Superset Architecture Plan](knowledge/superset_architecture_plan.md)
- [Superset Ontology v1](knowledge/superset/superset_ontology_v1.json)
- [Phase 5 UX MVP Baseline](knowledge/phase5_ux_mvp_baseline.md)
- [Living Roadmap](knowledge/living_roadmap_moos.md)
- [Open Source Launch Strategy](knowledge/Open%20Source%20Launch%20&%20App%20Maturity%20Strategy%20moos.md)
- [ACT 2026 Conference Paper Plan](knowledge/Plan%20ACT%202026%20Conference%20Paper_Open%20Source%20Launch%20Strategy.md)
- [Abstract OS Language](knowledge/languagues/abstract_os_language.md)

### Manifest
- [Manifest](manifest.yaml)

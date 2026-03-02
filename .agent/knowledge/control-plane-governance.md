# FFS0 Control Plane Governance

FFS0 is the governance/control plane for the Collider workspace graph.

## Purpose
- Define global policy and inheritance contracts.
- Keep implementation details in FFS1/FFS2/FFS3.
- Keep write access controlled through GitHub permissions and branch protections.

## Scope
- Global `.agent` inheritance and export contracts.
- RBAC policy mapping to GitHub permissions.
- Collaboration and merge workflow standards.
- Workspace-to-DB sync contract for IDE-focused context containers.

## Out of Scope
- Feature implementation and app-specific runtime details.
- Secrets or local machine-specific configuration.

## Operational Rule
Any change affecting inheritance wiring, role semantics, or sync contracts must be documented in FFS0 first, then propagated to FFS1/FFS2/FFS3 as needed.

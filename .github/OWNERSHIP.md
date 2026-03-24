# Ownership Model

This document defines the agent/user/admin/group ownership model for mo:os.

## Role Definitions

| Role    | Label        | Description                                                         |
|---------|--------------|---------------------------------------------------------------------|
| `user`  | `role:user`  | End-user who requested or owns the outcome of a task.               |
| `admin` | `role:admin` | Repository administrator performing ops or policy changes.          |
| `group` | `role:group` | A team or group that collectively owns a scope or deliverable.      |
| `agent` | `role:agent` | An automated agent (AI or bot) executing a task on behalf of a PRG. |

## Applying Ownership

Ownership is declared in:

- **Issues** — via the `Owner Role` dropdown in the [PRG task template](ISSUE_TEMPLATE/prg-task.yml).
- **Pull requests** — via the `User/Admin/Group` field in the [PR template](pull_request_template.md).
- **Labels** — automatically applied by the [PR intake workflow](workflows/pr-intake.yml) based on PR body content.
- **Project fields** — synced to the GitHub Project V2 board by the [project sync workflow](workflows/project-sync.yml).

## Branch Role Mapping

Branch prefixes determine the role context for automation:

| Branch prefix  | Role      | Label            |
|----------------|-----------|------------------|
| `feat/`        | feature   | `branch:feature` |
| `fix/`         | feature   | `branch:feature` |
| `chore/`       | chore     | `branch:chore`   |
| `agent/`       | agent     | `branch:agent`   |
| `admin/`       | admin     | `branch:admin`   |
| `hotfix/`      | hotfix    | `branch:hotfix`  |
| `release/`     | release   | `branch:release` |

Branch naming is enforced by the [branch name guard workflow](workflows/branch-name-guard.yml).

## Governance Axiom

Per **Axiom AX5** in the mo:os design — governance is structural: access control and ownership are
expressed as graph morphisms over the typed hypergraph, not as out-of-band middleware. The labels
and project fields above are the surface representation of those morphisms in the GitHub layer.

## First Execution PR

The first PR to execute against this ownership model is the one that introduced this document,
resolving the *Kickstart: PRG and agent mapping backlog* issue that bootstrapped cloud tracking.

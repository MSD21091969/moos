# Delegation Protocol: Claude Code ↔ VS Code AI

## How It Works

Claude Code (strategic layer) writes task files to `.agent/configs/tasks/`.
VS Code AI (execution layer) picks them up, implements, commits, pushes.

## Handoff Channel

`.agent/knowledge_base/handoff.md` — single bidirectional message board.

- **VS Code AI:** After completing a task or hitting a blocker, append a
  message under `## Messages` (newest on top), commit, and push.
- **Claude Code:** Checks on `git pull`. Responds by appending below.
- Format: `### [YYYY-MM-DD HH:MM] Source → type: subject`
- Types: `complete` | `blocked` | `question` | `answer` | `direction`
- Keep messages short — status, blockers, questions only.
- Questions and answers go in the same file (no separate discussion channel).

## Task File Format

File: `.agent/configs/tasks/YYYYMMDD-NNN-short-name.md`

```markdown
# Task: <title>

**Status:** pending | in_progress | done | blocked
**Priority:** p0 | p1 | p2
**Delegated:** YYYY-MM-DD HH:MM
**Completed:** (filled by VS Code on commit)

## Objective
What needs to happen.

## Files to Touch
- path/to/file.go — what to change

## Acceptance Criteria
- [ ] criterion 1
- [ ] criterion 2

## Context
Links to design docs, relevant knowledge base entries.

## Notes from Execution
(Filled by VS Code AI after implementation)
```

## Git Convention

VS Code commits with: `feat|fix|chore: <description> [task:YYYYMMDD-NNN]`
Claude Code reviews via: `git log --oneline --since="1 hour ago"`

## Knowledge Hydration Convention

VS Code uses YouTube/Arxiv/web skills to fetch content.
Output goes to: `.agent/knowledge_base/reference/digests/<source>-<topic>.md`
Claude Code synthesizes into design docs or ontology updates.

## Shared Surfaces

| Surface | Owner | Consumer |
|---------|-------|----------|
| `.agent/configs/tasks/` | Claude Code writes | VS Code reads + executes |
| `.agent/knowledge_base/` | Both write | Both read |
| `.agent/knowledge_base/handoff.md` | Both write | Both read |
| `platform/kernel/` | VS Code writes code | Claude Code reviews |
| `git log` | VS Code pushes | Claude Code monitors |
| MCP `:8080` (future) | Kernel serves | Both query/mutate |

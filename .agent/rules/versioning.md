# Versioning Strategy

> Keep canonical governance in FFS0, track runtime evolution via explicit versioned artifacts.

---

## Active Structure

```text
D:\FFS0_Factory\
├── .agent/              ← canonical governance and context docs
├── models/              ← active shared schemas/models
├── sdk/                 ← active seeder/tools runtime glue
└── workspaces/          ← execution workspaces (FFS1/FFS2/FFS3)
```

---

## Versioning Rules

1. Canonical terms and process docs are versioned in `.agent/knowledge/*`.
2. Structural migrations are documented as workflow runbooks in `.agent/workflows/*`.
3. Runtime/service versions are tracked in their owning workspace repos.
4. Historical transitions should be preserved in git history/tags, not implicit file-path assumptions.

---

## Canonical References

- `.agent/knowledge/moos_architecture_foundations.md`
- `.agent/workflows/conversation-state-rehydration.md`
- `.agent/workflows/db-sync-contract.md`

---

## Git Strategy

- Use semantic commits for governance/doc updates (`docs:`, `chore:`).
- Keep root `.agent` changes small and traceable.
- Avoid deleting historical context without a replacement reference.
- `.agent/` remains active governance metadata and should not be treated as disposable build output.

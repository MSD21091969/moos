# Public Repository Safety

This rule applies when repositories are public-read and controlled-write.

## Mandatory
- Never commit secrets, tokens, passwords, or private keys.
- Never commit machine-specific auth material.
- Keep role semantics consistent with GitHub permission boundaries.
- Keep branch protection active on protected branches.
- Keep context docs implementation-agnostic at FFS0; implementation detail belongs downstream.

## Documentation Safety
- Avoid leaking sensitive internal infrastructure details in public docs.
- Prefer relative paths where practical in shared/public-facing context docs.
- Keep operational ownership and permission boundaries explicit.

## Review Gate
Any change to auth, permissions, inheritance wiring, or sync contracts requires:
1. Peer review from the owning admin group.
2. Validation of `.agent` include/export path integrity.
3. Confirmation that no sensitive data was introduced.

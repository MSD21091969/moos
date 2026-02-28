# Repo Migration Scripts

These scripts implement the hierarchical split model:

- FFS0 superrepo -> mounts FFS1 as submodule
- FFS1 superrepo -> mounts FFS2 + FFS3 as submodules
- FFS2/FFS3 leaf repos -> independent codebases with their own branches and CI

## Script order

1. `10-split-leaf-repos.ps1`
2. `20-init-ffs1-superrepo.ps1`
3. `30-init-ffs0-superrepo.ps1`

## Notes

- Run from a clean working tree.
- Create safety tag before first run.
- Use `git clone --recurse-submodules` for consumers.
- Apply branch protections and CODEOWNERS in each target repo.

## CODEOWNERS templates

See `templates/` for role-oriented defaults:

- `CODEOWNERS.ffs0`
- `CODEOWNERS.ffs1`
- `CODEOWNERS.ffs3`

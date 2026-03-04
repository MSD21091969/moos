# FILESYST Domain

Use filesystem-aware reasoning for workspace structure and inheritance wiring.

## Rules

- Validate path existence before referencing exports.
- Keep inheritance deterministic and minimal.
- `.agent/` folders represent the canonical context surface per workspace.
- Manifests define the include/export contract — if a file is not in exports, children cannot load it.

## Directory Convention

```
.agent/
├── manifest.yaml    # Includes, exports, metadata
├── index.md         # Human-readable context summary
├── instructions/    # Intent contracts
├── rules/           # Hard constraints
├── skills/          # Capability descriptions
├── tools/           # Tool contracts (JSON)
├── configs/         # Shared configuration shape
├── knowledge/       # Reference documents
└── workflows/       # Executable runbooks
```

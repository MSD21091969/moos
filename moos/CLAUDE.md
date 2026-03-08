# CLAUDE.md — moos

Refer to the root factory instructions at `D:\FFS0_Factory\CLAUDE.md`.

## moos Context

- **Identity**: Platform packaging and preset staging area inside a legacy MOOS snapshot.
- **Active Path**: `D:\FFS0_Factory\moos\platform`
- **Status**: Only `platform/` is active. All other directories under `moos/` are legacy/reference-only.

## Repository Role

The only active forward-work surface in this tree is:

- platform-specific runtime packaging and installer assets under `platform/`
- runtime presets describing how a given environment should launch a kernel at runtime

All other content in `moos/` is preserved as legacy implementation context and should not be treated as the source of truth for future commits.

## Layout

```text
moos/
├── platform/
│   ├── presets/                 # runtime launch presets by environment
│   ├── windows/installers/      # Windows installer payloads and manifests
│   ├── linux/installers/        # Linux packaging payloads and manifests
│   └── darwin/installers/       # macOS packaging payloads and manifests
├── cmd/                         # Legacy
├── internal/                    # Legacy
├── apps/                        # Legacy
├── migrations/                  # Legacy
├── proto/                       # Legacy
├── scripts/                     # Legacy
├── docs/                        # Legacy
└── CLAUDE.md                    # workspace-local authority for kernel work
```

## Platform Packaging Rules

- Presets are declarative environment launch recipes, not hidden shell logic.
- Platform-specific installers (for example `install.exe`) must be accompanied by metadata or checksum notes.
- Runtime environment assumptions should be captured in `platform/presets/` before being embedded into scripts or binaries.
- OS-specific concerns belong under `platform/`.
- When in doubt, prefer extracting values from legacy code rather than editing that code.

## Development

- Edit only `D:\FFS0_Factory\moos\platform\**` for forward work unless explicitly asked to touch archival material.
- Do not treat `cmd/`, `internal/`, `apps/`, `migrations/`, or related runtime code as active implementation.
- Preserve historical values as needed for presets, installer metadata, and migration notes.

## Migration Status

- `D:\FFS0_Factory\moos\platform` is the active MOOS surface.
- The rest of `D:\FFS0_Factory\moos` is legacy snapshot material and should not be part of the forward mainline push set.
- `workspaces/FFS1_ColliderDataSystems/FFS2_ColliderBackends_MultiAgentChromeExtension/moos` remains legacy lineage/reference.

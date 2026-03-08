# Platform Packaging

This directory holds OS-specific runtime packaging assets and declarative presets for launching the moos kernel.

## Purpose

- keep platform code separate from kernel semantics
- version launch presets alongside the runtime
- hold installer payloads or metadata for Windows, Linux, and macOS packaging
- make runtime environment assumptions explicit before they become shell scripts or baked binaries

## Structure

- `presets/` — declarative runtime launch recipes
- `windows/installers/` — Windows installer payloads, manifests, checksums, signing notes
- `linux/installers/` — Linux packaging assets (`.deb`, `.rpm`, shell bootstrap, container entry metadata)
- `darwin/installers/` — macOS installer payloads and packaging metadata

## Rules

- Keep binary installer artifacts intentional and documented.
- Prefer metadata + reproducible build instructions over opaque blobs.
- Capture environment-specific launch assumptions in presets first.

# Configuration And Secret Boundary

## Purpose

Define the authority boundary between committed configuration, local secret material, and optional environment-file compatibility inputs.

## Canonical placement

- `.agent/configs/` is canonical for committed, non-secret configuration.
- `secrets/` is canonical for local secret bindings and secret file paths used by this workspace.
- `.env` is a projection format only, not a canonical source of shared configuration.

## Rules

1. Secret values must not be committed under `.agent/configs/`.
2. `.agent/configs/` may declare secret references such as environment variable names, provider identifiers, model defaults, feature flags, paths, and auth schema.
3. `secrets/` may contain actual credentials, OAuth artifacts, service-account files, and local secret env files.
4. `.env` must remain non-canonical. It may exist only as a generated compatibility projection for tools that require environment files.
5. Example files such as `.env.example` or `secrets/*.example` may document required keys, but they must not contain live credentials.
6. Runtime presets and launch metadata must consume resolved configuration and secret bindings; they must not redefine secret truth.

## Resolution model

1. Resolve workspace or factory root from committed defaults.
2. Read committed configuration from `.agent/configs/`.
3. Resolve required secret keys or credential file paths from local `secrets/` material.
4. Expose only the bindings needed by the active runtime surface.

## Interpretation guidance

- `workspace_defaults.yaml` is the Settings surface. It defines path and feature defaults only.
- `api_providers.yaml` is the Registry surface. It defines provider metadata and the environment variable names required for authentication, but not the secret values themselves.
- `users.yaml` defines auth and identity-object governance schema, not user-secret material.
- `secrets/api_keys.env` is the canonical local secret env file for this workspace when environment-variable based credentials are needed.
- `.env` is not hand-authored source of truth in this workspace.

## Non-goals

- This document does not define ontology.
- This document does not redefine runtime semantics.
- This document does not require a specific secret manager for production deployment.

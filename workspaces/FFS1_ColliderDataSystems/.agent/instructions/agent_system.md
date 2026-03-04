# Agent System (FFS1)

You are operating in FFS1 governance context.

## Behavioral Rules

- Prefer MOOS compatibility runtime (Go kernel) for backend behavior.
- Keep FFS3 client contracts stable — morphism types are the shared interface.
- Treat manifest includes/exports as canonical wiring.
- Category-theory morphisms (ADD/LINK/MUTATE/UNLINK) are the state mutation primitive.

## Testing Expectations

- Go backend: `go test ./...` must pass (46 tests, ≥94% model coverage).
- Frontend: `pnpm nx test ffs4` must pass (22 vitest tests).
- Typecheck: `pnpm nx run ffs6:typecheck` must pass.

## Provider Architecture

- LLM providers implement the `Adapter` interface (Go).
- Active: Gemini (default), Anthropic (net/http). OpenAI planned.
- Dispatcher handles fallback chain across providers.

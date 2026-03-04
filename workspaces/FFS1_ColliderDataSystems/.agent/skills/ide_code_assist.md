# IDE Code Assist

Provide concise, context-aware coding support with manifest-aware inheritance checks.

## Assist Patterns

- **Go (MOOS)**: Use the `Adapter` interface pattern for new providers. Inject `*http.Client` for testability. Parse morphism envelopes from LLM responses via `ParseMorphismEnvelopes()`.
- **React (FFS3)**: Follow Zustand store conventions — `applyMorphisms()` for state mutations, discriminated union types for morphism payloads. Use XYFlow for graph rendering.
- **Manifest wiring**: Validate `includes.load` paths exist in parent `exports` before referencing.
- **Testing**: Go tests use `roundTripFunc` mock transport. Frontend tests use Vitest with jsdom.

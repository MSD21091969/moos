# Contributing to mo:os

Thank you for your interest in contributing to mo:os — the categorical graph kernel for local-first sovereign AI.

---

## Getting Started

### Prerequisites

- Go 1.22 or later (`go version`)
- A knowledge base directory (use `platform/kernel/examples/kb-starter/` as a template)

### Run locally

```bash
git clone https://github.com/your-org/moos
cd moos/platform/kernel
go run ./cmd/moos --kb /path/to/my-kb --hydrate
```

Health check: `curl http://localhost:8000/healthz`

### Run tests

```bash
cd moos/platform/kernel
go test ./...
go vet ./...
```

All 8 packages must pass. No test failures are acceptable on `main`.

---

## How to Contribute

1. **Fork** the repository
2. **Branch** from `main`:
   - Features: `feat/<short-description>`
   - Bug fixes: `fix/<short-description>`
   - Chores: `chore/<short-description>`
3. **Make your change** — see conventions below
4. **Verify:** `go test ./... && go vet ./...` — must be green
5. **Commit** using the format below
6. **Open a PR** targeting `main`

---

## Commit Format

```
<type>: <short description> [task:<id>]

<optional body>
```

Types: `feat` | `fix` | `chore` | `docs` | `test` | `refactor`

Examples:

```
feat: add /log/stream SSE endpoint [task:20260312-013]
fix(operad): derive AllowedStrata from ontology.json [task:20260313-015]
chore: update CHANGELOG for v0.1.0
```

---

## Code Conventions

### The pure/impure boundary is absolute

This is the most important architectural constraint:

| Package                                    | Rule                                                    |
| ------------------------------------------ | ------------------------------------------------------- |
| `cat`                                      | Pure types only. No IO, no sync, no external imports.   |
| `fold`                                     | Pure evaluation. Imports only `cat`.                    |
| `operad`                                   | Pure validation. Imports only `cat`.                    |
| `shell`                                    | Effect boundary. The ONLY package that touches IO/sync. |
| `hydration`, `functor`, `mcp`, `transport` | Call `shell` methods — never mutate graph directly.     |

**Never add IO to `cat` or `fold`.** If you need IO, it belongs in `shell` or `transport`.

### Zero external dependencies

mo:os uses Go's standard library only. **Do not add external packages.**

The `go.mod` contains no `require` directives. Keep it that way.

If you believe an external dependency is genuinely necessary, open an issue first for discussion.

### Table-driven tests

Write tests as table-driven subtests:

```go
func TestMyFunc(t *testing.T) {
    tests := []struct {
        name  string
        input string
        want  string
    }{
        {"basic", "input", "expected"},
        {"edge case", "", ""},
    }
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got := MyFunc(tt.input)
            if got != tt.want {
                t.Errorf("MyFunc(%q) = %q, want %q", tt.input, got, tt.want)
            }
        })
    }
}
```

### Graph mutations go through morphisms

Never modify `shell.Runtime` state directly. All graph writes must be expressed as `cat.Envelope` values (`ADD`, `LINK`, `MUTATE`, `UNLINK`) passed to `runtime.Apply()` or `runtime.ApplyProgram()`.

### Ontology is the SOT

The 21 node types and their port topology are defined in `examples/kb-starter/superset/ontology.json`. If you add a new type, it must be declared there first. Code follows ontology, not the reverse.

---

## What Makes a Good Contribution

**Good:**

- New functor in `internal/functor/` (read-only projection, pure)
- New HTTP route in `internal/transport/` (no business logic, delegates to shell)
- New instance file in a KB (seed data, not code)
- Doc improvement that increases clarity
- Test coverage for uncovered paths

**Requires discussion first:**

- New morphism types (changes the 4-invariant contract)
- New external dependency
- Changes to `cat` package types (breaking change to all dependents)
- Changes to ontology port topology (affects all instance files)

---

## Reporting Issues

Please use GitHub Issues. Include:

- Go version (`go version`)
- OS
- Steps to reproduce
- Expected vs actual behaviour
- Relevant log output or `curl` responses

Label suggestions: `bug`, `enhancement`, `good first issue`, `question`

---

## Good First Issues

Look for issues tagged `good first issue`. These are typically:

- Adding a new instance file to `examples/kb-starter/`
- Improving error messages
- Adding a missing test case
- Documentation clarifications

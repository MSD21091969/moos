# mo:os Kernel

> **Everything reduces to state. State reduces to log. Log reduces to truth.**

The mo:os kernel is a **typed graph database** built from four morphisms and a
pure catamorphism. The entire graph state is a deterministic function of an
append-only morphism log — replay the log, always reconstruct the same graph.

**Go 1.23 · Zero external dependencies · MIT license**

---

## What This Is

The kernel implements the categorical graph model described in [../../README.md](../../README.md).
In plain terms: nodes and wires, four operations, one pure fold. No ORM, no
migrations, no ad-hoc mutation endpoints. The HTTP API exposes the morphism
surface; the Explorer UI lets you browse the graph visually.

For the full developer reference — package map, core concepts, data-flow
diagrams, and glossary — see [DEVELOPERS.md](DEVELOPERS.md).

---

## Prerequisites

- **Go 1.23+** — `go version`
- **Git** — to clone the repo
- **Windows:** PowerShell 5+ (built-in)
- **Linux/macOS:** bash + curl

---

## Quick Start

```powershell
# 1. Clone
git clone https://github.com/your-org/moos.git
cd moos

# 2. Build
Push-Location platform\kernel
go build -o moos.exe .\cmd\moos
Pop-Location

# 3. Boot with the bundled knowledge base
.\platform\kernel\moos.exe --kb .agent\knowledge_base --hydrate
```

The kernel starts on **`:8000`** (HTTP API) and **`:8080`** (MCP SSE bridge).
On first boot it seeds the graph from the ontology and hydrates instance files.

```
[boot] store=file addr=:8000
[boot] registry loaded: 21 types
[boot] hydration: 65 nodes, 80 wires materialised
```

---

## The 8-Step Demo

Run these in a **second terminal** while the kernel is running.

### Step 1 — Health check

```powershell
Invoke-RestMethod http://localhost:8000/healthz
```

```json
{ "status": "ok", "nodes": 65, "wires": 80 }
```

### Step 2 — Full graph state

```powershell
Invoke-RestMethod http://localhost:8000/state | ConvertTo-Json -Depth 4
```

Returns every node and wire. Pipe to `| select nodes, wires` to get counts:

```powershell
$s = Invoke-RestMethod http://localhost:8000/state
"nodes: $($s.nodes.Count)   wires: $($s.wires.Count)"
```

### Step 3 — List all nodes

```powershell
Invoke-RestMethod http://localhost:8000/state/nodes | ForEach-Object {
    "$($_.urn)  [$($_.kind)]  S$($_.stratum)"
}
```

### Step 4 — Look up a specific node

```powershell
$urn = "urn:moos:kernel:wave-0"
Invoke-RestMethod "http://localhost:8000/state/nodes/$($urn)"
```

### Step 5 — Explorer UI

Open in a browser:

```
http://localhost:8000/explorer
```

You'll see an interactive SVG graph: colored circles for all 21 node types,
edge lines for wires, sidebar cards, and kind/stratum filter toggles.

The Explorer calls `GET /functor/ui` — a read-only S4 projection that never
writes morphisms.

### Step 6 — Apply a morphism

Add a new node via `ADD` envelope:

```powershell
$body = @{
  type        = "ADD"
  urn         = "urn:demo:agent:hello-world"
  kind        = "Agent"
  stratum     = "S2"
  payload     = @{ label = "Hello World Agent"; version = "0.1.0" }
  metadata    = @{ created_by = "demo" }
} | ConvertTo-Json

Invoke-RestMethod -Method Post `
  -Uri http://localhost:8000/morphisms `
  -Body $body `
  -ContentType "application/json"
```

Verify:

```powershell
Invoke-RestMethod "http://localhost:8000/state/nodes/urn:demo:agent:hello-world"
```

### Step 7 — Scoped projection

View the kernel actor's subgraph (everything it owns):

```powershell
$actor = "urn:moos:kernel:self"
Invoke-RestMethod "http://localhost:8000/state/scope/$actor" | ConvertTo-Json -Depth 3
```

### Step 8 — MCP bridge

The MCP bridge exposes 5 tools over SSE on `:8080`. To call a tool via
JSON-RPC 2.0:

```powershell
# List available tools
$body = '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
$session = "demo-$(Get-Random)"
Invoke-RestMethod -Method Post `
  -Uri "http://localhost:8080/message?sessionId=$session" `
  -Body $body `
  -ContentType "application/json"
```

```powershell
# Call graph_state tool
$body = @{
  jsonrpc = "2.0"; id = 2; method = "tools/call"
  params  = @{ name = "graph_state"; arguments = @{} }
} | ConvertTo-Json -Depth 4

Invoke-RestMethod -Method Post `
  -Uri "http://localhost:8080/message?sessionId=$session" `
  -Body $body `
  -ContentType "application/json"
```

See [examples/demo.ps1](examples/demo.ps1) for the full interactive walkthrough.
See [examples/demo.sh](examples/demo.sh) for the bash equivalent.

---

## HTTP API Reference

All routes on **`:8000`**.

| Method | Route                         | Description                                      |
| ------ | ----------------------------- | ------------------------------------------------ |
| `GET`  | `/healthz`                    | Liveness check — node + wire counts              |
| `GET`  | `/state`                      | Full graph snapshot (nodes + wires)              |
| `GET`  | `/state/nodes`                | All nodes as array                               |
| `GET`  | `/state/nodes/{urn}`          | Single node by URN                               |
| `GET`  | `/state/wires`                | All wires as array                               |
| `GET`  | `/state/wires/outgoing/{urn}` | Wires where source = urn                         |
| `GET`  | `/state/wires/incoming/{urn}` | Wires where target = urn                         |
| `GET`  | `/state/scope/{actor}`        | Scoped subgraph for an actor URN                 |
| `POST` | `/morphisms`                  | Apply a single envelope (ADD/LINK/MUTATE/UNLINK) |
| `POST` | `/programs`                   | Apply an atomic batch of envelopes               |
| `GET`  | `/log`                        | Full morphism log (append-only history)          |
| `GET`  | `/semantics/registry`         | Operad registry (type constraints)               |
| `POST` | `/hydration/materialize`      | Batch-materialise a declarative JSON manifest    |
| `GET`  | `/functor/ui`                 | S4 projection for the Explorer UI                |
| `GET`  | `/functor/benchmark/{suite}`  | Benchmark functor projection                     |
| `GET`  | `/explorer`                   | Embedded HTML Explorer UI                        |

### Envelope schema

```json
{
  "type":     "ADD | LINK | MUTATE | UNLINK",
  "urn":      "urn:...",
  "kind":     "Agent | Container | ...",
  "stratum":  "S0 | S1 | S2 | S3 | S4",
  "payload":  { ... },
  "metadata": { ... },

  // LINK / UNLINK only:
  "source_urn":  "urn:...",
  "source_port": "OWNS",
  "target_urn":  "urn:..."
}
```

POST `/programs` accepts `{ "envelopes": [ ... ] }` — applied all-or-nothing.

---

## MCP Bridge Reference

SSE server on **`:8080`**. Protocol: JSON-RPC 2.0, MCP version `2024-11-05`.

| Route                       | Description                                          |
| --------------------------- | ---------------------------------------------------- |
| `GET /sse`                  | Open SSE stream (connect once, receive async events) |
| `POST /message?sessionId=…` | Send JSON-RPC request on an active session           |
| `GET /healthz`              | MCP bridge liveness                                  |

### 5 MCP Tools

| Tool                | Arguments          | Description              |
| ------------------- | ------------------ | ------------------------ |
| `graph_state`       | _(none)_           | Full graph snapshot      |
| `node_lookup`       | `urn: string`      | Single node by URN       |
| `apply_morphism`    | `envelope: object` | Apply one envelope       |
| `scoped_subgraph`   | `actor: string`    | Actor-scoped subgraph    |
| `benchmark_project` | _(none)_           | Benchmark functor output |

---

## Explorer UI

Open `http://localhost:8000/explorer` in any modern browser.

- **SVG canvas** — colored circles (one color per node kind, 21 kinds)
- **Sidebar** — click any node to see its URN, kind, stratum, payload
- **Filter toggles** — show/hide by kind and stratum
- **Stratum opacity** — S0=dim, S2=standard, S3=bright

The Explorer is a read-only S4 functor projection. It calls `GET /functor/ui`
and renders the response. It never writes morphisms.

---

## Configuration

The kernel accepts either a JSON config file or a knowledge-base root:

```
moos --config path/to/config.json   # explicit config
moos --kb path/to/kb-root           # derive config from KB root
moos --kb path/to/kb-root --hydrate # + auto-materialise instances on boot
```

When `--kb` is used the kernel derives all paths from the KB directory structure.
`config.json` is always gitignored — it contains absolute machine-specific paths.

Key config fields:

| Field           | Description                                           |
| --------------- | ----------------------------------------------------- |
| `store_type`    | `"file"` (default) or `"memory"`                      |
| `log_path`      | Absolute path to morphism-log.jsonl                   |
| `registry_path` | Absolute path to ontology.json                        |
| `listen_addr`   | HTTP listen address (default `:8000`)                 |
| `seed`          | Array of seed programs (applied idempotently on boot) |

---

## Testing

```powershell
Push-Location platform\kernel
go test ./...
Pop-Location
```

All packages include table-driven tests with `t.Run`. The MCP bridge tests use
`httptest.NewServer` for real HTTP round-trips over SSE.

---

## Architecture

```
kernel/
├── cmd/moos/main.go     # Boot: config → store → registry → runtime → seed → HTTP
├── internal/
│   ├── cat/             # Value types: Node, Wire, Envelope, Program, GraphState
│   ├── fold/            # Pure catamorphism: Evaluate(), Replay() — NO side effects
│   ├── operad/          # Type system: validates operations against ontology
│   ├── shell/           # Effect boundary: RWMutex + persistence + fold
│   ├── functor/         # Read-path projections: UI, benchmark
│   ├── mcp/             # MCP SSE bridge: JSON-RPC 2.0, 5 tools
│   ├── transport/       # HTTP API: 16 routes + embedded Explorer HTML
│   ├── hydration/       # Batch materialization from declarative JSON manifests
│   └── config/          # JSON config loader — no env vars, no magic defaults
├── registry/            # ontology.json + schema.json (committed)
└── go.mod               # Module: moos/platform/kernel, zero external deps
```

The **pure/impure boundary** is absolute:

- `cat` + `fold` + `operad` → pure, no IO, import stdlib only
- `shell` → wraps fold with `sync.RWMutex` and store writes
- `transport` + `mcp` → HTTP handlers, call shell methods only

See [DEVELOPERS.md](DEVELOPERS.md) for the full package walkthrough, Python-analogy
table, write/read data flow diagrams, and complete HTTP API documentation.

---

## Contributing

1. Fork + branch off `main`
2. `go test ./...` must be green before PR
3. All graph writes must use the four morphisms — no direct state mutation
4. `fold` package must remain IO-free (CI enforces zero imports of `os`, `net`, `sync`)
5. Commit format: `feat|fix|chore: description [task:YYYYMMDD-NNN]`

---

## License

MIT — see [LICENSE](../../LICENSE) at repo root.

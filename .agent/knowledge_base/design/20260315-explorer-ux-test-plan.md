# Explorer UX Test Plan — Headless Browser

**Date:** 2026-03-15
**Scope:** Task 011 precheck — comprehensive UX/UI validation of mo:os Explorer
**Target:** `http://localhost:8000/explorer` (kernel HTTP) + `http://localhost:8080` (MCP SSE)
**Tool:** Headless browser (Playwright/Puppeteer/antgraviti IDE headless)
**Prereq:** Kernel running with `--kb` and `--hydrate` flags

---

## 0. Server Health Preconditions

Before any browser test, validate both servers are live.

| #   | Test                       | Method                                                     | Expected                                                |
| --- | -------------------------- | ---------------------------------------------------------- | ------------------------------------------------------- |
| 0.1 | Kernel HTTP alive          | `GET http://localhost:8000/healthz`                        | `{"status":"ok","nodes":65,"wires":80,"log_depth":145}` |
| 0.2 | MCP SSE alive              | `GET http://localhost:8080/healthz`                        | `{"status":"ok"}`                                       |
| 0.3 | UI functor responds        | `GET http://localhost:8000/functor/ui`                     | JSON with `nodes[]` (65 items) and `edges[]` (80 items) |
| 0.4 | Benchmark functor responds | `GET http://localhost:8000/functor/benchmark/`             | JSON with `suites[]` array                              |
| 0.5 | Explorer HTML serves       | `GET http://localhost:8000/explorer` response Content-Type | `text/html`                                             |

---

## 1. Page Load & Structure

| #   | Test                      | Selector / Action                      | Expected                                             |
| --- | ------------------------- | -------------------------------------- | ---------------------------------------------------- |
| 1.1 | Page loads without errors | Navigate to `/explorer`, check console | Zero JS errors, zero failed network requests         |
| 1.2 | Title correct             | `document.title`                       | `"mo:os — Explorer (FUN02 UI_Lens)"`                 |
| 1.3 | Header renders            | `header h1`                            | Text content: `"mo:os Explorer"`                     |
| 1.4 | FUN02 badge present       | `header .badge:nth-child(2)`           | Text: `"FUN02 UI_Lens"`, background-color: `#238636` |
| 1.5 | Read-only badge present   | `header .badge:nth-child(3)`           | Text: `"S4 read-only"`, background-color: `#1f6feb`  |
| 1.6 | Container layout is flex  | `.container` computed style            | `display: flex`, `height: calc(100vh - 48px)`        |
| 1.7 | Sidebar width             | `.sidebar` computed style              | `width: 340px`                                       |
| 1.8 | Dark theme                | `body` computed `background-color`     | `rgb(11, 18, 32)` (= `#0b1220`)                      |

---

## 2. Data Fetch & Functor Projection

| #    | Test                                     | Method                                     | Expected                                                                                                                                                                                                                                                                                                                                                                |
| ---- | ---------------------------------------- | ------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2.1  | `/functor/ui` fetch succeeds             | Intercept network request to `/functor/ui` | HTTP 200, Content-Type `application/json`                                                                                                                                                                                                                                                                                                                               |
| 2.2  | Response has `nodes` array               | Parse JSON body                            | `data.nodes` is array, length ≥ 50                                                                                                                                                                                                                                                                                                                                      |
| 2.3  | Response has `edges` array               | Parse JSON body                            | `data.edges` is array, length ≥ 70                                                                                                                                                                                                                                                                                                                                      |
| 2.4  | Each node has required fields            | Validate `data.nodes[*]`                   | Every node has: `id` (string), `kind` (string), `stratum` (string), `label` (string), `x` (number), `y` (number)                                                                                                                                                                                                                                                        |
| 2.5  | Each edge has required fields            | Validate `data.edges[*]`                   | Every edge has: `id` (string), `source` (string), `target` (string)                                                                                                                                                                                                                                                                                                     |
| 2.6  | Node IDs are URNs                        | Check `data.nodes[*].id`                   | Every ID starts with `"urn:moos:"`                                                                                                                                                                                                                                                                                                                                      |
| 2.7  | All 21 type_ids represented              | Collect unique `data.nodes[*].kind` values | Set includes: `user`, `collider_admin`, `superadmin`, `agent_spec`, `app_template`, `node_container`, `agnostic_model`, `system_tool`, `compute_resource`, `provider`, `ui_lens`, `runtime_surface`, `protocol_adapter`, `infra_service`, `memory_store`, `platform_config`, `workstation_config`, `preference`, `benchmark_suite`, `benchmark_task`, `benchmark_score` |
| 2.8  | Strata are valid enum values             | Check `data.nodes[*].stratum`              | Every stratum ∈ `{S0, S1, S2, S3, S4}`                                                                                                                                                                                                                                                                                                                                  |
| 2.9  | broad_category populated                 | Check `data.nodes[*].broad_category`       | Every node has non-empty `broad_category` ∈ `{identity, structure, compute, surface, protocol, infra, memory, platform, config, evaluation}`                                                                                                                                                                                                                            |
| 2.10 | Deterministic positions                  | Fetch `/functor/ui` twice                  | Same `x`, `y` values for same node IDs                                                                                                                                                                                                                                                                                                                                  |
| 2.11 | No duplicate node IDs                    | Check uniqueness                           | `Set(nodes.map(n => n.id)).size === nodes.length`                                                                                                                                                                                                                                                                                                                       |
| 2.12 | No duplicate edge IDs                    | Check uniqueness                           | `Set(edges.map(e => e.id)).size === edges.length`                                                                                                                                                                                                                                                                                                                       |
| 2.13 | Edge source/target reference valid nodes | Cross-reference                            | Every `edge.source` and `edge.target` exists in `nodes[*].id`                                                                                                                                                                                                                                                                                                           |

---

## 3. SVG Canvas Rendering

| #    | Test                                | Selector / Action               | Expected                                                                                        |
| ---- | ----------------------------------- | ------------------------------- | ----------------------------------------------------------------------------------------------- |
| 3.1  | SVG element exists                  | `svg#graph`                     | Present, fills canvas area                                                                      |
| 3.2  | SVG has child elements              | `svg#graph > g`                 | Count > 0 (at least some nodes and edges rendered)                                              |
| 3.3  | Node groups render                  | `svg .node`                     | Count matches visible node count in sidebar                                                     |
| 3.4  | Each node has circle                | `svg .node circle`              | Each has `r="8"`, non-empty `fill` attribute                                                    |
| 3.5  | Each node has text label            | `svg .node text`                | Each has non-empty `textContent`                                                                |
| 3.6  | Edge groups render                  | `svg .edge`                     | Count matches visible edge count                                                                |
| 3.7  | Each edge has line                  | `svg .edge line`                | Each has `x1`, `y1`, `x2`, `y2` attributes set                                                  |
| 3.8  | Edge lines have stroke              | `svg .edge line` computed style | `stroke: #4a5f83`, `stroke-width: 1.5`                                                          |
| 3.9  | Node circles use ontology colors    | For known types, check `fill`   | `user` circle fill = `#ffd166`, `benchmark_suite` fill = `#fb923c`, `provider` fill = `#83c5be` |
| 3.10 | Stratum affects opacity             | Compare circle `fill-opacity`   | S0 nodes: 0.55, S2 nodes: 0.86, S3 nodes: 1.0                                                   |
| 3.11 | Nodes positioned in positive coords | Check `transform` attribute     | All `translate(x, y)` values have `x > 0` and `y > 0`                                           |
| 3.12 | No node overlap (basic)             | Collect all transform positions | No two nodes share identical (x, y)                                                             |

---

## 4. Sidebar Node Cards

| #    | Test                             | Selector / Action                              | Expected                                                                                                |
| ---- | -------------------------------- | ---------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| 4.1  | Loading state clears             | `#node-list .loading` after data fetch         | Element removed (no `.loading` child)                                                                   |
| 4.2  | Card count matches stats         | `#node-list .node-card` count                  | Equals number shown in `#stats` text (e.g. "65 nodes")                                                  |
| 4.3  | Each card has URN                | `.node-card .urn`                              | Non-empty text, starts with `urn:moos:` or is a display label                                           |
| 4.4  | Each card has kind-pill          | `.node-card .kind-pill`                        | Non-empty text, has `background` inline style                                                           |
| 4.5  | Kind-pill color matches ontology | Check `.kind-pill` background per type         | `user` pill → `#ffd166`, `node_container` pill → `#4cc9f0`, etc.                                        |
| 4.6  | Each card has stratum-pill       | `.node-card .stratum-pill`                     | Text ∈ `{S0, S1, S2, S3, S4}`                                                                           |
| 4.7  | Each card has category-pill      | `.node-card .category-pill`                    | Text ∈ `{identity, structure, compute, surface, protocol, infra, memory, platform, config, evaluation}` |
| 4.8  | Card hover effect                | Hover over card, check computed `border-color` | Changes to `#58a6ff`                                                                                    |
| 4.9  | Sidebar is scrollable            | Check `overflow-y` on `.sidebar`               | `overflow-y: auto`, scrollHeight > clientHeight (with 65 nodes)                                         |
| 4.10 | Cards sorted deterministically   | Collect card URN order                         | Same order on page reload                                                                               |

---

## 5. Stats Display

| #   | Test                          | Selector / Action                 | Expected                                     |
| --- | ----------------------------- | --------------------------------- | -------------------------------------------- |
| 5.1 | Stats text present            | `#stats` textContent              | Matches pattern `^\d+ nodes, \d+ edges$`     |
| 5.2 | Node count ≥ 50               | Parse number from stats           | Extracted node count ≥ 50                    |
| 5.3 | Edge count ≥ 70               | Parse number from stats           | Extracted edge count ≥ 70                    |
| 5.4 | Stats update on filter toggle | Toggle a filter, re-read `#stats` | Numbers change (decrease when filtering out) |

---

## 6. Filter Toggles — Glossary

| #   | Test                                 | Selector / Action                     | Expected                                     |
| --- | ------------------------------------ | ------------------------------------- | -------------------------------------------- |
| 6.1 | Glossary toggle unchecked by default | `#toggle-cat.checked`                 | `false`                                      |
| 6.2 | Glossary nodes hidden by default     | Check for `urn:moos:cat:*` in sidebar | Zero cards with URN starting `urn:moos:cat:` |
| 6.3 | Enable glossary toggle               | Click `#toggle-cat`                   | Checkbox becomes checked                     |
| 6.4 | Glossary nodes appear in sidebar     | Count cards with `urn:moos:cat:` URN  | Count > 0                                    |
| 6.5 | Glossary nodes appear in SVG         | Count new `.node` groups in SVG       | SVG node count increases                     |
| 6.6 | Stats update                         | `#stats` text                         | Node and edge counts increase                |
| 6.7 | Disable glossary toggle              | Uncheck `#toggle-cat`                 | Glossary nodes removed from sidebar and SVG  |
| 6.8 | Counts return to original            | `#stats` text                         | Same numbers as before toggle                |

---

## 7. Filter Toggles — Kernel/Feature

| #   | Test                                | Selector / Action                                 | Expected                     |
| --- | ----------------------------------- | ------------------------------------------------- | ---------------------------- |
| 7.1 | System toggle unchecked by default  | `#toggle-system.checked`                          | `false`                      |
| 7.2 | Kernel/feature nodes hidden default | Check sidebar for kind=`kernel` or `feature`      | Zero cards with those kinds  |
| 7.3 | Enable system toggle                | Click `#toggle-system`                            | Checkbox becomes checked     |
| 7.4 | Kernel/feature nodes appear         | Count cards with `kind-pill` = `kernel`/`feature` | Count ≥ 1                    |
| 7.5 | Disable system toggle               | Uncheck `#toggle-system`                          | Kernel/feature nodes removed |

---

## 8. Combined Filter Interactions

| #   | Test                          | Selector / Action                           | Expected                                      |
| --- | ----------------------------- | ------------------------------------------- | --------------------------------------------- |
| 8.1 | Both filters on               | Check both `#toggle-cat` + `#toggle-system` | Highest node/edge count (all visible)         |
| 8.2 | Both filters off              | Uncheck both                                | Lowest count (no glossary, no kernel/feature) |
| 8.3 | Toggle order independence     | Enable cat→system vs system→cat             | Same final count either way                   |
| 8.4 | Edge visibility follows nodes | With filter hiding source node              | Edge connected to hidden node also hidden     |
| 8.5 | Rapid toggle doesn't break    | Toggle each filter 10x rapidly              | No JS errors, final render matches state      |

---

## 9. Color Map Completeness

Verify every ontology type_id has a distinct color assignment in the rendered UI.

| #    | type_id              | Expected Color | Test                                         |
| ---- | -------------------- | -------------- | -------------------------------------------- |
| 9.1  | `user`               | `#ffd166`      | Find node with kind=user, verify circle fill |
| 9.2  | `collider_admin`     | `#f4a261`      | Find node, verify fill                       |
| 9.3  | `superadmin`         | `#e76f51`      | Find node, verify fill                       |
| 9.4  | `agent_spec`         | `#ef476f`      | Find node, verify fill                       |
| 9.5  | `app_template`       | `#2a9d8f`      | Find node, verify fill                       |
| 9.6  | `node_container`     | `#4cc9f0`      | Find node, verify fill                       |
| 9.7  | `agnostic_model`     | `#72efdd`      | Find node, verify fill                       |
| 9.8  | `system_tool`        | `#90be6d`      | Find node, verify fill                       |
| 9.9  | `compute_resource`   | `#5bc0be`      | Find node, verify fill                       |
| 9.10 | `provider`           | `#83c5be`      | Find node, verify fill                       |
| 9.11 | `ui_lens`            | `#f7b267`      | Find node, verify fill                       |
| 9.12 | `runtime_surface`    | `#f4845f`      | Find node, verify fill                       |
| 9.13 | `protocol_adapter`   | `#9d4edd`      | Find node, verify fill                       |
| 9.14 | `infra_service`      | `#577590`      | Find node, verify fill                       |
| 9.15 | `memory_store`       | `#b8de6f`      | Find node, verify fill                       |
| 9.16 | `platform_config`    | `#a5b4fc`      | Find node, verify fill                       |
| 9.17 | `workstation_config` | `#818cf8`      | Find node, verify fill                       |
| 9.18 | `preference`         | `#c4b5fd`      | Find node, verify fill                       |
| 9.19 | `benchmark_suite`    | `#fb923c`      | Find node, verify fill                       |
| 9.20 | `benchmark_task`     | `#fdba74`      | Find node, verify fill                       |
| 9.21 | `benchmark_score`    | `#fed7aa`      | Find node, verify fill                       |

---

## 10. XSS / Security (escapeHtml)

| #    | Test                            | Method                                                                          | Expected                                   |
| ---- | ------------------------------- | ------------------------------------------------------------------------------- | ------------------------------------------ |
| 10.1 | escapeHtml sanitizes `<script>` | Inject node with label `<script>alert(1)</script>` via `/morphisms` then reload | Label renders as text, no script execution |
| 10.2 | escapeHtml sanitizes quotes     | Inject node with label `"onload="alert(1)`                                      | Renders as literal text                    |
| 10.3 | URN with special chars safe     | Node URN with `&`, `<`, `>`                                                     | Rendered safely via escapeHtml             |

---

## 11. Error Handling

| #    | Test                   | Method                                  | Expected                                                                 |
| ---- | ---------------------- | --------------------------------------- | ------------------------------------------------------------------------ |
| 11.1 | Server down gracefully | Stop kernel, load `/explorer`           | "Failed to load" error message in `#node-list` with red text (`#f85149`) |
| 11.2 | Error message visible  | Check `.loading` element in error state | Contains "Failed to load:" prefix                                        |
| 11.3 | Partial data recovery  | Start server after error, reload page   | Explorer recovers and renders normally                                   |

---

## 12. Performance & Responsiveness

| #    | Test                     | Method                                                     | Expected                                   |
| ---- | ------------------------ | ---------------------------------------------------------- | ------------------------------------------ |
| 12.1 | Initial render time      | Measure from navigation start to last SVG element appended | < 2000ms for 65 nodes + 80 edges           |
| 12.2 | Filter toggle response   | Measure from click to render complete                      | < 200ms                                    |
| 12.3 | No memory leak on toggle | Toggle filters 50 times, check JS heap                     | Heap size stays stable (no runaway growth) |
| 12.4 | SVG scales with viewport | Resize browser window                                      | SVG fills 100% of `.canvas-area`           |

---

## 13. Cross-Endpoint Integration (API Round-Trip)

These tests validate the full stack from the kernel REST API through to the UI.

| #    | Test                                       | Method                                                              | Expected                                              |
| ---- | ------------------------------------------ | ------------------------------------------------------------------- | ----------------------------------------------------- |
| 13.1 | `/state` node count matches UI             | `GET /state` → count nodes, compare to `#stats`                     | Numbers match (accounting for glossary/system filter) |
| 13.2 | `/functor/ui` nodes match sidebar          | Count `/functor/ui` response nodes vs `#node-list .node-card` count | Match (with default filters)                          |
| 13.3 | `/functor/benchmark/` accessible           | `GET /functor/benchmark/`                                           | Returns valid JSON with suites array                  |
| 13.4 | `/state/scope/{actor}` returns subset      | `GET /state/scope/urn:moos:identity:admin-local-dev`                | Returns scoped subgraph with OWNS children            |
| 13.5 | Scoped view is strict subset of full state | Compare scoped nodes to full `/state`                               | Every scoped node exists in full state                |

---

## 14. MCP Bridge (port 8080) Integration

| #    | Test                          | Method                                                           | Expected                                                                                                 |
| ---- | ----------------------------- | ---------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| 14.1 | SSE endpoint connects         | `GET http://localhost:8080/sse` with `Accept: text/event-stream` | Receives `endpoint` event with session URL                                                               |
| 14.2 | Initialize handshake          | POST JSON-RPC `initialize` with correct params                   | Response includes `serverInfo`, `capabilities.tools`                                                     |
| 14.3 | tools/list returns 5 tools    | POST `tools/list`                                                | Array of 5 tools: `graph_state`, `node_lookup`, `apply_morphism`, `scoped_subgraph`, `benchmark_project` |
| 14.4 | graph_state tool returns data | POST `tools/call` with `graph_state`                             | Returns JSON with nodes and wires counts matching `/healthz`                                             |
| 14.5 | node_lookup finds known node  | POST `tools/call` with `node_lookup` + URN                       | Returns node data                                                                                        |
| 14.6 | scoped_subgraph by actor      | POST `tools/call` with `scoped_subgraph` + actor URN             | Returns OWNS subtree                                                                                     |
| 14.7 | Unknown session rejected      | POST `/message` with invalid session ID                          | JSON-RPC error response                                                                                  |

---

## 15. Accessibility Baseline

| #    | Test                           | Method                                         | Expected                                             |
| ---- | ------------------------------ | ---------------------------------------------- | ---------------------------------------------------- |
| 15.1 | HTML lang attribute            | `<html lang="en">`                             | Present                                              |
| 15.2 | Viewport meta                  | `<meta name="viewport">`                       | Present with `width=device-width, initial-scale=1.0` |
| 15.3 | Text contrast                  | Body text `#dbe7ff` on `#0b1220`               | WCAG AA pass (contrast ratio > 4.5:1)                |
| 15.4 | Kind-pill text contrast        | Dark text `#0d1117` on lightest pill `#fed7aa` | WCAG AA pass                                         |
| 15.5 | Interactive elements focusable | Tab through checkboxes                         | Both toggle checkboxes receive focus                 |

---

## Execution Checklist

```
[ ] Start kernel: go run ./cmd/moos --kb <kb> --hydrate (from platform/kernel/)
[ ] Verify: curl http://localhost:8000/healthz → 65 nodes, 80 wires
[ ] Verify: curl http://localhost:8080/healthz → ok
[ ] Run Section 0: Server preconditions
[ ] Run Sections 1-5: Page structure, data, canvas, sidebar, stats
[ ] Run Sections 6-8: Filter toggle interactions
[ ] Run Section 9: Color map completeness (21 types)
[ ] Run Section 10: XSS security
[ ] Run Section 11: Error handling
[ ] Run Section 12: Performance
[ ] Run Sections 13-14: API + MCP integration
[ ] Run Section 15: Accessibility
[ ] Report results
```

**Total test cases: 95**

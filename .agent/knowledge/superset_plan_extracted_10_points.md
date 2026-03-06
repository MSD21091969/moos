# 10 Key Points Extracted from superset_architecture_plan.md

> Source: `.agent/knowledge/superset_architecture_plan.md` (now deleted)
> Extracted: 2026-session | Branch: `chore/moos-overhaul-prep`

These are the 10 most actionable/structural points from the plan that are NOT already captured in foundations.md v3.0 or architecture.md v3.0. They carry forward as next-session reference.

---

## 1. Z440 as Semantic Functor (§2.1)
The physical machine IS the semantic functor — the structure-preserving mapping from abstract categories to execution. Abstract `compute.gpu` → 12GB device, `infra.postgres` → Docker PG container, `protocol.ws` → :18789 listener. This functor concept is not yet formalized in v2 ontology.

## 2. VRAM Budget: 10K Containers ≈ 10MB (§3.1)
~10K containers × ~1KB = ~10MB active state in GPU. 12GB leaves massive headroom for parallel branch caches, model weights, tensor buffers. This is the empirical sizing basis for CAN_FORK Phase D.

## 3. kind Column Is Free TEXT — Zero Schema Migration (§5.2 / §6.4)
PostgreSQL `kind` column has NO CHECK constraint. Adding new category kinds (`compute.*`, `protocol.*`, `infra.*`, `memory.*`) requires zero schema changes — purely data + ontology operation. Executor already handles ADD/LINK/MUTATE/UNLINK for ANY kind.

## 4. Phase B: Graph-Driven Bootstrap (§7 Phase B)
Kernel startup should query `containers` table for available categories (`WHERE kind LIKE 'model.%'`, `compute.%`, etc.). Model dispatch resolves providers from `model.*` containers — replaces `config.ModelProvider` env var. Tool dispatch resolves from `compute.*` LINKs — replaces hardcoded `runner.address`.

## 5. Phase C Step 10: Interface Port Type-Checking on LINK (§7 Phase C)
Before writing a wire, validate `from_port` output schema is compatible with `to_port` input schema. Composability safety, NOT restriction. Implementation point: `internal/container/store.go Link()` method — add pre-check before SQL insert.

## 6. Phase C Step 13: CAN_HYDRATE Go Implementation (§7 Phase C)
Read template container, clone topology into new URN namespace, set owner. Verifiable: CAN_HYDRATE creates working instance from 2XZ template. This is the template instantiation workhorse.

## 7. Phase D Step 14: CAN_FORK Full Decomposition (§7 Phase D)
(a) Fork in-memory graph into CUDA-addressable memory, (b) Run parallel branch scoring per `categorical_foundations.md` §7.3, (c) Collapse winning branch back to main. GPU benchmark target: measure VRAM usage for 10K-container graph.

## 8. Phase D Step 15: CAN_FEDERATE Discovery Protocol (§7 Phase D)
Discovery via mDNS or explicit config. Schema negotiation: exchange ontology versions before LINK. Remote MUTATE proxying through federation wire. Verifiable: two kernels exchange morphisms across network.

## 9. Design Question §10.1: Category-as-Container (Resolved Direction)
Should a category itself be stored as a container (kind=category, kernel_json holds objects+morphisms)? Plan recommends YES — eliminates JSON/DB split, satisfies DB_Is_Truth axiom. Makes superset ontology entirely graph-native.

## 10. Design Question §10.2: Graph Complexity Budget Threshold
At what edge/node ratio does discovery become too expensive for real-time? Practical workspace graphs are sparse (2-5 edges/node). Action: collect empirical data once Phase A seeds exist, define soft budget threshold. Ties to corrected edge density formula k/(n² · |P_s| · |P_t|).

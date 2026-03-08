# HyperGraphRAG — Paper Digest

> **Paper:** Luo et al., "HyperGraphRAG: Retrieval-Augmented Generation via Hypergraph-Structured Knowledge Representation" (NeurIPS 2025, arXiv:2503.21322v3)
>
> **Digest purpose:** Extract concepts relevant to mo:os categorical foundations, hypergraph storage, and retrieval architecture.

---

## Core Thesis

Standard graph-based RAG (GraphRAG, LightRAG, etc.) decomposes knowledge into binary triples $(s, r, o)$. This is **provably lossy** for n-ary relational facts. HyperGraphRAG replaces the binary knowledge graph with a **knowledge hypergraph** $G_H = (V, E_H)$ where each hyperedge $e_H \in E_H$ connects $n \geq 2$ entities through a single n-ary relation.

---

## Key Mathematical Results

### Proposition 1 — Binary Decomposition Is Lossy

Given a knowledge hypergraph $G_H$ and its binary decomposition $\phi_B(G_H)$:

$$H(X \mid \phi_B(X)) > 0 \quad \text{while} \quad H(X \mid \phi_H(X)) = 0$$

where $H$ is Shannon conditional entropy. Binary decomposition **destroys information** that was present in the n-ary structure. The hypergraph representation preserves it completely.

**mo:os relevance:** This validates `foundations.md` §4 (Hypergraph Superposition). The mo:os wire model with its 4-tuple uniqueness `(source_urn, source_port, target_urn, target_port)` preserves port-typed multi-edges between any node pair. If we collapsed to plain binary edges, we would lose the port semantics — exactly the lossy decomposition this proposition warns against.

### Proposition 2 — Bipartite Storage Bijection

The bipartite encoding $\Phi: G_H \to G_B$ is a **bijection**. A hypergraph can be losslessly stored as a bipartite ordinary graph where:

- **Entity nodes** represent the original vertices
- **Relation nodes** represent the hyperedges
- **Binary edges** connect each entity node to the relation nodes it participates in

This encoding preserves all n-ary structure and is fully invertible.

**mo:os relevance:** This validates the PostgreSQL storage strategy. The `wires` table with `(source_urn, source_port, target_urn, target_port)` is essentially a bipartite encoding: each wire connects two entities through a typed port relationship. The port-pair acts as the "relation node" in the bipartite encoding. Reconstruction of the full hyperedge is: group wires by port type and shared context → recover the n-ary relation.

### Proposition 3 — Retrieval Efficiency

Hypergraph retrieval achieves higher **information efficiency density**:

$$\eta = \frac{I(X; Y)}{\mathcal{L}}$$

where $I(X; Y)$ is mutual information between retrieved knowledge and the query, and $\mathcal{L}$ is the token length of the retrieved context. Hypergraph structure transmits more effective information per token than binary graph structure.

**mo:os relevance:** Extends the cost model (`foundations.md` §7, `architecture.md` §10). When the Embedding functor retrieves subgraph context for LLM operations, preserving hypergraph structure means higher information density per token — reducing the D (Discovery) cost dimension while increasing retrieval quality.

---

## Architecture Elements

### Knowledge Hypergraph Construction

1. **N-ary Relation Extraction**: LLM extracts relations connecting $n \geq 2$ entities from documents
2. **Bipartite Hypergraph Storage**: Maps hypergraph to bipartite ordinary graph for database storage
3. **Vector Representation Storage**: Embeds entity and hyperedge descriptions for retrieval

### Hypergraph Retrieval Strategy

1. **Entity retrieval**: Vector similarity → retrieve relevant entities
2. **Hyperedge retrieval**: Vector similarity → retrieve relevant relations
3. **Bidirectional expansion**: From entity → expand to connected hyperedges, and from hyperedge → expand to connected entities
4. **Knowledge fusion**: Merge expanded contexts into unified knowledge $K_H$

**mo:os relevance:** This bidirectional expansion maps to the coslice/slice traversal in `foundations.md` §5. Entity retrieval = slice category (fan-in), hyperedge retrieval = coslice category (fan-out). The fusion step is the colimit of the retrieved subdiagram.

### Hybrid RAG Generation

Final generation fuses hypergraph knowledge $K_H$ with chunk-based knowledge $K_{\text{chunk}}$:

$$\text{Answer} = \text{LLM}(Q, K_H \cup K_{\text{chunk}})$$

**mo:os relevance:** The LLM (Fuzzy Processing Unit) receives both graph-structured context (from the Embedding functor) and raw text chunks. This hybrid approach aligns with the System 3 architecture: the symbolic engine (kernel) provides structured knowledge, the LLM provides linguistic capability.

---

## Experimental Results (Key Takeaways)

- HyperGraphRAG outperforms GraphRAG, LightRAG, PathRAG, HippoRAG2 across medicine, agriculture, CS, legal domains
- Gains are largest on **multi-hop** and **comparison** queries — exactly the queries requiring n-ary relational reasoning
- Bipartite storage adds negligible overhead vs. binary triple storage
- Ablation confirms: removing hyperedge-level retrieval causes largest performance drop

---

## Concepts Promoted to mo:os Knowledge

| Concept | Promoted To | Section |
| --- | --- | --- |
| Binary decomposition is lossy (Proposition 1) | `foundations.md` §4 annotation | Validates hypergraph superposition |
| Bipartite storage bijection (Proposition 2) | `foundations.md` §4, `architecture.md` §1 | Validates wire table design |
| Information efficiency density $\eta$ | `architecture.md` §10 | Extends cost model |
| Bidirectional expansion ↔ coslice/slice | `foundations.md` §5 annotation | Validates traversal model |
| Hybrid RAG fusion (graph + chunks) | `foundations.md` §14 | Strengthens neuro-symbolic architecture |

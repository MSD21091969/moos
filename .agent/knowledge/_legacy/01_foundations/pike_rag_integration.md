# Pike RAG Integration

## Position in the Model

RAG (Retrieval-Augmented Generation) is a functor in the mo:os category:

```
Embedding : state_payload → ℝ¹⁵³⁶  (pgvector)
```

This maps container content from the graph domain into a continuous vector space
for approximate nearest-neighbor search. It is NOT a replacement for graph
traversal — it is a complementary discovery mechanism for cases where the user
does not know which node to start from.

## Relation to Graph Operations

| Concern      | Graph                     | Vector (RAG)                   |
| ------------ | ------------------------- | ------------------------------ |
| Lookup       | Exact: follow URN → wires | Approximate: cosine similarity |
| Composable   | Yes: traverse A→B→C       | No: vectors don't compose      |
| Schema-aware | Yes: port types on wires  | No: all content flattened      |
| Explainable  | Yes: path = proof         | No: embedding = opaque         |

RAG answers: "which nodes have content SIMILAR to X?"
Graph answers: "which nodes are CONNECTED to X through edges of type T?"

Both are useful. They should not be confused.

## Implementation

- `container_embeddings` table: `id BIGSERIAL, container_urn FK, embedding VECTOR(1536)`
- Embeddings are generated from `state_payload` via a provider-agnostic API
- HNSW index for fast approximate search
- Embedding generation is a MUTATE morphism on the container_embeddings table —
  it follows the same logging, the same permissions, the same four-operation model

## Separation Principle

Embeddings are a FUNCTOR OUTPUT, not graph metadata. The vector representation of
a node's content is derived data, stored in a separate table, and regenerated
whenever `state_payload` changes via MUTATE. This respects the principle:
functorial code (embedding generation) is separated from metadata (graph structure).
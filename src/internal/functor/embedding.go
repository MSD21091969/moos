package functor

import (
	"hash/fnv"
	"math"

	"moos/src/internal/cat"
)

// EmbeddingResult is the output of the Embedding functor (FUN03: F_embed: state_payload → R^1536).
type EmbeddingResult struct {
	URN    cat.URN   `json:"urn"`
	Vector []float64 `json:"vector"`
}

// Embedder maps a node's payload into a vector space.
type Embedder interface {
	Embed(node cat.Node) EmbeddingResult
}

// MockEmbedder returns a deterministic hash-based 1536-dim vector.
// No real model calls — pure mock.
type MockEmbedder struct{}

func (m MockEmbedder) Embed(node cat.Node) EmbeddingResult {
	vec := make([]float64, 1536)
	h := fnv.New64a()
	h.Write([]byte(node.URN))
	seed := h.Sum64()
	for i := range vec {
		// deterministic pseudo-random from URN hash
		seed ^= seed << 13
		seed ^= seed >> 7
		seed ^= seed << 17
		vec[i] = math.Float64frombits(seed)
		if math.IsNaN(vec[i]) || math.IsInf(vec[i], 0) {
			vec[i] = 0
		}
		// normalize to [-1, 1]
		vec[i] = (float64(seed%2000) - 1000.0) / 1000.0
	}
	return EmbeddingResult{URN: node.URN, Vector: vec}
}

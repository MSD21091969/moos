// Package functor defines read-path projections: F: C → D.
//
// Per the categorical specification (Step 9), functors are structure-preserving
// maps from the graph category C to codomain categories (React, R^1536, DAG, etc.).
// Functor outputs are NEVER ground truth (S4 invariant).
//
// In the MVP, all functors are mocked with deterministic implementations.
package functor

import "moos/internal/cat"

// Projector is the common interface for all functors F: C → D.
type Projector interface {
	Name() string
	Project(state cat.GraphState) (any, error)
}

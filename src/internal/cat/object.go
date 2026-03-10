// Package cat defines Category C — the typed graph model for mo:os.
//
// Objects (Ob(C)) are Nodes identified by URN, classified by Kind and Stratum.
// Morphisms (Hom(C)) are Wires connecting ports between Nodes.
// Composition is transitive wiring: if A→B and B→C then A→C via SQL-join or
// graph traversal (CAT01).
//
// This package contains ONLY value types: no IO, no side effects, no concurrency.
package cat

// URN is a universally unique resource name — the identity of an Object in C.
// Per AX1, every entity is a container identified by URN.
type URN string

// Kind classifies a Node. Corresponds to an Object type in the operad (OBJ01–OBJ13+).
type Kind string

// Port is a named connection point on a Node. Ports have direction (in/out)
// and admissible targets defined by the operad.
type Port string

// Stratum represents the hydration level of a Node (S0–S4).
// See doctrine/strata.md for the canonical layering model.
type Stratum string

const (
	S0 Stratum = "S0" // Authored — declared syntax, manifests, references
	S1 Stratum = "S1" // Validated — schema-checked, admissible for realization
	S2 Stratum = "S2" // Materialized — graph-ready programs and structures
	S3 Stratum = "S3" // Evaluated — contingent state after execution/replay
	S4 Stratum = "S4" // Projected — views, lenses, embeddings, metrics
)

// NormalizeStratum returns S2 (Materialized) for an empty stratum, otherwise the value as-is.
func NormalizeStratum(s Stratum) Stratum {
	if s == "" {
		return S2
	}
	return s
}

// ValidStratum reports whether s is one of the five canonical strata.
func ValidStratum(s Stratum) bool {
	switch s {
	case S0, S1, S2, S3, S4:
		return true
	}
	return false
}

// Node is an Object in Category C (CAT01).
//
// Per AX1: every entity is a container identified by URN. No metadata layer —
// only containers referencing containers via wires.
type Node struct {
	URN      URN            `json:"urn"`
	Kind     Kind           `json:"kind"`
	Stratum  Stratum        `json:"stratum"`
	Payload  map[string]any `json:"payload,omitempty"`
	Metadata map[string]any `json:"metadata,omitempty"`
	Version  int64          `json:"version"`
}

// Package cat defines the typed graph model for mo:os.
//
// Objects are Nodes identified by URN, classified by TypeID and Stratum.
// Morphisms are Wires connecting ports between Nodes.
//
// This package contains ONLY value types: no IO, no side effects, no concurrency.
package cat

// URN is a universally unique resource name — the identity of a Node.
type URN string

// TypeID classifies a Node. Foreign key into the ontology registry (type_id field).
type TypeID string

// Port is a named connection point on a Node. Ports have direction (in/out)
// and admissible targets defined by the operad.
type Port string

// Stratum represents the hydration level of a Node (S0–S4).
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

// Node is an Object in the typed graph — a vertex identified by URN.
type Node struct {
	URN      URN            `json:"urn"`
	TypeID   TypeID         `json:"type_id"`
	Stratum  Stratum        `json:"stratum"`
	Payload  map[string]any `json:"payload,omitempty"`
	Metadata map[string]any `json:"metadata,omitempty"`
	Version  int64          `json:"version"`
}

// Package operad implements the type system — the colored operad that defines
// which operations are legal on which Kinds.
//
// The operad declares:
//   - Kinds (colors) and their allowed strata
//   - Ports (arities) with direction (in/out) and admissible targets
//   - Validation functions for ADD, LINK, MUTATE operations
//
// This corresponds to the operad C in the categorical specification (Step 6/7):
// Colors = Kinds, Operations = morphisms, Arities = ports.
package operad

import (
	"moos/src/internal/cat"
)

// Registry is the semantic type system derived from ontology.json.
// It constrains which morphisms are admissible on the typed graph.
type Registry struct {
	Kinds map[cat.Kind]KindSpec `json:"kinds"`
}

// KindSpec defines a Kind's operad color: mutability, strata, and ports.
type KindSpec struct {
	Mutable       bool                  `json:"mutable"`
	AllowedStrata []cat.Stratum         `json:"allowed_strata"`
	Ports         map[cat.Port]PortSpec `json:"ports,omitempty"`
}

// PortSpec defines a port's direction and the set of admissible targets.
type PortSpec struct {
	Direction string       `json:"direction"` // "in" or "out"
	Targets   []PortTarget `json:"targets,omitempty"`
}

// PortTarget is an admissible (Kind, Port) pair for an outbound port.
type PortTarget struct {
	Kind cat.Kind `json:"kind"`
	Port cat.Port `json:"port"`
}

// Package operad implements the type system — the colored operad that defines
// which operations are legal on which Kinds.
//
// Colors = Kinds, Operations = morphisms, Arities = ports.
package operad

import (
	"moos/internal/cat"
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

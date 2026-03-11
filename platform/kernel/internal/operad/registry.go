// Package operad implements the type system — the colored operad that defines
// which operations are legal on which TypeIDs.
//
// Colors = TypeIDs, Operations = morphisms, Arities = ports.
package operad

import (
	"moos/platform/kernel/internal/cat"
)

// Registry is the semantic type system derived from ontology.json.
// It constrains which morphisms are admissible on the typed graph.
type Registry struct {
	Types map[cat.TypeID]TypeSpec `json:"types"`
}

// TypeSpec defines a TypeID's operad color: mutability, strata, and ports.
type TypeSpec struct {
	Mutable       bool                  `json:"mutable"`
	AllowedStrata []cat.Stratum         `json:"allowed_strata"`
	Ports         map[cat.Port]PortSpec `json:"ports,omitempty"`
}

// PortSpec defines a port's direction and the set of admissible targets.
type PortSpec struct {
	Direction string       `json:"direction"` // "in" or "out"
	Targets   []PortTarget `json:"targets,omitempty"`
}

// PortTarget is an admissible (TypeID, Port) pair for an outbound port.
type PortTarget struct {
	TypeID cat.TypeID `json:"type_id"`
	Port   cat.Port   `json:"port"`
}

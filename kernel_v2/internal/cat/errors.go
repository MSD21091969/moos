package cat

import "errors"

// Sentinel errors for the four invariant NTs and structural violations.
var (
	ErrInvalidEnvelope     = errors.New("invalid envelope")
	ErrInvalidProgram      = errors.New("invalid program")
	ErrUnsupportedMorphism = errors.New("unsupported morphism")
	ErrInvalidTypeID       = errors.New("invalid type_id")
	ErrInvalidPort         = errors.New("invalid port")
	ErrInvalidLink         = errors.New("invalid link")
	ErrImmutableType       = errors.New("immutable type")
	ErrNodeExists          = errors.New("node already exists")
	ErrNodeNotFound        = errors.New("node not found")
	ErrWireExists          = errors.New("wire already exists")
	ErrWireNotFound        = errors.New("wire not found")
	ErrVersionConflict     = errors.New("version conflict")
	ErrInvalidActor        = errors.New("actor is required")
	ErrInvalidStratum      = errors.New("invalid stratum")
	ErrMutationBlocked     = errors.New("mutation blocked for authored nodes")
)

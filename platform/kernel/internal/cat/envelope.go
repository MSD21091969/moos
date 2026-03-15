package cat

import "fmt"

// MorphismType identifies one of the four invariant Natural Transformations.
// All graph mutations are composed from these four primitives.
type MorphismType string

const (
	// ADD creates a new node (object) in graph state.
	ADD MorphismType = "ADD" // ∅ → Node: create a node
	// LINK creates a new wire (morphism) between existing nodes.
	LINK MorphismType = "LINK" // N × N → Wire: create a wire
	// MUTATE updates payload/metadata of an existing node.
	MUTATE MorphismType = "MUTATE" // N → N: update node payload (endomorphism)
	// UNLINK removes an existing wire from graph state.
	UNLINK MorphismType = "UNLINK" // Wire → ∅: remove a wire
)

// Envelope is an instantiation of one of the four Natural Transformations.
// It carries exactly one non-nil payload matching its Type.
type Envelope struct {
	Type   MorphismType   `json:"type"`
	Actor  URN            `json:"actor"`
	Scope  URN            `json:"scope,omitempty"`
	Add    *AddPayload    `json:"add,omitempty"`
	Link   *LinkPayload   `json:"link,omitempty"`
	Mutate *MutatePayload `json:"mutate,omitempty"`
	Unlink *UnlinkPayload `json:"unlink,omitempty"`
}

// Validate checks structural correctness of the envelope:
// - Actor is required
// - Exactly one payload is set, matching the declared Type
// - Required fields within the payload are present
func (e Envelope) Validate() error {
	if e.Actor == "" {
		return fmt.Errorf("%w: actor", ErrInvalidActor)
	}

	count := 0
	if e.Add != nil {
		count++
	}
	if e.Link != nil {
		count++
	}
	if e.Mutate != nil {
		count++
	}
	if e.Unlink != nil {
		count++
	}
	if count != 1 {
		return fmt.Errorf("%w: exactly one payload is required", ErrInvalidEnvelope)
	}

	switch e.Type {
	case ADD:
		if e.Add == nil || e.Add.URN == "" || e.Add.TypeID == "" {
			return fmt.Errorf("%w: add payload requires urn and type_id", ErrInvalidEnvelope)
		}
	case LINK:
		if e.Link == nil || e.Link.SourceURN == "" || e.Link.SourcePort == "" ||
			e.Link.TargetURN == "" || e.Link.TargetPort == "" {
			return fmt.Errorf("%w: link payload requires source and target ports", ErrInvalidEnvelope)
		}
	case MUTATE:
		if e.Mutate == nil || e.Mutate.URN == "" {
			return fmt.Errorf("%w: mutate payload requires urn", ErrInvalidEnvelope)
		}
	case UNLINK:
		if e.Unlink == nil || e.Unlink.SourceURN == "" || e.Unlink.SourcePort == "" ||
			e.Unlink.TargetURN == "" || e.Unlink.TargetPort == "" {
			return fmt.Errorf("%w: unlink payload requires source and target ports", ErrInvalidEnvelope)
		}
	default:
		return fmt.Errorf("%w: %s", ErrUnsupportedMorphism, e.Type)
	}

	return nil
}

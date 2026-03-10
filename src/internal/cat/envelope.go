package cat

import "fmt"

// MorphismType identifies one of the four invariant Natural Transformations.
// All graph mutations are composed from these four primitives (AX3).
type MorphismType string

const (
	ADD    MorphismType = "ADD"    // ∅ → Container: create a node (URN enters Ob(C))
	LINK   MorphismType = "LINK"   // C × C → Wire: create a wire (edge enters Hom(C))
	MUTATE MorphismType = "MUTATE" // C → C: update node payload (endomorphism)
	UNLINK MorphismType = "UNLINK" // Wire → ∅: remove a wire (edge leaves Hom(C))
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
		if e.Add == nil || e.Add.URN == "" || e.Add.Kind == "" {
			return fmt.Errorf("%w: add payload requires urn and kind", ErrInvalidEnvelope)
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

package core

import (
	"fmt"
)

func (envelope Envelope) Validate() error {
	if envelope.Actor == "" {
		return fmt.Errorf("%w: actor", ErrInvalidActor)
	}

	payloadCount := 0
	if envelope.Add != nil {
		payloadCount++
	}
	if envelope.Link != nil {
		payloadCount++
	}
	if envelope.Mutate != nil {
		payloadCount++
	}
	if envelope.Unlink != nil {
		payloadCount++
	}
	if payloadCount != 1 {
		return fmt.Errorf("%w: exactly one payload is required", ErrInvalidEnvelope)
	}

	switch envelope.Type {
	case MorphismAdd:
		if envelope.Add == nil || envelope.Add.URN == "" || envelope.Add.Kind == "" {
			return fmt.Errorf("%w: add payload requires urn and kind", ErrInvalidEnvelope)
		}
	case MorphismLink:
		if envelope.Link == nil || envelope.Link.SourceURN == "" || envelope.Link.SourcePort == "" || envelope.Link.TargetURN == "" || envelope.Link.TargetPort == "" {
			return fmt.Errorf("%w: link payload requires source and target ports", ErrInvalidEnvelope)
		}
	case MorphismMutate:
		if envelope.Mutate == nil || envelope.Mutate.URN == "" {
			return fmt.Errorf("%w: mutate payload requires urn", ErrInvalidEnvelope)
		}
	case MorphismUnlink:
		if envelope.Unlink == nil || envelope.Unlink.SourceURN == "" || envelope.Unlink.SourcePort == "" || envelope.Unlink.TargetURN == "" || envelope.Unlink.TargetPort == "" {
			return fmt.Errorf("%w: unlink payload requires source and target ports", ErrInvalidEnvelope)
		}
	default:
		return fmt.Errorf("%w: %s", ErrUnsupportedMorphism, envelope.Type)
	}

	return nil
}

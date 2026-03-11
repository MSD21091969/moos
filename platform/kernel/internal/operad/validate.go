package operad

import (
	"fmt"

	"moos/platform/kernel/internal/cat"
)

// Validate checks the Registry for internal consistency.
func (r *Registry) Validate() error {
	if r == nil {
		return nil
	}
	if len(r.Types) == 0 {
		return fmt.Errorf("%w: registry must contain at least one type", cat.ErrInvalidTypeID)
	}
	for typeID, spec := range r.Types {
		if typeID == "" {
			return fmt.Errorf("%w: type_id is required", cat.ErrInvalidTypeID)
		}
		if len(spec.AllowedStrata) == 0 {
			return fmt.Errorf("%w: type %s must declare allowed strata", cat.ErrInvalidTypeID, typeID)
		}
		for _, s := range spec.AllowedStrata {
			if !cat.ValidStratum(s) {
				return fmt.Errorf("%w: %s", cat.ErrInvalidStratum, s)
			}
		}
		for port, ps := range spec.Ports {
			if port == "" {
				return fmt.Errorf("%w: type %s contains an empty port id", cat.ErrInvalidPort, typeID)
			}
			if ps.Direction != "in" && ps.Direction != "out" {
				return fmt.Errorf("%w: type %s port %s must declare direction in|out", cat.ErrInvalidPort, typeID, port)
			}
			for _, tgt := range ps.Targets {
				if tgt.TypeID == "" || tgt.Port == "" {
					return fmt.Errorf("%w: type %s port %s has incomplete target", cat.ErrInvalidLink, typeID, port)
				}
			}
		}
	}
	return nil
}

// TypeOf looks up a TypeSpec. Returns an error if the type is not registered.
func (r *Registry) TypeOf(id cat.TypeID) (TypeSpec, error) {
	if r == nil {
		return TypeSpec{}, nil
	}
	spec, ok := r.Types[id]
	if !ok {
		return TypeSpec{}, fmt.Errorf("%w: %s", cat.ErrInvalidTypeID, id)
	}
	return spec, nil
}

// ValidateAdd checks whether an ADD payload is admissible under the operad constraints.
func (r *Registry) ValidateAdd(p *cat.AddPayload) error {
	if r == nil {
		return nil
	}
	stratum := cat.NormalizeStratum(p.Stratum)
	spec, err := r.TypeOf(p.TypeID)
	if err != nil {
		return err
	}
	for _, s := range spec.AllowedStrata {
		if s == stratum {
			return nil
		}
	}
	return fmt.Errorf("%w: type %s does not admit stratum %s", cat.ErrInvalidStratum, p.TypeID, stratum)
}

// ValidateMutate checks whether a node's type is mutable.
func (r *Registry) ValidateMutate(node cat.Node) error {
	if r == nil {
		return nil
	}
	spec, err := r.TypeOf(node.TypeID)
	if err != nil {
		return err
	}
	if !spec.Mutable {
		return fmt.Errorf("%w: type %s is immutable", cat.ErrImmutableType, node.TypeID)
	}
	return nil
}

// ValidateLink checks port existence, direction, and target admissibility.
func (r *Registry) ValidateLink(src, tgt cat.Node, p *cat.LinkPayload) error {
	if r == nil {
		return nil
	}
	srcType, err := r.TypeOf(src.TypeID)
	if err != nil {
		return err
	}
	tgtType, err := r.TypeOf(tgt.TypeID)
	if err != nil {
		return err
	}
	srcPort, ok := srcType.Ports[p.SourcePort]
	if !ok {
		return fmt.Errorf("%w: source type %s does not define port %s", cat.ErrInvalidPort, src.TypeID, p.SourcePort)
	}
	if srcPort.Direction != "out" {
		return fmt.Errorf("%w: source port %s on type %s is not outbound", cat.ErrInvalidLink, p.SourcePort, src.TypeID)
	}
	tgtPort, ok := tgtType.Ports[p.TargetPort]
	if !ok {
		return fmt.Errorf("%w: target type %s does not define port %s", cat.ErrInvalidPort, tgt.TypeID, p.TargetPort)
	}
	if tgtPort.Direction != "in" {
		return fmt.Errorf("%w: target port %s on type %s is not inbound", cat.ErrInvalidLink, p.TargetPort, tgt.TypeID)
	}
	for _, candidate := range srcPort.Targets {
		if candidate.TypeID == tgt.TypeID && candidate.Port == p.TargetPort {
			return nil
		}
	}
	return fmt.Errorf("%w: %s.%s cannot link to %s.%s",
		cat.ErrInvalidLink, src.TypeID, p.SourcePort, tgt.TypeID, p.TargetPort)
}

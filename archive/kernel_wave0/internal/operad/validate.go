package operad

import (
	"fmt"

	"moos/internal/cat"
)

// Validate checks the Registry for internal consistency.
func (r *Registry) Validate() error {
	if r == nil {
		return nil
	}
	if len(r.Kinds) == 0 {
		return fmt.Errorf("%w: registry must contain at least one kind", cat.ErrInvalidKind)
	}
	for kind, spec := range r.Kinds {
		if kind == "" {
			return fmt.Errorf("%w: kind id is required", cat.ErrInvalidKind)
		}
		if len(spec.AllowedStrata) == 0 {
			return fmt.Errorf("%w: kind %s must declare allowed strata", cat.ErrInvalidKind, kind)
		}
		for _, s := range spec.AllowedStrata {
			if !cat.ValidStratum(s) {
				return fmt.Errorf("%w: %s", cat.ErrInvalidStratum, s)
			}
		}
		for port, ps := range spec.Ports {
			if port == "" {
				return fmt.Errorf("%w: kind %s contains an empty port id", cat.ErrInvalidPort, kind)
			}
			if ps.Direction != "in" && ps.Direction != "out" {
				return fmt.Errorf("%w: kind %s port %s must declare direction in|out", cat.ErrInvalidPort, kind, port)
			}
			for _, tgt := range ps.Targets {
				if tgt.Kind == "" || tgt.Port == "" {
					return fmt.Errorf("%w: kind %s port %s has incomplete target", cat.ErrInvalidLink, kind, port)
				}
			}
		}
	}
	return nil
}

// Kind looks up a KindSpec. Returns an error if the kind is not registered.
func (r *Registry) Kind(k cat.Kind) (KindSpec, error) {
	if r == nil {
		return KindSpec{}, nil
	}
	spec, ok := r.Kinds[k]
	if !ok {
		return KindSpec{}, fmt.Errorf("%w: %s", cat.ErrInvalidKind, k)
	}
	return spec, nil
}

// ValidateAdd checks whether an ADD payload is admissible under the operad constraints.
func (r *Registry) ValidateAdd(p *cat.AddPayload) error {
	if r == nil {
		return nil
	}
	stratum := cat.NormalizeStratum(p.Stratum)
	spec, err := r.Kind(p.Kind)
	if err != nil {
		return err
	}
	for _, s := range spec.AllowedStrata {
		if s == stratum {
			return nil
		}
	}
	return fmt.Errorf("%w: kind %s does not admit stratum %s", cat.ErrInvalidStratum, p.Kind, stratum)
}

// ValidateMutate checks whether a node's kind is mutable.
func (r *Registry) ValidateMutate(node cat.Node) error {
	if r == nil {
		return nil
	}
	spec, err := r.Kind(node.Kind)
	if err != nil {
		return err
	}
	if !spec.Mutable {
		return fmt.Errorf("%w: kind %s is immutable", cat.ErrImmutableKind, node.Kind)
	}
	return nil
}

// ValidateLink checks port existence, direction, and target admissibility.
func (r *Registry) ValidateLink(src, tgt cat.Node, p *cat.LinkPayload) error {
	if r == nil {
		return nil
	}
	srcKind, err := r.Kind(src.Kind)
	if err != nil {
		return err
	}
	tgtKind, err := r.Kind(tgt.Kind)
	if err != nil {
		return err
	}
	srcPort, ok := srcKind.Ports[p.SourcePort]
	if !ok {
		return fmt.Errorf("%w: source kind %s does not define port %s", cat.ErrInvalidPort, src.Kind, p.SourcePort)
	}
	if srcPort.Direction != "out" {
		return fmt.Errorf("%w: source port %s on kind %s is not outbound", cat.ErrInvalidLink, p.SourcePort, src.Kind)
	}
	tgtPort, ok := tgtKind.Ports[p.TargetPort]
	if !ok {
		return fmt.Errorf("%w: target kind %s does not define port %s", cat.ErrInvalidPort, tgt.Kind, p.TargetPort)
	}
	if tgtPort.Direction != "in" {
		return fmt.Errorf("%w: target port %s on kind %s is not inbound", cat.ErrInvalidLink, p.TargetPort, tgt.Kind)
	}
	for _, candidate := range srcPort.Targets {
		if candidate.Kind == tgt.Kind && candidate.Port == p.TargetPort {
			return nil
		}
	}
	return fmt.Errorf("%w: %s.%s cannot link to %s.%s",
		cat.ErrInvalidLink, src.Kind, p.SourcePort, tgt.Kind, p.TargetPort)
}

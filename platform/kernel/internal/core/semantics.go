package core

import "fmt"

type SemanticRegistry struct {
	Kinds map[Kind]KindSpec `json:"kinds"`
}

type KindSpec struct {
	Mutable       bool              `json:"mutable"`
	AllowedStrata []Stratum         `json:"allowed_strata"`
	Ports         map[Port]PortSpec `json:"ports,omitempty"`
}

type PortSpec struct {
	Direction string       `json:"direction"`
	Targets   []PortTarget `json:"targets,omitempty"`
}

type PortTarget struct {
	Kind Kind `json:"kind"`
	Port Port `json:"port"`
}

func (registry *SemanticRegistry) Validate() error {
	if registry == nil {
		return nil
	}
	if len(registry.Kinds) == 0 {
		return fmt.Errorf("%w: registry must contain at least one kind", ErrInvalidKind)
	}
	for kind, spec := range registry.Kinds {
		if kind == "" {
			return fmt.Errorf("%w: kind id is required", ErrInvalidKind)
		}
		if len(spec.AllowedStrata) == 0 {
			return fmt.Errorf("%w: kind %s must declare allowed strata", ErrInvalidKind, kind)
		}
		for _, stratum := range spec.AllowedStrata {
			if !isValidStratum(stratum) {
				return fmt.Errorf("%w: %s", ErrInvalidStratum, stratum)
			}
		}
		for port, portSpec := range spec.Ports {
			if port == "" {
				return fmt.Errorf("%w: kind %s contains an empty port id", ErrInvalidPort, kind)
			}
			if portSpec.Direction != "in" && portSpec.Direction != "out" {
				return fmt.Errorf("%w: kind %s port %s must declare direction in|out", ErrInvalidPort, kind, port)
			}
			for _, target := range portSpec.Targets {
				if target.Kind == "" || target.Port == "" {
					return fmt.Errorf("%w: kind %s port %s has incomplete target", ErrInvalidLink, kind, port)
				}
			}
		}
	}
	return nil
}

func (registry *SemanticRegistry) Kind(kind Kind) (KindSpec, error) {
	if registry == nil {
		return KindSpec{}, nil
	}
	spec, ok := registry.Kinds[kind]
	if !ok {
		return KindSpec{}, fmt.Errorf("%w: %s", ErrInvalidKind, kind)
	}
	return spec, nil
}

func (registry *SemanticRegistry) ValidateAdd(payload *AddPayload) error {
	if registry == nil {
		return nil
	}
	stratum := NormalizeStratum(payload.Stratum)
	spec, err := registry.Kind(payload.Kind)
	if err != nil {
		return err
	}
	for _, allowed := range spec.AllowedStrata {
		if allowed == stratum {
			return nil
		}
	}
	return fmt.Errorf("%w: kind %s does not admit stratum %s", ErrInvalidStratum, payload.Kind, stratum)
}

func (registry *SemanticRegistry) ValidateMutate(node Node) error {
	if registry == nil {
		return nil
	}
	spec, err := registry.Kind(node.Kind)
	if err != nil {
		return err
	}
	if !spec.Mutable {
		return fmt.Errorf("%w: kind %s is immutable", ErrImmutableKind, node.Kind)
	}
	return nil
}

func (registry *SemanticRegistry) ValidateLink(source Node, target Node, payload *LinkPayload) error {
	if registry == nil {
		return nil
	}
	sourceKind, err := registry.Kind(source.Kind)
	if err != nil {
		return err
	}
	targetKind, err := registry.Kind(target.Kind)
	if err != nil {
		return err
	}
	sourcePort, ok := sourceKind.Ports[payload.SourcePort]
	if !ok {
		return fmt.Errorf("%w: source kind %s does not define port %s", ErrInvalidPort, source.Kind, payload.SourcePort)
	}
	if sourcePort.Direction != "out" {
		return fmt.Errorf("%w: source port %s on kind %s is not outbound", ErrInvalidLink, payload.SourcePort, source.Kind)
	}
	targetPort, ok := targetKind.Ports[payload.TargetPort]
	if !ok {
		return fmt.Errorf("%w: target kind %s does not define port %s", ErrInvalidPort, target.Kind, payload.TargetPort)
	}
	if targetPort.Direction != "in" {
		return fmt.Errorf("%w: target port %s on kind %s is not inbound", ErrInvalidLink, payload.TargetPort, target.Kind)
	}
	for _, candidate := range sourcePort.Targets {
		if candidate.Kind == target.Kind && candidate.Port == payload.TargetPort {
			return nil
		}
	}
	return fmt.Errorf("%w: %s.%s cannot link to %s.%s", ErrInvalidLink, source.Kind, payload.SourcePort, target.Kind, payload.TargetPort)
}

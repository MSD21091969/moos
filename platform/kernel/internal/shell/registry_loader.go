package shell

import (
	"encoding/json"
	"fmt"
	"os"
	"regexp"
	"sort"
	"strings"

	"moos/platform/kernel/internal/core"
)

var quotedPortPattern = regexp.MustCompile(`'([^']+)'`)

type ontologyRegistry struct {
	Objects   []ontologyObject   `json:"objects"`
	Morphisms []ontologyMorphism `json:"morphisms"`
}

type ontologyObject struct {
	Name              string   `json:"name"`
	BroadCategory     string   `json:"broad_category"`
	SourceConnections []string `json:"source_connections"`
	TargetConnections []string `json:"target_connections"`
}

type ontologyMorphism struct {
	Name          string `json:"name"`
	Decomposition string `json:"decomposition"`
}

func LoadRegistry(path string) (*core.SemanticRegistry, error) {
	content, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}

	var probe struct {
		Kinds     map[string]json.RawMessage `json:"kinds"`
		Objects   []json.RawMessage          `json:"objects"`
		Morphisms []json.RawMessage          `json:"morphisms"`
	}
	if err := json.Unmarshal(content, &probe); err != nil {
		return nil, err
	}

	var registry core.SemanticRegistry
	switch {
	case len(probe.Kinds) > 0:
		if err := json.Unmarshal(content, &registry); err != nil {
			return nil, err
		}
	case len(probe.Objects) > 0 && len(probe.Morphisms) > 0:
		var ontology ontologyRegistry
		if err := json.Unmarshal(content, &ontology); err != nil {
			return nil, err
		}
		registry = deriveRegistryFromOntology(ontology)
	default:
		return nil, fmt.Errorf("unsupported registry format: %s", path)
	}

	if err := registry.Validate(); err != nil {
		return nil, fmt.Errorf("invalid semantic registry: %w", err)
	}
	return &registry, nil
}

func deriveRegistryFromOntology(ontology ontologyRegistry) core.SemanticRegistry {
	morphismsByName := make(map[string]ontologyMorphism, len(ontology.Morphisms))
	for _, morphism := range ontology.Morphisms {
		morphismsByName[morphism.Name] = morphism
	}

	registry := core.SemanticRegistry{Kinds: map[core.Kind]core.KindSpec{}}
	for _, object := range ontology.Objects {
		registry.Kinds[core.Kind(object.Name)] = deriveKindSpec(object)
	}
	addCompatibilityKinds(&registry)

	for _, object := range ontology.Objects {
		kindName := core.Kind(object.Name)
		spec := registry.Kinds[kindName]
		for _, connection := range object.SourceConnections {
			morphism, ok := morphismsByName[connection]
			if !ok {
				continue
			}
			sourcePort, targetPort, ok := derivePorts(connection, morphism.Decomposition)
			if !ok {
				continue
			}
			portSpec := spec.Ports[sourcePort]
			if portSpec.Direction == "" {
				portSpec.Direction = "out"
			}
			for _, candidate := range ontology.Objects {
				if !contains(candidate.TargetConnections, connection) {
					continue
				}
				portSpec.Targets = appendUniqueTarget(portSpec.Targets, core.PortTarget{Kind: core.Kind(candidate.Name), Port: targetPort})
			}
			spec.Ports[sourcePort] = normalizePortSpec(portSpec)
		}
		for _, connection := range object.TargetConnections {
			morphism, ok := morphismsByName[connection]
			if !ok {
				continue
			}
			_, targetPort, ok := derivePorts(connection, morphism.Decomposition)
			if !ok {
				continue
			}
			portSpec := spec.Ports[targetPort]
			if portSpec.Direction == "" {
				portSpec.Direction = "in"
			}
			spec.Ports[targetPort] = normalizePortSpec(portSpec)
		}
		registry.Kinds[kindName] = spec
	}

	bridgeCompatibilityKinds(&registry)
	return registry
}

func deriveKindSpec(object ontologyObject) core.KindSpec {
	mutable := object.Name != "UI_Lens"
	allowedStrata := []core.Stratum{core.StratumMaterialized, core.StratumEvaluated}
	if object.Name == "UI_Lens" {
		mutable = false
		allowedStrata = []core.Stratum{core.StratumProjected}
	}
	return core.KindSpec{
		Mutable:       mutable,
		AllowedStrata: allowedStrata,
		Ports:         map[core.Port]core.PortSpec{},
	}
}

func addCompatibilityKinds(registry *core.SemanticRegistry) {
	registry.Kinds["Node"] = core.KindSpec{
		Mutable:       true,
		AllowedStrata: []core.Stratum{core.StratumMaterialized, core.StratumEvaluated},
		Ports:         map[core.Port]core.PortSpec{},
	}
	registry.Kinds["Projection"] = core.KindSpec{
		Mutable:       false,
		AllowedStrata: []core.Stratum{core.StratumProjected},
		Ports:         map[core.Port]core.PortSpec{},
	}
}

func bridgeCompatibilityKinds(registry *core.SemanticRegistry) {
	if nodeContainer, ok := registry.Kinds["NodeContainer"]; ok {
		registry.Kinds["Node"] = cloneKindSpec(nodeContainer)
		if port, exists := registry.Kinds["Node"].Ports["out"]; exists {
			port.Targets = appendUniqueTarget(port.Targets, core.PortTarget{Kind: "Node", Port: "in"})
			registry.Kinds["Node"].Ports["out"] = normalizePortSpec(port)
		}
		if _, exists := registry.Kinds["Node"].Ports["out"]; !exists {
			registry.Kinds["Node"].Ports["out"] = core.PortSpec{Direction: "out", Targets: []core.PortTarget{{Kind: "Node", Port: "in"}}}
		}
		if _, exists := registry.Kinds["Node"].Ports["in"]; !exists {
			registry.Kinds["Node"].Ports["in"] = core.PortSpec{Direction: "in"}
		}
	}
	if uiLens, ok := registry.Kinds["UI_Lens"]; ok {
		registry.Kinds["Projection"] = cloneKindSpec(uiLens)
	}
	for kind, spec := range registry.Kinds {
		for port, portSpec := range spec.Ports {
			spec.Ports[port] = normalizePortSpec(portSpec)
		}
		registry.Kinds[kind] = spec
	}
}

func cloneKindSpec(spec core.KindSpec) core.KindSpec {
	clone := core.KindSpec{
		Mutable:       spec.Mutable,
		AllowedStrata: append([]core.Stratum(nil), spec.AllowedStrata...),
		Ports:         make(map[core.Port]core.PortSpec, len(spec.Ports)),
	}
	for port, portSpec := range spec.Ports {
		clone.Ports[port] = normalizePortSpec(core.PortSpec{
			Direction: portSpec.Direction,
			Targets:   append([]core.PortTarget(nil), portSpec.Targets...),
		})
	}
	return clone
}

func derivePorts(connection string, decomposition string) (core.Port, core.Port, bool) {
	quoted := quotedPortPattern.FindAllStringSubmatch(decomposition, -1)
	if len(quoted) >= 2 {
		return core.Port(quoted[0][1]), core.Port(quoted[1][1]), true
	}
	if strings.EqualFold(connection, "LINK_NODES") {
		return "out", "in", true
	}
	return "", "", false
}

func appendUniqueTarget(targets []core.PortTarget, target core.PortTarget) []core.PortTarget {
	for _, existing := range targets {
		if existing.Kind == target.Kind && existing.Port == target.Port {
			return targets
		}
	}
	return append(targets, target)
}

func normalizePortSpec(spec core.PortSpec) core.PortSpec {
	if len(spec.Targets) == 0 {
		return spec
	}
	sort.Slice(spec.Targets, func(left int, right int) bool {
		leftKey := string(spec.Targets[left].Kind) + ":" + string(spec.Targets[left].Port)
		rightKey := string(spec.Targets[right].Kind) + ":" + string(spec.Targets[right].Port)
		return leftKey < rightKey
	})
	return spec
}

func contains(values []string, expected string) bool {
	for _, value := range values {
		if value == expected {
			return true
		}
	}
	return false
}

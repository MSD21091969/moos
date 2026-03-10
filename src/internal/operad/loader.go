package operad

import (
	"encoding/json"
	"fmt"
	"os"
	"regexp"
	"sort"
	"strings"

	"moos/src/internal/cat"
)

var quotedPortPattern = regexp.MustCompile(`'([^']+)'`)

// ontology types for parsing ontology.json
type ontologyFile struct {
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

// LoadRegistry reads a registry from disk. It auto-detects format:
//   - Direct KindSpec format (has "kinds" key)
//   - Ontology format (has "objects" + "morphisms") → derives registry
func LoadRegistry(path string) (*Registry, error) {
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

	var registry Registry
	switch {
	case len(probe.Kinds) > 0:
		if err := json.Unmarshal(content, &registry); err != nil {
			return nil, err
		}
	case len(probe.Objects) > 0 && len(probe.Morphisms) > 0:
		var ont ontologyFile
		if err := json.Unmarshal(content, &ont); err != nil {
			return nil, err
		}
		registry = DeriveFromOntology(ont)
	default:
		return nil, fmt.Errorf("unsupported registry format: %s", path)
	}

	if err := registry.Validate(); err != nil {
		return nil, fmt.Errorf("invalid semantic registry: %w", err)
	}
	return &registry, nil
}

// DeriveFromOntology builds a Registry from the ontology objects and morphisms.
// This replaces the old deriveRegistryFromOntology function with the same logic,
// but now also registers Kind=Kernel and Kind=Feature (fixing F1).
func DeriveFromOntology(ont ontologyFile) Registry {
	morphByName := make(map[string]ontologyMorphism, len(ont.Morphisms))
	for _, m := range ont.Morphisms {
		morphByName[m.Name] = m
	}

	reg := Registry{Kinds: map[cat.Kind]KindSpec{}}

	// Derive kinds from ontology objects
	for _, obj := range ont.Objects {
		reg.Kinds[cat.Kind(obj.Name)] = deriveKindSpec(obj)
	}

	// FIX F1: Ensure Kernel and Feature are always present
	if _, ok := reg.Kinds["Kernel"]; !ok {
		reg.Kinds["Kernel"] = KindSpec{
			Mutable:       true,
			AllowedStrata: []cat.Stratum{cat.S2, cat.S3},
			Ports: map[cat.Port]PortSpec{
				"implements":   {Direction: "in"},
				"exposes":      {Direction: "in"},
				"can_schedule": {Direction: "out"},
				"can_federate": {Direction: "out"},
			},
		}
	}
	if _, ok := reg.Kinds["Feature"]; !ok {
		reg.Kinds["Feature"] = KindSpec{
			Mutable:       true,
			AllowedStrata: []cat.Stratum{cat.S2, cat.S3},
			Ports: map[cat.Port]PortSpec{
				"implements": {Direction: "out"},
			},
		}
	}

	// Add compatibility Kinds
	addCompatibilityKinds(&reg)

	// Wire up ports from ontology connections
	for _, obj := range ont.Objects {
		kindName := cat.Kind(obj.Name)
		spec := reg.Kinds[kindName]

		for _, conn := range obj.SourceConnections {
			morph, ok := morphByName[conn]
			if !ok {
				continue
			}
			sp, tp, ok := derivePorts(conn, morph.Decomposition)
			if !ok {
				continue
			}
			ps := spec.Ports[sp]
			if ps.Direction == "" {
				ps.Direction = "out"
			}
			for _, cand := range ont.Objects {
				if !strSliceContains(cand.TargetConnections, conn) {
					continue
				}
				ps.Targets = appendUniqueTarget(ps.Targets, PortTarget{Kind: cat.Kind(cand.Name), Port: tp})
			}
			spec.Ports[sp] = normalizePortSpec(ps)
		}

		for _, conn := range obj.TargetConnections {
			morph, ok := morphByName[conn]
			if !ok {
				continue
			}
			_, tp, ok := derivePorts(conn, morph.Decomposition)
			if !ok {
				continue
			}
			ps := spec.Ports[tp]
			if ps.Direction == "" {
				ps.Direction = "in"
			}
			spec.Ports[tp] = normalizePortSpec(ps)
		}
		reg.Kinds[kindName] = spec
	}

	// Wire up Kernel ↔ Feature port targets
	wireKernelFeature(&reg)

	bridgeCompatibilityKinds(&reg)
	return reg
}

func wireKernelFeature(reg *Registry) {
	if kernel, ok := reg.Kinds["Kernel"]; ok {
		ps := kernel.Ports["implements"]
		ps.Targets = appendUniqueTarget(ps.Targets, PortTarget{Kind: "Feature", Port: "implements"})
		kernel.Ports["implements"] = normalizePortSpec(ps)
		reg.Kinds["Kernel"] = kernel
	}
	if feat, ok := reg.Kinds["Feature"]; ok {
		ps := feat.Ports["implements"]
		ps.Targets = appendUniqueTarget(ps.Targets, PortTarget{Kind: "Kernel", Port: "implements"})
		feat.Ports["implements"] = normalizePortSpec(ps)
		reg.Kinds["Feature"] = feat
	}
}

func deriveKindSpec(obj ontologyObject) KindSpec {
	mutable := obj.Name != "UI_Lens"
	strata := []cat.Stratum{cat.S2, cat.S3}
	if obj.Name == "UI_Lens" {
		mutable = false
		strata = []cat.Stratum{cat.S4}
	}
	return KindSpec{
		Mutable:       mutable,
		AllowedStrata: strata,
		Ports:         map[cat.Port]PortSpec{},
	}
}

func addCompatibilityKinds(reg *Registry) {
	reg.Kinds["Node"] = KindSpec{
		Mutable:       true,
		AllowedStrata: []cat.Stratum{cat.S2, cat.S3},
		Ports:         map[cat.Port]PortSpec{},
	}
	reg.Kinds["Projection"] = KindSpec{
		Mutable:       false,
		AllowedStrata: []cat.Stratum{cat.S4},
		Ports:         map[cat.Port]PortSpec{},
	}
}

func bridgeCompatibilityKinds(reg *Registry) {
	if nc, ok := reg.Kinds["NodeContainer"]; ok {
		reg.Kinds["Node"] = cloneKindSpec(nc)
		ps := reg.Kinds["Node"].Ports["out"]
		ps.Targets = appendUniqueTarget(ps.Targets, PortTarget{Kind: "Node", Port: "in"})
		reg.Kinds["Node"].Ports["out"] = normalizePortSpec(ps)
		if _, exists := reg.Kinds["Node"].Ports["in"]; !exists {
			reg.Kinds["Node"].Ports["in"] = PortSpec{Direction: "in"}
		}
	}
	if ul, ok := reg.Kinds["UI_Lens"]; ok {
		reg.Kinds["Projection"] = cloneKindSpec(ul)
	}
	for kind, spec := range reg.Kinds {
		for port, ps := range spec.Ports {
			spec.Ports[port] = normalizePortSpec(ps)
		}
		reg.Kinds[kind] = spec
	}
}

func cloneKindSpec(spec KindSpec) KindSpec {
	c := KindSpec{
		Mutable:       spec.Mutable,
		AllowedStrata: append([]cat.Stratum(nil), spec.AllowedStrata...),
		Ports:         make(map[cat.Port]PortSpec, len(spec.Ports)),
	}
	for port, ps := range spec.Ports {
		c.Ports[port] = normalizePortSpec(PortSpec{
			Direction: ps.Direction,
			Targets:   append([]PortTarget(nil), ps.Targets...),
		})
	}
	return c
}

func derivePorts(connection string, decomposition string) (cat.Port, cat.Port, bool) {
	quoted := quotedPortPattern.FindAllStringSubmatch(decomposition, -1)
	if len(quoted) >= 2 {
		return cat.Port(quoted[0][1]), cat.Port(quoted[1][1]), true
	}
	if strings.EqualFold(connection, "LINK_NODES") {
		return "out", "in", true
	}
	return "", "", false
}

func appendUniqueTarget(targets []PortTarget, t PortTarget) []PortTarget {
	for _, existing := range targets {
		if existing.Kind == t.Kind && existing.Port == t.Port {
			return targets
		}
	}
	return append(targets, t)
}

func normalizePortSpec(ps PortSpec) PortSpec {
	if len(ps.Targets) == 0 {
		return ps
	}
	sort.Slice(ps.Targets, func(i, j int) bool {
		ki := string(ps.Targets[i].Kind) + ":" + string(ps.Targets[i].Port)
		kj := string(ps.Targets[j].Kind) + ":" + string(ps.Targets[j].Port)
		return ki < kj
	})
	return ps
}

func strSliceContains(ss []string, s string) bool {
	for _, v := range ss {
		if v == s {
			return true
		}
	}
	return false
}

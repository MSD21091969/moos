package operad

import (
	"encoding/json"
	"fmt"
	"regexp"
	"sort"
	"strings"

	"moos/kernel_v2/internal/cat"
)

var quotedPortPattern = regexp.MustCompile(`'([^']+)'`)

// ontology types for parsing ontology.json
type ontologyFile struct {
	Objects   []ontologyObject   `json:"objects"`
	Morphisms []ontologyMorphism `json:"morphisms"`
}

type ontologyObject struct {
	Name              string `json:"name"`
	TypeID            string `json:"type_id"`
	BroadCategory     string `json:"broad_category"`
	SourceConnections []string `json:"source_connections"`
	TargetConnections []string `json:"target_connections"`
}

type ontologyMorphism struct {
	Name          string `json:"name"`
	Decomposition string `json:"decomposition"`
}

// LoadRegistry parses a registry from raw JSON bytes. It auto-detects format:
//   - Direct TypeSpec format (has "types" key)
//   - Ontology format (has "objects" + "morphisms") → derives registry
func LoadRegistry(data []byte) (*Registry, error) {
	var probe struct {
		Types     map[string]json.RawMessage `json:"types"`
		Objects   []json.RawMessage          `json:"objects"`
		Morphisms []json.RawMessage          `json:"morphisms"`
	}
	if err := json.Unmarshal(data, &probe); err != nil {
		return nil, err
	}

	var registry Registry
	switch {
	case len(probe.Types) > 0:
		if err := json.Unmarshal(data, &registry); err != nil {
			return nil, err
		}
	case len(probe.Objects) > 0 && len(probe.Morphisms) > 0:
		var ont ontologyFile
		if err := json.Unmarshal(data, &ont); err != nil {
			return nil, err
		}
		registry = DeriveFromOntology(ont)
	default:
		return nil, fmt.Errorf("unsupported registry format")
	}

	if err := registry.Validate(); err != nil {
		return nil, fmt.Errorf("invalid semantic registry: %w", err)
	}
	return &registry, nil
}

// DeriveFromOntology builds a Registry from the ontology objects and morphisms.
// Uses type_id as the registry key (not name).
func DeriveFromOntology(ont ontologyFile) Registry {
	morphByName := make(map[string]ontologyMorphism, len(ont.Morphisms))
	for _, m := range ont.Morphisms {
		morphByName[m.Name] = m
	}

	// Map from object name to type_id for lookups
	nameToTypeID := make(map[string]cat.TypeID, len(ont.Objects))
	for _, obj := range ont.Objects {
		nameToTypeID[obj.Name] = cat.TypeID(obj.TypeID)
	}

	reg := Registry{Types: map[cat.TypeID]TypeSpec{}}

	for _, obj := range ont.Objects {
		tid := cat.TypeID(obj.TypeID)
		reg.Types[tid] = deriveTypeSpec(obj)
	}

	for _, obj := range ont.Objects {
		tid := cat.TypeID(obj.TypeID)
		spec := reg.Types[tid]

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
				candTID := cat.TypeID(cand.TypeID)
				ps.Targets = appendUniqueTarget(ps.Targets, PortTarget{TypeID: candTID, Port: tp})
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
		reg.Types[tid] = spec
	}

	return reg
}

func deriveTypeSpec(obj ontologyObject) TypeSpec {
	mutable := obj.TypeID != "ui_lens"
	strata := []cat.Stratum{cat.S2, cat.S3}
	if obj.TypeID == "ui_lens" {
		mutable = false
		strata = []cat.Stratum{cat.S4}
	}
	return TypeSpec{
		Mutable:       mutable,
		AllowedStrata: strata,
		Ports:         map[cat.Port]PortSpec{},
	}
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
		if existing.TypeID == t.TypeID && existing.Port == t.Port {
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
		ki := string(ps.Targets[i].TypeID) + ":" + string(ps.Targets[i].Port)
		kj := string(ps.Targets[j].TypeID) + ":" + string(ps.Targets[j].Port)
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

package operad_test

import (
	"encoding/json"
	"errors"
	"testing"

	"moos/platform/kernel/internal/cat"
	"moos/platform/kernel/internal/operad"
)

func minimalRegistry() *operad.Registry {
	return &operad.Registry{
		Types: map[cat.TypeID]operad.TypeSpec{
			"node_container": {
				Mutable:       true,
				AllowedStrata: []cat.Stratum{cat.S2, cat.S3},
				Ports: map[cat.Port]operad.PortSpec{
					"out": {Direction: "out", Targets: []operad.PortTarget{{TypeID: "node_container", Port: "in"}}},
					"in":  {Direction: "in"},
				},
			},
			"ui_lens": {
				Mutable:       false,
				AllowedStrata: []cat.Stratum{cat.S4},
				Ports:         map[cat.Port]operad.PortSpec{},
			},
		},
	}
}

func TestRegistryValidate(t *testing.T) {
	reg := minimalRegistry()
	if err := reg.Validate(); err != nil {
		t.Errorf("valid registry should pass: %v", err)
	}
}

func TestRegistryValidate_Empty(t *testing.T) {
	reg := &operad.Registry{Types: map[cat.TypeID]operad.TypeSpec{}}
	if err := reg.Validate(); err == nil {
		t.Error("empty registry should fail validation")
	}
}

func TestValidateAdd_Admissible(t *testing.T) {
	reg := minimalRegistry()
	err := reg.ValidateAdd(&cat.AddPayload{URN: "urn:x", TypeID: "node_container", Stratum: cat.S2})
	if err != nil {
		t.Errorf("admissible ADD should pass: %v", err)
	}
}

func TestValidateAdd_WrongStratum(t *testing.T) {
	reg := minimalRegistry()
	err := reg.ValidateAdd(&cat.AddPayload{URN: "urn:x", TypeID: "ui_lens", Stratum: cat.S2})
	if !errors.Is(err, cat.ErrInvalidStratum) {
		t.Errorf("expected ErrInvalidStratum, got %v", err)
	}
}

func TestValidateMutate_Immutable(t *testing.T) {
	reg := minimalRegistry()
	err := reg.ValidateMutate(cat.Node{URN: "urn:x", TypeID: "ui_lens", Stratum: cat.S4, Version: 1})
	if !errors.Is(err, cat.ErrImmutableType) {
		t.Errorf("expected ErrImmutableType, got %v", err)
	}
}

func TestValidateLink_Valid(t *testing.T) {
	reg := minimalRegistry()
	src := cat.Node{URN: "urn:a", TypeID: "node_container", Stratum: cat.S2}
	tgt := cat.Node{URN: "urn:b", TypeID: "node_container", Stratum: cat.S2}
	err := reg.ValidateLink(src, tgt, &cat.LinkPayload{
		SourceURN: "urn:a", SourcePort: "out",
		TargetURN: "urn:b", TargetPort: "in",
	})
	if err != nil {
		t.Errorf("valid link should pass: %v", err)
	}
}

func TestValidateLink_BadPort(t *testing.T) {
	reg := minimalRegistry()
	src := cat.Node{URN: "urn:a", TypeID: "node_container", Stratum: cat.S2}
	tgt := cat.Node{URN: "urn:b", TypeID: "node_container", Stratum: cat.S2}
	err := reg.ValidateLink(src, tgt, &cat.LinkPayload{
		SourceURN: "urn:a", SourcePort: "nonexistent",
		TargetURN: "urn:b", TargetPort: "in",
	})
	if !errors.Is(err, cat.ErrInvalidPort) {
		t.Errorf("expected ErrInvalidPort, got %v", err)
	}
}

func TestLoadRegistry_OntologyFormat(t *testing.T) {
	ontology := map[string]any{
		"objects": []map[string]any{
			{
				"name": "NodeContainer", "type_id": "node_container",
				"broad_category":     "structure",
				"source_connections": []string{"LINK_NODES"},
				"target_connections": []string{"LINK_NODES"},
			},
		},
		"morphisms": []map[string]any{
			{"name": "LINK_NODES", "decomposition": "LINK(source, port_s, target, port_t)"},
		},
	}
	data, _ := json.Marshal(ontology)
	reg, err := operad.LoadRegistry(data)
	if err != nil {
		t.Fatalf("LoadRegistry failed: %v", err)
	}
	if _, ok := reg.Types["node_container"]; !ok {
		t.Error("expected node_container type in registry")
	}
}

func TestLoadRegistry_DirectFormat(t *testing.T) {
	reg := minimalRegistry()
	data, _ := json.Marshal(reg)
	loaded, err := operad.LoadRegistry(data)
	if err != nil {
		t.Fatalf("LoadRegistry failed: %v", err)
	}
	if len(loaded.Types) != 2 {
		t.Errorf("expected 2 types, got %d", len(loaded.Types))
	}
}

func TestLoadRegistry_OntologyIndustryEntity(t *testing.T) {
	ontology := map[string]any{
		"objects": []map[string]any{
			{
				"name":               "IndustryEntity",
				"type_id":            "industry_entity",
				"allowed_strata":     []string{"S0"},
				"source_connections": []string{"CLASSIFIES"},
				"target_connections": []string{"OWNS"},
			},
			{
				"name":               "Provider",
				"type_id":            "provider",
				"allowed_strata":     []string{"S2", "S3"},
				"source_connections": []string{"OWNS"},
				"target_connections": []string{"OWNS"},
			},
		},
		"morphisms": []map[string]any{
			{
				"name":          "CLASSIFIES",
				"decomposition": "LINK(industry_node, 'classifies', instance_node, 'source')",
				"target":        "any",
			},
		},
	}

	data, _ := json.Marshal(ontology)
	reg, err := operad.LoadRegistry(data)
	if err != nil {
		t.Fatalf("LoadRegistry failed: %v", err)
	}

	industry, ok := reg.Types["industry_entity"]
	if !ok {
		t.Fatal("industry_entity type missing")
	}
	if len(industry.AllowedStrata) != 1 || industry.AllowedStrata[0] != cat.S0 {
		t.Fatalf("industry_entity strata = %v, want [S0]", industry.AllowedStrata)
	}
	classifies, ok := industry.Ports["classifies"]
	if !ok {
		t.Fatal("industry_entity classifies port missing")
	}
	if classifies.Direction != "out" {
		t.Fatalf("classifies direction = %q, want out", classifies.Direction)
	}
	if len(classifies.Targets) == 0 {
		t.Fatal("classifies should derive at least one admissible target when morphism target is any")
	}
}

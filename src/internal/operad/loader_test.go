package operad

import (
	"path/filepath"
	"runtime"
	"testing"

	"moos/src/internal/cat"
)

func repoRoot() string {
	_, file, _, _ := runtime.Caller(0)
	// src/internal/operad/loader_test.go → 3 levels up to moos/
	return filepath.Join(filepath.Dir(file), "..", "..", "..")
}

func TestLoadRegistryFromOntology(t *testing.T) {
	root := repoRoot()
	path := filepath.Join(root, ".agent", "knowledge_base", "registry", "ontology.json")

	reg, err := LoadRegistry(path)
	if err != nil {
		t.Fatalf("LoadRegistry: %v", err)
	}

	// Must have at least the 13 ontology Kinds + Kernel + Feature + Node + Projection
	if len(reg.Kinds) < 13 {
		t.Fatalf("expected ≥13 kinds, got %d", len(reg.Kinds))
	}

	// FIX F1 regression: Kernel and Feature MUST be present
	for _, required := range []cat.Kind{"Kernel", "Feature"} {
		if _, ok := reg.Kinds[required]; !ok {
			t.Errorf("kind %s not found in derived registry", required)
		}
	}

	// Verify Kernel has implements/in port
	kernel := reg.Kinds["Kernel"]
	p, ok := kernel.Ports["implements"]
	if !ok {
		t.Fatal("Kernel missing implements port")
	}
	if p.Direction != "in" {
		t.Errorf("Kernel.implements direction = %s, want in", p.Direction)
	}

	// Verify Feature has implements/out port
	feat := reg.Kinds["Feature"]
	fp, ok := feat.Ports["implements"]
	if !ok {
		t.Fatal("Feature missing implements port")
	}
	if fp.Direction != "out" {
		t.Errorf("Feature.implements direction = %s, want out", fp.Direction)
	}

	// Verify NodeContainer derived with ports
	nc, ok := reg.Kinds["NodeContainer"]
	if !ok {
		t.Fatal("NodeContainer not derived")
	}
	if !nc.Mutable {
		t.Error("NodeContainer should be mutable")
	}
}

func TestRegistryValidateAdd(t *testing.T) {
	reg := &Registry{
		Kinds: map[cat.Kind]KindSpec{
			"TestKind": {Mutable: true, AllowedStrata: []cat.Stratum{cat.S2}, Ports: map[cat.Port]PortSpec{}},
		},
	}

	// valid
	if err := reg.ValidateAdd(&cat.AddPayload{URN: "urn:x", Kind: "TestKind", Stratum: cat.S2}); err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	// invalid kind
	if err := reg.ValidateAdd(&cat.AddPayload{URN: "urn:y", Kind: "Bogus", Stratum: cat.S2}); err == nil {
		t.Fatal("expected error for unknown kind")
	}

	// invalid stratum
	if err := reg.ValidateAdd(&cat.AddPayload{URN: "urn:z", Kind: "TestKind", Stratum: cat.S4}); err == nil {
		t.Fatal("expected error for disallowed stratum")
	}
}

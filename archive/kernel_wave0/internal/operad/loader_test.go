package operad

import (
	"os"
	"path/filepath"
	"runtime"
	"testing"

	"moos/internal/cat"
)

func repoRoot() string {
	_, file, _, _ := runtime.Caller(0)
	// kernel/internal/operad/loader_test.go → 3 levels up to moos/
	return filepath.Join(filepath.Dir(file), "..", "..", "..")
}

func TestLoadRegistryFromOntology(t *testing.T) {
	root := repoRoot()
	path := filepath.Join(root, "kernel", "registry", "ontology.json")

	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("ReadFile: %v", err)
	}
	reg, err := LoadRegistry(data)
	if err != nil {
		t.Fatalf("LoadRegistry: %v", err)
	}

	// Must have at least the 13 ontology Kinds plus compatibility Node/Projection.
	if len(reg.Kinds) < 13 {
		t.Fatalf("expected ≥13 kinds, got %d", len(reg.Kinds))
	}

	for _, required := range []cat.Kind{"NodeContainer", "ProtocolAdapter", "Node", "Projection"} {
		if _, ok := reg.Kinds[required]; !ok {
			t.Errorf("kind %s not found in derived registry", required)
		}
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
	if err := reg.ValidateAdd(&cat.AddPayload{URN: "urn:y", Kind: "NoSuch", Stratum: cat.S2}); err == nil {
		t.Fatal("expected error for unknown kind")
	}

	// invalid stratum
	if err := reg.ValidateAdd(&cat.AddPayload{URN: "urn:z", Kind: "TestKind", Stratum: cat.S4}); err == nil {
		t.Fatal("expected error for disallowed stratum")
	}
}

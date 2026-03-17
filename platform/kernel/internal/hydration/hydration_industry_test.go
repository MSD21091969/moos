package hydration_test

import (
	"os"
	"path/filepath"
	"testing"

	"moos/platform/kernel/internal/cat"
	"moos/platform/kernel/internal/hydration"
	"moos/platform/kernel/internal/shell"
)

func TestHydrateAll_IndustryEntities(t *testing.T) {
	kbRoot := t.TempDir()
	mustMkdir(t, filepath.Join(kbRoot, "superset"))
	mustMkdir(t, filepath.Join(kbRoot, "instances"))
	mustMkdir(t, filepath.Join(kbRoot, "industry"))

	writeJSON(t, filepath.Join(kbRoot, "superset", "ontology.json"), `{
  "objects": [
    {"id": "OBJ01"},
    {"id": "OBJ22"}
  ],
  "categories": {
    "core": [],
    "stratum_chain": [],
    "hydration_pipeline": [],
    "functor_codomains": [],
    "cross_provider": [],
    "glossary": []
  }
}`)

	writeJSON(t, filepath.Join(kbRoot, "superset", "sources.json"), `{
  "entries": [
    {"id": "urn:moos:source:anthropic-docs", "domain": "providers"}
  ]
}`)

	writeJSON(t, filepath.Join(kbRoot, "instances", "providers.json"), `{
  "domain": "providers",
  "entries": [
    {
      "id": "urn:moos:provider:anthropic",
      "type_id": "provider",
      "name": "Anthropic"
    }
  ]
}`)

	writeJSON(t, filepath.Join(kbRoot, "industry", "providers.json"), `{
  "domain": "providers",
  "source": "urn:moos:source:anthropic-docs",
  "entries": [
    {"id": "ind:provider:anthropic", "name": "Anthropic"}
  ]
}`)

	store := shell.NewMemStore()
	rt, err := shell.NewRuntime(store, nil)
	if err != nil {
		t.Fatalf("NewRuntime: %v", err)
	}

	if err := rt.SeedIfAbsent(cat.Envelope{
		Type:  cat.ADD,
		Actor: "urn:moos:identity:test",
		Add: &cat.AddPayload{
			URN:    "urn:moos:kernel:wave-0",
			TypeID: "node_container",
		},
	}); err != nil {
		t.Fatalf("seed root: %v", err)
	}
	if err := rt.SeedIfAbsent(cat.Envelope{
		Type:  cat.ADD,
		Actor: "urn:moos:identity:test",
		Add: &cat.AddPayload{
			URN:    "urn:moos:source:anthropic-docs",
			TypeID: "node_container",
		},
	}); err != nil {
		t.Fatalf("seed source: %v", err)
	}

	if err := hydration.HydrateAll(kbRoot, "urn:moos:kernel:wave-0", rt); err != nil {
		t.Fatalf("HydrateAll: %v", err)
	}

	industryURN := cat.URN("urn:moos:industry:providers:ind-provider-anthropic")
	node, ok := rt.Node(industryURN)
	if !ok {
		t.Fatalf("missing industry node %s", industryURN)
	}
	if node.TypeID != "industry_entity" {
		t.Fatalf("industry type_id = %s, want industry_entity", node.TypeID)
	}
	if node.Stratum != cat.S0 {
		t.Fatalf("industry stratum = %s, want S0", node.Stratum)
	}

	classifiesKey := cat.WireKey(industryURN, "classifies", "urn:moos:provider:anthropic", "source")
	if _, ok := rt.Wires()[classifiesKey]; !ok {
		t.Fatalf("missing classifies wire %s", classifiesKey)
	}
}

func mustMkdir(t *testing.T, path string) {
	t.Helper()
	if err := os.MkdirAll(path, 0o755); err != nil {
		t.Fatalf("mkdir %s: %v", path, err)
	}
}

func writeJSON(t *testing.T, path, content string) {
	t.Helper()
	if err := os.WriteFile(path, []byte(content), 0o600); err != nil {
		t.Fatalf("write %s: %v", path, err)
	}
}

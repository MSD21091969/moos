package main

import (
	"os"
	"path/filepath"
	"testing"

	"moos/platform/kernel/internal/cat"
	"moos/platform/kernel/internal/shell"
)

func TestSeedSourceNodes(t *testing.T) {
	kbRoot := t.TempDir()
	superset := filepath.Join(kbRoot, "superset")
	if err := os.MkdirAll(superset, 0o755); err != nil {
		t.Fatalf("mkdir: %v", err)
	}

	const sources = `{
  "entries": [
    {
      "id": "urn:moos:source:anthropic-docs",
      "label": "Anthropic API Docs",
      "domain": "providers",
      "url": "https://docs.anthropic.com"
    }
  ]
}`
	if err := os.WriteFile(filepath.Join(superset, "sources.json"), []byte(sources), 0o600); err != nil {
		t.Fatalf("write sources: %v", err)
	}

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

	seedSourceNodes(rt, kbRoot, "urn:moos:kernel:wave-0")

	if _, ok := rt.Node("urn:moos:source:anthropic-docs"); !ok {
		t.Fatal("expected source node to be seeded")
	}

	wireKey := cat.WireKey("urn:moos:kernel:wave-0", "owns", "urn:moos:source:anthropic-docs", "child")
	if _, ok := rt.Wires()[wireKey]; !ok {
		t.Fatal("expected root->source OWNS wire")
	}
}

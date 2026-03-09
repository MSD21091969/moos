package shell

import (
	"path/filepath"
	"testing"

	"moos/platform/kernel/internal/core"
)

func TestLoadRegistryDerivesKindsFromOntology(t *testing.T) {
	registry, err := LoadRegistry(filepath.Join("..", "..", "..", "..", ".agent", "knowledge_base", "superset", "ontology.json"))
	if err != nil {
		t.Fatalf("load registry failed: %v", err)
	}

	nodeContainer, ok := registry.Kinds[core.Kind("NodeContainer")]
	if !ok {
		t.Fatal("expected NodeContainer kind in derived registry")
	}
	if len(nodeContainer.AllowedStrata) == 0 {
		t.Fatal("expected NodeContainer to declare allowed strata")
	}
	if port, ok := nodeContainer.Ports[core.Port("out")]; !ok || port.Direction != "out" {
		t.Fatalf("expected NodeContainer out port, got %+v", nodeContainer.Ports)
	}

	compatibilityNode, ok := registry.Kinds[core.Kind("Node")]
	if !ok {
		t.Fatal("expected compatibility Node kind in derived registry")
	}
	if port, ok := compatibilityNode.Ports[core.Port("out")]; !ok || len(port.Targets) == 0 {
		t.Fatalf("expected compatibility Node out targets, got %+v", compatibilityNode.Ports)
	}

	uiLens, ok := registry.Kinds[core.Kind("UI_Lens")]
	if !ok {
		t.Fatal("expected UI_Lens kind in derived registry")
	}
	if len(uiLens.AllowedStrata) != 1 || uiLens.AllowedStrata[0] != core.StratumProjected {
		t.Fatalf("expected UI_Lens projected stratum, got %+v", uiLens.AllowedStrata)
	}
	if uiLens.Mutable {
		t.Fatal("expected UI_Lens to be immutable")
	}

	tool, ok := registry.Kinds[core.Kind("SystemTool")]
	if !ok {
		t.Fatal("expected SystemTool kind in derived registry")
	}
	if port, ok := tool.Ports[core.Port("transport")]; !ok || port.Direction != "in" {
		t.Fatalf("expected SystemTool transport port, got %+v", tool.Ports)
	}
}

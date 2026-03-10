package functor

import (
	"testing"

	"moos/src/internal/cat"
)

func TestMockUILens(t *testing.T) {
	state := cat.NewGraphState()
	state.Nodes["urn:a"] = cat.Node{URN: "urn:a", Kind: "Node", Stratum: cat.S2, Version: 1}
	state.Nodes["urn:b"] = cat.Node{URN: "urn:b", Kind: "Node", Stratum: cat.S2, Version: 1}
	state.Wires[cat.WireKey("urn:a", "out", "urn:b", "in")] = cat.Wire{
		SourceURN: "urn:a", SourcePort: "out", TargetURN: "urn:b", TargetPort: "in",
	}

	lens := MockUILens{}
	proj := lens.ProjectUI(state)
	if len(proj.Nodes) != 2 {
		t.Fatalf("expected 2 UI nodes, got %d", len(proj.Nodes))
	}
	if len(proj.Edges) != 1 {
		t.Fatalf("expected 1 UI edge, got %d", len(proj.Edges))
	}
}

func TestMockEmbedder(t *testing.T) {
	node := cat.Node{URN: "urn:test", Kind: "Node", Stratum: cat.S2, Version: 1}
	emb := MockEmbedder{}
	result := emb.Embed(node)
	if len(result.Vector) != 1536 {
		t.Fatalf("expected 1536-dim vector, got %d", len(result.Vector))
	}
	if result.URN != "urn:test" {
		t.Fatalf("expected URN urn:test, got %s", result.URN)
	}
	// Determinism: same input → same output
	result2 := emb.Embed(node)
	for i := range result.Vector {
		if result.Vector[i] != result2.Vector[i] {
			t.Fatal("embedder is not deterministic")
		}
	}
}

func TestMockStructureMap(t *testing.T) {
	state := cat.NewGraphState()
	state.Nodes["urn:c"] = cat.Node{URN: "urn:c", Kind: "Node", Version: 1}
	state.Nodes["urn:a"] = cat.Node{URN: "urn:a", Kind: "Node", Version: 1}
	state.Nodes["urn:b"] = cat.Node{URN: "urn:b", Kind: "Node", Version: 1}

	sm := MockStructureMap{}
	dag := sm.Analyze(state)
	if len(dag.TopologicalOrder) != 3 {
		t.Fatalf("expected 3 in topo order, got %d", len(dag.TopologicalOrder))
	}
	if dag.TopologicalOrder[0] != "urn:a" {
		t.Fatalf("expected urn:a first (sorted), got %s", dag.TopologicalOrder[0])
	}
}

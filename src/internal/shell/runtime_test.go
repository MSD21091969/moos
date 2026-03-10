package shell

import (
	"testing"

	"moos/src/internal/cat"
)

func TestRuntimeApplyAndQuery(t *testing.T) {
	store := NewMemStore()
	rt, err := NewRuntime(store, nil)
	if err != nil {
		t.Fatal(err)
	}

	// ADD a node
	env := cat.Envelope{
		Type:  cat.ADD,
		Actor: "urn:test:actor",
		Add:   &cat.AddPayload{URN: "urn:test:node", Kind: "TestKind", Stratum: cat.S2},
	}
	result, err := rt.Apply(env)
	if err != nil {
		t.Fatalf("Apply ADD: %v", err)
	}
	if result.Node == nil {
		t.Fatal("expected non-nil node in result")
	}

	// Query
	node, ok := rt.Node("urn:test:node")
	if !ok {
		t.Fatal("node not found after ADD")
	}
	if node.Kind != "TestKind" {
		t.Fatalf("expected TestKind, got %s", node.Kind)
	}
	if len(rt.Nodes()) != 1 {
		t.Fatalf("expected 1 node, got %d", len(rt.Nodes()))
	}
}

func TestRuntimeSeedIfAbsent(t *testing.T) {
	store := NewMemStore()
	rt, err := NewRuntime(store, nil)
	if err != nil {
		t.Fatal(err)
	}

	env := cat.Envelope{
		Type:  cat.ADD,
		Actor: "urn:test:actor",
		Add:   &cat.AddPayload{URN: "urn:seed:x", Kind: "TestKind", Stratum: cat.S2},
	}

	// First seed: creates
	if err := rt.SeedIfAbsent(env); err != nil {
		t.Fatalf("first seed failed: %v", err)
	}
	// Second seed: idempotent (absorbs ErrNodeExists)
	if err := rt.SeedIfAbsent(env); err != nil {
		t.Fatalf("second seed should be idempotent: %v", err)
	}

	if len(rt.Nodes()) != 1 {
		t.Fatalf("expected 1 node after double seed, got %d", len(rt.Nodes()))
	}
}

func TestRuntimeReplayOnRestart(t *testing.T) {
	store := NewMemStore()
	rt, err := NewRuntime(store, nil)
	if err != nil {
		t.Fatal(err)
	}

	// Seed some morphisms
	if err := rt.SeedIfAbsent(cat.Envelope{
		Type: cat.ADD, Actor: "urn:actor",
		Add: &cat.AddPayload{URN: "urn:a", Kind: "K", Stratum: cat.S2},
	}); err != nil {
		t.Fatal(err)
	}
	if err := rt.SeedIfAbsent(cat.Envelope{
		Type: cat.ADD, Actor: "urn:actor",
		Add: &cat.AddPayload{URN: "urn:b", Kind: "K", Stratum: cat.S2},
	}); err != nil {
		t.Fatal(err)
	}

	// Create a new runtime from the same store — simulates restart
	rt2, err := NewRuntime(store, nil)
	if err != nil {
		t.Fatal(err)
	}

	if len(rt2.Nodes()) != 2 {
		t.Fatalf("expected 2 nodes after replay, got %d", len(rt2.Nodes()))
	}
	if rt2.LogLen() != 2 {
		t.Fatalf("expected 2 log entries, got %d", rt2.LogLen())
	}
}

func TestRuntimeApplyProgram(t *testing.T) {
	store := NewMemStore()
	rt, err := NewRuntime(store, nil)
	if err != nil {
		t.Fatal(err)
	}

	prog := cat.Program{
		Actor: "urn:actor",
		Envelopes: []cat.Envelope{
			{Type: cat.ADD, Add: &cat.AddPayload{URN: "urn:p1", Kind: "K", Stratum: cat.S2}},
			{Type: cat.ADD, Add: &cat.AddPayload{URN: "urn:p2", Kind: "K", Stratum: cat.S2}},
			{Type: cat.LINK, Link: &cat.LinkPayload{
				SourceURN: "urn:p1", SourcePort: "out",
				TargetURN: "urn:p2", TargetPort: "in",
			}},
		},
	}

	result, err := rt.ApplyProgram(prog)
	if err != nil {
		t.Fatalf("ApplyProgram: %v", err)
	}
	if len(result.Results) != 3 {
		t.Fatalf("expected 3 results, got %d", len(result.Results))
	}
	if len(rt.Nodes()) != 2 {
		t.Fatalf("expected 2 nodes, got %d", len(rt.Nodes()))
	}
	if len(rt.Wires()) != 1 {
		t.Fatalf("expected 1 wire, got %d", len(rt.Wires()))
	}
}

func TestRuntimeWireQueries(t *testing.T) {
	store := NewMemStore()
	rt, err := NewRuntime(store, nil)
	if err != nil {
		t.Fatal(err)
	}

	prog := cat.Program{
		Actor: "urn:actor",
		Envelopes: []cat.Envelope{
			{Type: cat.ADD, Add: &cat.AddPayload{URN: "urn:src", Kind: "K", Stratum: cat.S2}},
			{Type: cat.ADD, Add: &cat.AddPayload{URN: "urn:tgt", Kind: "K", Stratum: cat.S2}},
			{Type: cat.LINK, Link: &cat.LinkPayload{
				SourceURN: "urn:src", SourcePort: "out",
				TargetURN: "urn:tgt", TargetPort: "in",
			}},
		},
	}
	if _, err := rt.ApplyProgram(prog); err != nil {
		t.Fatal(err)
	}

	out := rt.OutgoingWires("urn:src")
	if len(out) != 1 {
		t.Fatalf("expected 1 outgoing wire, got %d", len(out))
	}
	in := rt.IncomingWires("urn:tgt")
	if len(in) != 1 {
		t.Fatalf("expected 1 incoming wire, got %d", len(in))
	}
	if len(rt.OutgoingWires("urn:tgt")) != 0 {
		t.Fatal("urn:tgt should have no outgoing wires")
	}
}

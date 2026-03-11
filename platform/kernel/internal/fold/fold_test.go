package fold_test

import (
	"errors"
	"testing"
	"time"

	"moos/platform/kernel/internal/cat"
	"moos/platform/kernel/internal/fold"
)

var testActor = cat.URN("urn:moos:identity:test-actor")
var now = time.Date(2026, 3, 11, 0, 0, 0, 0, time.UTC)

func addEnvelope(urn cat.URN, typeID cat.TypeID) cat.Envelope {
	return cat.Envelope{
		Type:  cat.ADD,
		Actor: testActor,
		Add:   &cat.AddPayload{URN: urn, TypeID: typeID},
	}
}

func linkEnvelope(srcURN cat.URN, srcPort cat.Port, tgtURN cat.URN, tgtPort cat.Port) cat.Envelope {
	return cat.Envelope{
		Type:  cat.LINK,
		Actor: testActor,
		Link:  &cat.LinkPayload{SourceURN: srcURN, SourcePort: srcPort, TargetURN: tgtURN, TargetPort: tgtPort},
	}
}

func TestEvaluate_ADD(t *testing.T) {
	state := cat.NewGraphState()
	result, err := fold.Evaluate(state, addEnvelope("urn:a", "node_container"), now)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(result.State.Nodes) != 1 {
		t.Fatalf("expected 1 node, got %d", len(result.State.Nodes))
	}
	node := result.State.Nodes["urn:a"]
	if node.TypeID != "node_container" {
		t.Errorf("TypeID = %q, want node_container", node.TypeID)
	}
	if node.Version != 1 {
		t.Errorf("Version = %d, want 1", node.Version)
	}
	if node.Stratum != cat.S2 {
		t.Errorf("Stratum = %q, want S2", node.Stratum)
	}
}

func TestEvaluate_ADD_Duplicate(t *testing.T) {
	state := cat.NewGraphState()
	result, _ := fold.Evaluate(state, addEnvelope("urn:a", "node_container"), now)
	_, err := fold.Evaluate(result.State, addEnvelope("urn:a", "node_container"), now)
	if !errors.Is(err, cat.ErrNodeExists) {
		t.Errorf("expected ErrNodeExists, got %v", err)
	}
}

func TestEvaluate_LINK(t *testing.T) {
	state := cat.NewGraphState()
	r1, _ := fold.Evaluate(state, addEnvelope("urn:a", "node_container"), now)
	r2, _ := fold.Evaluate(r1.State, addEnvelope("urn:b", "node_container"), now)
	r3, err := fold.Evaluate(r2.State, linkEnvelope("urn:a", "out", "urn:b", "in"), now)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(r3.State.Wires) != 1 {
		t.Fatalf("expected 1 wire, got %d", len(r3.State.Wires))
	}
}

func TestEvaluate_LINK_MissingNode(t *testing.T) {
	state := cat.NewGraphState()
	r1, _ := fold.Evaluate(state, addEnvelope("urn:a", "node_container"), now)
	_, err := fold.Evaluate(r1.State, linkEnvelope("urn:a", "out", "urn:missing", "in"), now)
	if !errors.Is(err, cat.ErrNodeNotFound) {
		t.Errorf("expected ErrNodeNotFound, got %v", err)
	}
}

func TestEvaluate_MUTATE(t *testing.T) {
	state := cat.NewGraphState()
	r1, _ := fold.Evaluate(state, addEnvelope("urn:a", "node_container"), now)

	env := cat.Envelope{
		Type:  cat.MUTATE,
		Actor: testActor,
		Mutate: &cat.MutatePayload{
			URN:             "urn:a",
			ExpectedVersion: 1,
			Payload:         map[string]any{"updated": true},
		},
	}
	r2, err := fold.Evaluate(r1.State, env, now)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	node := r2.State.Nodes["urn:a"]
	if node.Version != 2 {
		t.Errorf("Version = %d, want 2", node.Version)
	}
	if node.Payload["updated"] != true {
		t.Error("Payload not updated")
	}
}

func TestEvaluate_MUTATE_VersionConflict(t *testing.T) {
	state := cat.NewGraphState()
	r1, _ := fold.Evaluate(state, addEnvelope("urn:a", "node_container"), now)

	env := cat.Envelope{
		Type:   cat.MUTATE,
		Actor:  testActor,
		Mutate: &cat.MutatePayload{URN: "urn:a", ExpectedVersion: 99},
	}
	_, err := fold.Evaluate(r1.State, env, now)
	if !errors.Is(err, cat.ErrVersionConflict) {
		t.Errorf("expected ErrVersionConflict, got %v", err)
	}
}

func TestEvaluate_UNLINK(t *testing.T) {
	state := cat.NewGraphState()
	r1, _ := fold.Evaluate(state, addEnvelope("urn:a", "node_container"), now)
	r2, _ := fold.Evaluate(r1.State, addEnvelope("urn:b", "node_container"), now)
	r3, _ := fold.Evaluate(r2.State, linkEnvelope("urn:a", "out", "urn:b", "in"), now)

	env := cat.Envelope{
		Type:  cat.UNLINK,
		Actor: testActor,
		Unlink: &cat.UnlinkPayload{
			SourceURN: "urn:a", SourcePort: "out",
			TargetURN: "urn:b", TargetPort: "in",
		},
	}
	r4, err := fold.Evaluate(r3.State, env, now)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(r4.State.Wires) != 0 {
		t.Errorf("expected 0 wires after unlink, got %d", len(r4.State.Wires))
	}
}

func TestEvaluateProgram(t *testing.T) {
	prog := cat.Program{
		Actor: testActor,
		Envelopes: []cat.Envelope{
			{Type: cat.ADD, Add: &cat.AddPayload{URN: "urn:a", TypeID: "node_container"}},
			{Type: cat.ADD, Add: &cat.AddPayload{URN: "urn:b", TypeID: "node_container"}},
			{Type: cat.LINK, Link: &cat.LinkPayload{SourceURN: "urn:a", SourcePort: "out", TargetURN: "urn:b", TargetPort: "in"}},
		},
	}
	state := cat.NewGraphState()
	result, err := fold.EvaluateProgram(state, prog, now)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(result.State.Nodes) != 2 {
		t.Errorf("expected 2 nodes, got %d", len(result.State.Nodes))
	}
	if len(result.State.Wires) != 1 {
		t.Errorf("expected 1 wire, got %d", len(result.State.Wires))
	}
	if len(result.Persisted) != 3 {
		t.Errorf("expected 3 persisted entries, got %d", len(result.Persisted))
	}
}

func TestReplay(t *testing.T) {
	// Build a small log manually
	entries := []cat.PersistedEnvelope{
		{Envelope: addEnvelope("urn:x", "node_container"), IssuedAt: now},
		{Envelope: addEnvelope("urn:y", "node_container"), IssuedAt: now.Add(time.Second)},
		{Envelope: linkEnvelope("urn:x", "out", "urn:y", "in"), IssuedAt: now.Add(2 * time.Second)},
	}
	state, err := fold.Replay(entries)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(state.Nodes) != 2 {
		t.Errorf("expected 2 nodes, got %d", len(state.Nodes))
	}
	if len(state.Wires) != 1 {
		t.Errorf("expected 1 wire, got %d", len(state.Wires))
	}
}

func TestEvaluate_Purity(t *testing.T) {
	// Verify that fold never mutates the input state
	state := cat.NewGraphState()
	state.Nodes["urn:pre"] = cat.Node{URN: "urn:pre", TypeID: "node_container", Stratum: cat.S2, Version: 1}

	_, err := fold.Evaluate(state, addEnvelope("urn:new", "node_container"), now)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(state.Nodes) != 1 {
		t.Error("fold mutated the input state")
	}
	if _, ok := state.Nodes["urn:new"]; ok {
		t.Error("new node leaked into input state")
	}
}

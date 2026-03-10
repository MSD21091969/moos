package fold

import (
	"testing"
	"time"

	"moos/src/internal/cat"
)

var testTime = time.Date(2026, 3, 10, 0, 0, 0, 0, time.UTC)
var actor = cat.URN("urn:moos:kernel:self")

func TestEvaluateAddLinkMutateUnlink(t *testing.T) {
	state := cat.NewGraphState()

	// ADD node A
	result, err := Evaluate(state, cat.Envelope{
		Type:  cat.ADD,
		Actor: actor,
		Add:   &cat.AddPayload{URN: "urn:a", Kind: "Node", Stratum: cat.S2},
	}, testTime)
	if err != nil {
		t.Fatalf("ADD a: %v", err)
	}
	if result.Node == nil || result.Node.URN != "urn:a" {
		t.Fatal("ADD a: missing node in result")
	}
	state = result.State

	// ADD node B
	result, err = Evaluate(state, cat.Envelope{
		Type:  cat.ADD,
		Actor: actor,
		Add:   &cat.AddPayload{URN: "urn:b", Kind: "Node", Stratum: cat.S2},
	}, testTime)
	if err != nil {
		t.Fatalf("ADD b: %v", err)
	}
	state = result.State

	// LINK A → B
	result, err = Evaluate(state, cat.Envelope{
		Type:  cat.LINK,
		Actor: actor,
		Link:  &cat.LinkPayload{SourceURN: "urn:a", SourcePort: "out", TargetURN: "urn:b", TargetPort: "in"},
	}, testTime)
	if err != nil {
		t.Fatalf("LINK: %v", err)
	}
	if result.Wire == nil {
		t.Fatal("LINK: missing wire in result")
	}
	state = result.State
	if len(state.Wires) != 1 {
		t.Fatalf("expected 1 wire, got %d", len(state.Wires))
	}

	// MUTATE A
	result, err = Evaluate(state, cat.Envelope{
		Type:   cat.MUTATE,
		Actor:  actor,
		Mutate: &cat.MutatePayload{URN: "urn:a", ExpectedVersion: 1, Payload: map[string]any{"k": "v"}},
	}, testTime)
	if err != nil {
		t.Fatalf("MUTATE: %v", err)
	}
	if result.Node.Version != 2 {
		t.Fatalf("expected version 2, got %d", result.Node.Version)
	}
	state = result.State

	// UNLINK A → B
	result, err = Evaluate(state, cat.Envelope{
		Type:   cat.UNLINK,
		Actor:  actor,
		Unlink: &cat.UnlinkPayload{SourceURN: "urn:a", SourcePort: "out", TargetURN: "urn:b", TargetPort: "in"},
	}, testTime)
	if err != nil {
		t.Fatalf("UNLINK: %v", err)
	}
	state = result.State
	if len(state.Wires) != 0 {
		t.Fatalf("expected 0 wires after UNLINK, got %d", len(state.Wires))
	}
}

func TestEvaluateRejectsDuplicateNode(t *testing.T) {
	state := cat.NewGraphState()
	env := cat.Envelope{Type: cat.ADD, Actor: actor, Add: &cat.AddPayload{URN: "urn:dup", Kind: "Node", Stratum: cat.S2}}

	result, err := Evaluate(state, env, testTime)
	if err != nil {
		t.Fatal(err)
	}
	_, err = Evaluate(result.State, env, testTime)
	if err == nil {
		t.Fatal("expected ErrNodeExists")
	}
}

func TestEvaluateRejectsDuplicateWire(t *testing.T) {
	state := cat.NewGraphState()
	state.Nodes["urn:a"] = cat.Node{URN: "urn:a", Kind: "Node", Stratum: cat.S2, Version: 1}
	state.Nodes["urn:b"] = cat.Node{URN: "urn:b", Kind: "Node", Stratum: cat.S2, Version: 1}

	link := cat.Envelope{Type: cat.LINK, Actor: actor, Link: &cat.LinkPayload{
		SourceURN: "urn:a", SourcePort: "out", TargetURN: "urn:b", TargetPort: "in",
	}}
	result, err := Evaluate(state, link, testTime)
	if err != nil {
		t.Fatal(err)
	}
	_, err = Evaluate(result.State, link, testTime)
	if err == nil {
		t.Fatal("expected ErrWireExists")
	}
}

func TestEvaluateRejectsVersionConflict(t *testing.T) {
	state := cat.NewGraphState()
	state.Nodes["urn:a"] = cat.Node{URN: "urn:a", Kind: "Node", Stratum: cat.S2, Version: 3}

	_, err := Evaluate(state, cat.Envelope{
		Type:   cat.MUTATE,
		Actor:  actor,
		Mutate: &cat.MutatePayload{URN: "urn:a", ExpectedVersion: 1},
	}, testTime)
	if err == nil {
		t.Fatal("expected ErrVersionConflict")
	}
}

func TestEvaluateRejectsMutationOnAuthored(t *testing.T) {
	state := cat.NewGraphState()
	state.Nodes["urn:a"] = cat.Node{URN: "urn:a", Kind: "Node", Stratum: cat.S0, Version: 1}

	_, err := Evaluate(state, cat.Envelope{
		Type:   cat.MUTATE,
		Actor:  actor,
		Mutate: &cat.MutatePayload{URN: "urn:a", ExpectedVersion: 1},
	}, testTime)
	if err == nil {
		t.Fatal("expected ErrMutationBlocked for S0 nodes")
	}
}

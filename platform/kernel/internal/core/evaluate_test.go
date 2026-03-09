package core

import (
	"errors"
	"testing"
	"time"
)

func TestEvaluateAddLinkMutateUnlink(t *testing.T) {
	state := NewGraphState()
	now := time.Date(2026, 3, 9, 0, 0, 0, 0, time.UTC)

	addA := Envelope{Type: MorphismAdd, Actor: "actor:test", Add: &AddPayload{URN: "urn:a", Kind: "Node"}}
	result, err := Evaluate(state, addA, now)
	if err != nil {
		t.Fatalf("add a failed: %v", err)
	}
	state = result.State

	addB := Envelope{Type: MorphismAdd, Actor: "actor:test", Add: &AddPayload{URN: "urn:b", Kind: "Node"}}
	result, err = Evaluate(state, addB, now)
	if err != nil {
		t.Fatalf("add b failed: %v", err)
	}
	state = result.State

	link := Envelope{Type: MorphismLink, Actor: "actor:test", Link: &LinkPayload{SourceURN: "urn:a", SourcePort: "out", TargetURN: "urn:b", TargetPort: "in"}}
	result, err = Evaluate(state, link, now)
	if err != nil {
		t.Fatalf("link failed: %v", err)
	}
	state = result.State

	mutate := Envelope{Type: MorphismMutate, Actor: "actor:test", Mutate: &MutatePayload{URN: "urn:a", ExpectedVersion: 1, Payload: map[string]any{"status": "ok"}}}
	result, err = Evaluate(state, mutate, now)
	if err != nil {
		t.Fatalf("mutate failed: %v", err)
	}
	state = result.State

	if state.Nodes["urn:a"].Version != 2 {
		t.Fatalf("expected version 2, got %d", state.Nodes["urn:a"].Version)
	}

	unlink := Envelope{Type: MorphismUnlink, Actor: "actor:test", Unlink: &UnlinkPayload{SourceURN: "urn:a", SourcePort: "out", TargetURN: "urn:b", TargetPort: "in"}}
	result, err = Evaluate(state, unlink, now)
	if err != nil {
		t.Fatalf("unlink failed: %v", err)
	}
	state = result.State

	if len(state.Wires) != 0 {
		t.Fatalf("expected wires to be removed, found %d", len(state.Wires))
	}
}

func TestEvaluateRejectsVersionConflict(t *testing.T) {
	state := NewGraphState()
	now := time.Now().UTC()
	add := Envelope{Type: MorphismAdd, Actor: "actor:test", Add: &AddPayload{URN: "urn:a", Kind: "Node"}}
	result, err := Evaluate(state, add, now)
	if err != nil {
		t.Fatalf("add failed: %v", err)
	}

	_, err = Evaluate(result.State, Envelope{Type: MorphismMutate, Actor: "actor:test", Mutate: &MutatePayload{URN: "urn:a", ExpectedVersion: 2}}, now)
	if err == nil {
		t.Fatal("expected version conflict")
	}
	if !errors.Is(err, ErrVersionConflict) {
		t.Fatalf("expected version conflict, got %v", err)
	}
}

func TestEvaluateRejectsDuplicateWire(t *testing.T) {
	state := NewGraphState()
	now := time.Now().UTC()
	for _, urn := range []URN{"urn:a", "urn:b"} {
		result, err := Evaluate(state, Envelope{Type: MorphismAdd, Actor: "actor:test", Add: &AddPayload{URN: urn, Kind: "Node"}}, now)
		if err != nil {
			t.Fatalf("add failed: %v", err)
		}
		state = result.State
	}
	link := Envelope{Type: MorphismLink, Actor: "actor:test", Link: &LinkPayload{SourceURN: "urn:a", SourcePort: "out", TargetURN: "urn:b", TargetPort: "in"}}
	result, err := Evaluate(state, link, now)
	if err != nil {
		t.Fatalf("link failed: %v", err)
	}
	_, err = Evaluate(result.State, link, now)
	if err == nil {
		t.Fatal("expected duplicate wire failure")
	}
	if !errors.Is(err, ErrWireExists) {
		t.Fatalf("expected wire exists, got %v", err)
	}
}

func TestEvaluateWithRegistryRejectsInvalidKindAndLink(t *testing.T) {
	registry := &SemanticRegistry{
		Kinds: map[Kind]KindSpec{
			"Node": {
				Mutable:       true,
				AllowedStrata: []Stratum{StratumMaterialized, StratumEvaluated},
				Ports: map[Port]PortSpec{
					"out": {Direction: "out", Targets: []PortTarget{{Kind: "Node", Port: "in"}}},
					"in":  {Direction: "in"},
				},
			},
		},
	}

	_, err := EvaluateWithRegistry(NewGraphState(), Envelope{Type: MorphismAdd, Actor: "actor:test", Add: &AddPayload{URN: "urn:a", Kind: "Missing"}}, time.Now().UTC(), registry)
	if err == nil || !errors.Is(err, ErrInvalidKind) {
		t.Fatalf("expected invalid kind, got %v", err)
	}

	state := NewGraphState()
	for _, urn := range []URN{"urn:a", "urn:b"} {
		result, err := EvaluateWithRegistry(state, Envelope{Type: MorphismAdd, Actor: "actor:test", Add: &AddPayload{URN: urn, Kind: "Node"}}, time.Now().UTC(), registry)
		if err != nil {
			t.Fatalf("add failed: %v", err)
		}
		state = result.State
	}

	_, err = EvaluateWithRegistry(state, Envelope{Type: MorphismLink, Actor: "actor:test", Link: &LinkPayload{SourceURN: "urn:a", SourcePort: "in", TargetURN: "urn:b", TargetPort: "in"}}, time.Now().UTC(), registry)
	if err == nil || !errors.Is(err, ErrInvalidLink) {
		t.Fatalf("expected invalid link, got %v", err)
	}
}

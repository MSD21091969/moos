package core

import (
	"errors"
	"testing"
	"time"
)

func TestEvaluateProgramAppliesAllMorphisms(t *testing.T) {
	state := NewGraphState()
	program := Program{
		Actor: "actor:test",
		Envelopes: []Envelope{
			{Type: MorphismAdd, Add: &AddPayload{URN: "urn:a", Kind: "Node"}},
			{Type: MorphismAdd, Add: &AddPayload{URN: "urn:b", Kind: "Node"}},
			{Type: MorphismLink, Link: &LinkPayload{SourceURN: "urn:a", SourcePort: "out", TargetURN: "urn:b", TargetPort: "in"}},
		},
	}

	result, err := EvaluateProgram(state, program, time.Date(2026, 3, 9, 0, 0, 0, 0, time.UTC))
	if err != nil {
		t.Fatalf("evaluate program failed: %v", err)
	}
	if len(result.Results) != 3 || len(result.Persisted) != 3 {
		t.Fatalf("expected 3 results and persisted entries, got %d and %d", len(result.Results), len(result.Persisted))
	}
	if len(result.State.Nodes) != 2 || len(result.State.Wires) != 1 {
		t.Fatalf("unexpected final state: %+v", result.State)
	}
}

func TestEvaluateProgramIsAtomicOnFailure(t *testing.T) {
	state := NewGraphState()
	program := Program{
		Actor: "actor:test",
		Envelopes: []Envelope{
			{Type: MorphismAdd, Add: &AddPayload{URN: "urn:a", Kind: "Node"}},
			{Type: MorphismLink, Link: &LinkPayload{SourceURN: "urn:a", SourcePort: "out", TargetURN: "urn:missing", TargetPort: "in"}},
		},
	}

	_, err := EvaluateProgram(state, program, time.Now().UTC())
	if err == nil {
		t.Fatal("expected evaluate program to fail")
	}
	if !errors.Is(err, ErrNodeNotFound) {
		t.Fatalf("expected node not found, got %v", err)
	}
	if len(state.Nodes) != 0 || len(state.Wires) != 0 {
		t.Fatalf("input state should be unchanged, got %+v", state)
	}
}

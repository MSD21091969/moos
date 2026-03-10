package fold

import (
	"testing"
	"time"

	"moos/internal/cat"
)

func TestEvaluateProgramAppliesAll(t *testing.T) {
	state := cat.NewGraphState()
	prog := cat.Program{
		Actor: actor,
		Envelopes: []cat.Envelope{
			{Type: cat.ADD, Add: &cat.AddPayload{URN: "urn:p1", Kind: "Node", Stratum: cat.S2}},
			{Type: cat.ADD, Add: &cat.AddPayload{URN: "urn:p2", Kind: "Node", Stratum: cat.S2}},
			{Type: cat.LINK, Link: &cat.LinkPayload{SourceURN: "urn:p1", SourcePort: "out", TargetURN: "urn:p2", TargetPort: "in"}},
		},
	}
	result, err := EvaluateProgram(state, prog, testTime)
	if err != nil {
		t.Fatal(err)
	}
	if len(result.State.Nodes) != 2 {
		t.Fatalf("expected 2 nodes, got %d", len(result.State.Nodes))
	}
	if len(result.State.Wires) != 1 {
		t.Fatalf("expected 1 wire, got %d", len(result.State.Wires))
	}
	if len(result.Persisted) != 3 {
		t.Fatalf("expected 3 persisted, got %d", len(result.Persisted))
	}
}

func TestEvaluateProgramIsAtomicOnFailure(t *testing.T) {
	state := cat.NewGraphState()
	prog := cat.Program{
		Actor: actor,
		Envelopes: []cat.Envelope{
			{Type: cat.ADD, Add: &cat.AddPayload{URN: "urn:ok", Kind: "Node", Stratum: cat.S2}},
			{Type: cat.LINK, Link: &cat.LinkPayload{
				SourceURN: "urn:ok", SourcePort: "out",
				TargetURN: "urn:missing", TargetPort: "in",
			}},
		},
	}
	_, err := EvaluateProgram(state, prog, testTime)
	if err == nil {
		t.Fatal("expected error from missing target")
	}
	if len(state.Nodes) != 0 {
		t.Fatal("original state was mutated on failure")
	}
}

func TestReplayDeterminism(t *testing.T) {
	entries := []cat.PersistedEnvelope{
		{Envelope: cat.Envelope{Type: cat.ADD, Actor: actor, Add: &cat.AddPayload{URN: "urn:r1", Kind: "Node", Stratum: cat.S2}}, IssuedAt: testTime},
		{Envelope: cat.Envelope{Type: cat.ADD, Actor: actor, Add: &cat.AddPayload{URN: "urn:r2", Kind: "Node", Stratum: cat.S2}}, IssuedAt: testTime.Add(time.Second)},
		{Envelope: cat.Envelope{Type: cat.LINK, Actor: actor, Link: &cat.LinkPayload{SourceURN: "urn:r1", SourcePort: "out", TargetURN: "urn:r2", TargetPort: "in"}}, IssuedAt: testTime.Add(2 * time.Second)},
	}

	state1, err := Replay(entries)
	if err != nil {
		t.Fatal(err)
	}
	state2, err := Replay(entries)
	if err != nil {
		t.Fatal(err)
	}

	if len(state1.Nodes) != len(state2.Nodes) || len(state1.Wires) != len(state2.Wires) {
		t.Fatal("replay is not deterministic")
	}
}

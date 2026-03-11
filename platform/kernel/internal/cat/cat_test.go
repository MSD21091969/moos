package cat_test

import (
	"testing"

	"moos/platform/kernel/internal/cat"
)

func TestNormalizeStratum(t *testing.T) {
	if got := cat.NormalizeStratum(""); got != cat.S2 {
		t.Errorf("NormalizeStratum(\"\") = %q, want S2", got)
	}
	if got := cat.NormalizeStratum(cat.S4); got != cat.S4 {
		t.Errorf("NormalizeStratum(S4) = %q, want S4", got)
	}
}

func TestValidStratum(t *testing.T) {
	for _, s := range []cat.Stratum{cat.S0, cat.S1, cat.S2, cat.S3, cat.S4} {
		if !cat.ValidStratum(s) {
			t.Errorf("ValidStratum(%q) = false, want true", s)
		}
	}
	if cat.ValidStratum("S9") {
		t.Error("ValidStratum(S9) = true, want false")
	}
}

func TestWireKey(t *testing.T) {
	key := cat.WireKey("urn:a", "out", "urn:b", "in")
	want := "urn:a|out|urn:b|in"
	if key != want {
		t.Errorf("WireKey = %q, want %q", key, want)
	}
}

func TestGraphStateClone(t *testing.T) {
	gs := cat.NewGraphState()
	gs.Nodes["urn:test"] = cat.Node{
		URN:     "urn:test",
		TypeID:  "node_container",
		Stratum: cat.S2,
		Payload: map[string]any{"key": "val"},
		Version: 1,
	}
	gs.Wires["k"] = cat.Wire{
		SourceURN: "urn:a", SourcePort: "out",
		TargetURN: "urn:b", TargetPort: "in",
	}

	cloned := gs.Clone()

	// Mutate original — clone should be unaffected
	gs.Nodes["urn:test"] = cat.Node{URN: "urn:test", TypeID: "changed", Version: 99}
	delete(gs.Wires, "k")

	if cloned.Nodes["urn:test"].TypeID != "node_container" {
		t.Error("Clone was mutated by modifying original node")
	}
	if _, ok := cloned.Wires["k"]; !ok {
		t.Error("Clone was mutated by deleting original wire")
	}
}

func TestEnvelopeValidate_RequiresActor(t *testing.T) {
	env := cat.Envelope{Type: cat.ADD, Add: &cat.AddPayload{URN: "urn:x", TypeID: "t"}}
	if err := env.Validate(); err == nil {
		t.Error("expected error for missing actor")
	}
}

func TestEnvelopeValidate_ADD(t *testing.T) {
	env := cat.Envelope{
		Type:  cat.ADD,
		Actor: "urn:actor",
		Add:   &cat.AddPayload{URN: "urn:x", TypeID: "node_container"},
	}
	if err := env.Validate(); err != nil {
		t.Errorf("valid ADD envelope should pass: %v", err)
	}
}

func TestEnvelopeValidate_LINK(t *testing.T) {
	env := cat.Envelope{
		Type:  cat.LINK,
		Actor: "urn:actor",
		Link: &cat.LinkPayload{
			SourceURN: "urn:a", SourcePort: "out",
			TargetURN: "urn:b", TargetPort: "in",
		},
	}
	if err := env.Validate(); err != nil {
		t.Errorf("valid LINK envelope should pass: %v", err)
	}
}

func TestEnvelopeValidate_MUTATE(t *testing.T) {
	env := cat.Envelope{
		Type:   cat.MUTATE,
		Actor:  "urn:actor",
		Mutate: &cat.MutatePayload{URN: "urn:x", ExpectedVersion: 1},
	}
	if err := env.Validate(); err != nil {
		t.Errorf("valid MUTATE envelope should pass: %v", err)
	}
}

func TestEnvelopeValidate_UNLINK(t *testing.T) {
	env := cat.Envelope{
		Type:  cat.UNLINK,
		Actor: "urn:actor",
		Unlink: &cat.UnlinkPayload{
			SourceURN: "urn:a", SourcePort: "out",
			TargetURN: "urn:b", TargetPort: "in",
		},
	}
	if err := env.Validate(); err != nil {
		t.Errorf("valid UNLINK envelope should pass: %v", err)
	}
}

func TestEnvelopeValidate_MultiplePayloads(t *testing.T) {
	env := cat.Envelope{
		Type:  cat.ADD,
		Actor: "urn:actor",
		Add:   &cat.AddPayload{URN: "urn:x", TypeID: "t"},
		Link:  &cat.LinkPayload{SourceURN: "a", SourcePort: "o", TargetURN: "b", TargetPort: "i"},
	}
	if err := env.Validate(); err == nil {
		t.Error("expected error for multiple payloads")
	}
}

func TestProgramValidate_Empty(t *testing.T) {
	p := cat.Program{Actor: "urn:actor"}
	if err := p.Validate(); err == nil {
		t.Error("expected error for empty program")
	}
}

func TestProgramNormalizedEnvelopes(t *testing.T) {
	p := cat.Program{
		Actor: "urn:actor",
		Scope: "urn:scope",
		Envelopes: []cat.Envelope{
			{Type: cat.ADD, Add: &cat.AddPayload{URN: "urn:x", TypeID: "node_container"}},
		},
	}
	envs, err := p.NormalizedEnvelopes()
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if envs[0].Actor != "urn:actor" {
		t.Errorf("actor not inherited: got %q", envs[0].Actor)
	}
	if envs[0].Scope != "urn:scope" {
		t.Errorf("scope not inherited: got %q", envs[0].Scope)
	}
}

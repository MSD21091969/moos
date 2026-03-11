package hydration_test

import (
	"testing"

	"moos/kernel_v2/internal/hydration"
)

func TestMaterialize_Basic(t *testing.T) {
	req := hydration.MaterializeRequest{
		Actor: "urn:moos:identity:test",
		Nodes: []hydration.NodeRequest{
			{URN: "urn:a", TypeID: "node_container"},
			{URN: "urn:b", TypeID: "node_container"},
		},
		Wires: []hydration.WireRequest{
			{SourceURN: "urn:a", SourcePort: "out", TargetURN: "urn:b", TargetPort: "in"},
		},
	}

	result, err := hydration.Materialize(req, nil, false)
	if err != nil {
		t.Fatalf("Materialize: %v", err)
	}
	if result.NodeCount != 2 {
		t.Errorf("NodeCount = %d, want 2", result.NodeCount)
	}
	if result.WireCount != 1 {
		t.Errorf("WireCount = %d, want 1", result.WireCount)
	}
	if len(result.Errors) != 0 {
		t.Errorf("unexpected errors: %v", result.Errors)
	}
	if len(result.Program.Envelopes) != 3 {
		t.Errorf("expected 3 envelopes, got %d", len(result.Program.Envelopes))
	}
}

func TestMaterialize_NoActor(t *testing.T) {
	req := hydration.MaterializeRequest{
		Nodes: []hydration.NodeRequest{{URN: "urn:x", TypeID: "t"}},
	}
	_, err := hydration.Materialize(req, nil, false)
	if err == nil {
		t.Error("expected error for missing actor")
	}
}

func TestMaterialize_DryRun(t *testing.T) {
	req := hydration.MaterializeRequest{
		Actor: "urn:moos:identity:test",
		Nodes: []hydration.NodeRequest{{URN: "urn:x", TypeID: "node_container"}},
	}
	result, err := hydration.Materialize(req, nil, true)
	if err != nil {
		t.Fatalf("Materialize: %v", err)
	}
	if !result.DryRun {
		t.Error("expected DryRun=true")
	}
}

func TestMaterialize_ValidationError(t *testing.T) {
	req := hydration.MaterializeRequest{
		Actor: "urn:moos:identity:test",
		Nodes: []hydration.NodeRequest{
			{URN: "", TypeID: "node_container"}, // empty URN → validation error
		},
	}
	result, err := hydration.Materialize(req, nil, false)
	if err != nil {
		t.Fatalf("Materialize: %v", err)
	}
	if len(result.Errors) == 0 {
		t.Error("expected validation errors for empty URN")
	}
}

package hydration

import (
	"testing"
)

func TestMaterializeBasic(t *testing.T) {
	req := MaterializeRequest{
		Actor: "urn:test:actor",
		Nodes: []NodeRequest{
			{URN: "urn:a", Kind: "Node", Stratum: "S2"},
			{URN: "urn:b", Kind: "Node", Stratum: "S2"},
		},
		Wires: []WireRequest{
			{SourceURN: "urn:a", SourcePort: "out", TargetURN: "urn:b", TargetPort: "in"},
		},
	}

	result, err := Materialize(req, nil, false)
	if err != nil {
		t.Fatal(err)
	}
	if result.NodeCount != 2 {
		t.Fatalf("expected 2 nodes, got %d", result.NodeCount)
	}
	if result.WireCount != 1 {
		t.Fatalf("expected 1 wire, got %d", result.WireCount)
	}
	if len(result.Program.Envelopes) != 3 {
		t.Fatalf("expected 3 envelopes (2 ADD + 1 LINK), got %d", len(result.Program.Envelopes))
	}
	if len(result.Errors) != 0 {
		t.Fatalf("expected no errors, got %v", result.Errors)
	}
}

func TestMaterializeMissingActor(t *testing.T) {
	req := MaterializeRequest{
		Nodes: []NodeRequest{{URN: "urn:x", Kind: "Node"}},
	}
	_, err := Materialize(req, nil, false)
	if err == nil {
		t.Fatal("expected error for missing actor")
	}
}

func TestMaterializeDryRun(t *testing.T) {
	req := MaterializeRequest{
		Actor: "urn:test:actor",
		Nodes: []NodeRequest{
			{URN: "urn:n", Kind: "Node"},
		},
	}
	result, err := Materialize(req, nil, true)
	if err != nil {
		t.Fatal(err)
	}
	if !result.DryRun {
		t.Fatal("expected dry_run=true")
	}
}

func TestMaterializeRejectsGlossaryAndLegacyKinds(t *testing.T) {
	req := MaterializeRequest{
		Actor: "urn:test:actor",
		Nodes: []NodeRequest{
			{URN: "urn:moos:cat:C", Kind: "NodeContainer", Stratum: "S2"},
			{URN: "urn:moos:feature:http-api", Kind: "Feature", Stratum: "S2"},
			{URN: "urn:ok:runtime", Kind: "RuntimeSurface", Stratum: "S2"},
		},
		Wires: []WireRequest{
			{SourceURN: "urn:moos:cat:C", SourcePort: "out", TargetURN: "urn:ok:runtime", TargetPort: "in"},
			{SourceURN: "urn:ok:runtime", SourcePort: "out", TargetURN: "urn:ok:runtime", TargetPort: "in"},
		},
	}

	result, err := Materialize(req, nil, false)
	if err != nil {
		t.Fatal(err)
	}

	if len(result.Errors) == 0 {
		t.Fatal("expected validation errors for glossary/legacy inputs")
	}

	if got := len(result.Program.Envelopes); got != 2 {
		t.Fatalf("expected only valid envelopes to survive (1 ADD + 1 LINK), got %d", got)
	}
}

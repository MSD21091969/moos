package lens

import (
	"net/url"
	"testing"

	"moos/platform/kernel/internal/cat"
)

func testState() cat.GraphState {
	gs := cat.NewGraphState()
	gs.Nodes["urn:user:alice"] = cat.Node{URN: "urn:user:alice", TypeID: "user", Stratum: "S2"}
	gs.Nodes["urn:user:bob"] = cat.Node{URN: "urn:user:bob", TypeID: "user", Stratum: "S3"}
	gs.Nodes["urn:provider:openai"] = cat.Node{URN: "urn:provider:openai", TypeID: "provider", Stratum: "S2"}
	gs.Nodes["urn:provider:meta"] = cat.Node{URN: "urn:provider:meta", TypeID: "provider", Stratum: "S2"}
	gs.Nodes["urn:model:gpt4"] = cat.Node{URN: "urn:model:gpt4", TypeID: "agnostic_model", Stratum: "S2"}
	gs.Nodes["urn:agent:a"] = cat.Node{URN: "urn:agent:a", TypeID: "agent_spec", Stratum: "S2"}
	gs.Nodes["urn:score:1"] = cat.Node{URN: "urn:score:1", TypeID: "benchmark_score", Stratum: "S3"}

	w1 := cat.Wire{SourceURN: "urn:user:alice", SourcePort: "OWNS", TargetURN: "urn:provider:openai", TargetPort: "CHILD"}
	w2 := cat.Wire{SourceURN: "urn:provider:openai", SourcePort: "OWNS", TargetURN: "urn:model:gpt4", TargetPort: "CHILD"}
	w3 := cat.Wire{SourceURN: "urn:agent:a", SourcePort: "CAN_ROUTE", TargetURN: "urn:provider:openai", TargetPort: "TRANSPORT"}
	w4 := cat.Wire{SourceURN: "urn:provider:openai", SourcePort: "LINK_NODES", TargetURN: "urn:provider:meta", TargetPort: "LINK_NODES"}
	gs.Wires[w1.Key()] = w1
	gs.Wires[w2.Key()] = w2
	gs.Wires[w3.Key()] = w3
	gs.Wires[w4.Key()] = w4
	return gs
}

func TestApply_FilterByKind(t *testing.T) {
	out := Apply(testState(), LensSpec{Rules: []Rule{{Kind: []cat.TypeID{"provider"}}}})
	if len(out.Nodes) != 2 {
		t.Fatalf("nodes=%d want 2", len(out.Nodes))
	}
	if len(out.Wires) != 1 {
		t.Fatalf("wires=%d want 1", len(out.Wires))
	}
}

func TestApply_FilterByStratum(t *testing.T) {
	out := Apply(testState(), LensSpec{Rules: []Rule{{Stratum: []cat.Stratum{"S3"}}}})
	if len(out.Nodes) != 2 {
		t.Fatalf("nodes=%d want 2", len(out.Nodes))
	}
}

func TestApply_FilterByCategory(t *testing.T) {
	out := Apply(testState(), LensSpec{Rules: []Rule{{Category: []string{"compute"}}}})
	if len(out.Nodes) != 3 {
		t.Fatalf("nodes=%d want 3", len(out.Nodes))
	}
}

func TestApply_FilterByPort(t *testing.T) {
	out := Apply(testState(), LensSpec{Rules: []Rule{{Port: "CAN_ROUTE"}}})
	if len(out.Nodes) != 2 {
		t.Fatalf("nodes=%d want 2", len(out.Nodes))
	}
}

func TestApply_NeighborhoodDepth1(t *testing.T) {
	out := Apply(testState(), LensSpec{Rules: []Rule{{Neighborhood: &Neighborhood{Origin: "urn:provider:openai", Depth: 1}}}})
	if len(out.Nodes) != 5 {
		t.Fatalf("nodes=%d want 5", len(out.Nodes))
	}
}

func TestApply_NeighborhoodDepth0(t *testing.T) {
	out := Apply(testState(), LensSpec{Rules: []Rule{{Neighborhood: &Neighborhood{Origin: "urn:provider:openai", Depth: 0}}}})
	if len(out.Nodes) != 1 {
		t.Fatalf("nodes=%d want 1", len(out.Nodes))
	}
}

func TestApply_IntersectRules(t *testing.T) {
	out := Apply(testState(), LensSpec{Rules: []Rule{{Kind: []cat.TypeID{"provider"}}, {Stratum: []cat.Stratum{"S2"}}}, Mode: "intersect"})
	if len(out.Nodes) != 2 {
		t.Fatalf("nodes=%d want 2", len(out.Nodes))
	}
}

func TestApply_UnionRules(t *testing.T) {
	out := Apply(testState(), LensSpec{Rules: []Rule{{Kind: []cat.TypeID{"provider"}}, {Kind: []cat.TypeID{"user"}}}, Mode: "union"})
	if len(out.Nodes) != 4 {
		t.Fatalf("nodes=%d want 4", len(out.Nodes))
	}
}

func TestApply_EmptyRulesIdentity(t *testing.T) {
	in := testState()
	out := Apply(in, LensSpec{})
	if len(out.Nodes) != len(in.Nodes) || len(out.Wires) != len(in.Wires) {
		t.Fatalf("expected identity lens")
	}
}

func TestApply_UnknownNeighborhood(t *testing.T) {
	out := Apply(testState(), LensSpec{Rules: []Rule{{Neighborhood: &Neighborhood{Origin: "urn:missing", Depth: 2}}}})
	if len(out.Nodes) != 0 || len(out.Wires) != 0 {
		t.Fatalf("expected empty result")
	}
}

func TestApply_NeighborhoodDepthCap(t *testing.T) {
	outA := Apply(testState(), LensSpec{Rules: []Rule{{Neighborhood: &Neighborhood{Origin: "urn:provider:openai", Depth: 10}}}})
	outB := Apply(testState(), LensSpec{Rules: []Rule{{Neighborhood: &Neighborhood{Origin: "urn:provider:openai", Depth: 100}}}})
	if len(outA.Nodes) != len(outB.Nodes) {
		t.Fatalf("depth cap mismatch: %d vs %d", len(outA.Nodes), len(outB.Nodes))
	}
}

func TestParseQueryParams(t *testing.T) {
	q, _ := url.ParseQuery("kind=provider,agnostic_model&stratum=S2,S3&category=compute&port=CAN_ROUTE&neighborhood=urn:provider:openai&depth=2&mode=union")
	s := ParseQueryParams(q)
	if s.Mode != "union" {
		t.Fatalf("mode=%q want union", s.Mode)
	}
	if len(s.Rules) != 1 {
		t.Fatalf("rules=%d want 1", len(s.Rules))
	}
	r := s.Rules[0]
	if len(r.Kind) != 2 || len(r.Stratum) != 2 || len(r.Category) != 1 {
		t.Fatalf("unexpected parsed rule sizes")
	}
	if r.Port != "CAN_ROUTE" || r.Neighborhood == nil || r.Neighborhood.Depth != 2 {
		t.Fatalf("unexpected parsed neighborhood/port")
	}
}

func TestBroadCategoryMapping(t *testing.T) {
	tests := []struct {
		typeID cat.TypeID
		want   string
	}{
		{"agent_session", "identity"},
		{"prg_task", "structure"},
		{"calendar_event", "structure"},
		{"keep_note", "structure"},
		{"channel_message", "structure"},
		{"delegation_task", "structure"},
		{"ontology_term", "ontology"},
		{"ptp_family", "ontology"},
		{"unknown_future_type", "unknown"},
	}

	for _, tt := range tests {
		t.Run(string(tt.typeID), func(t *testing.T) {
			if got := broadCategory(tt.typeID); got != tt.want {
				t.Fatalf("broadCategory(%q) = %q, want %q", tt.typeID, got, tt.want)
			}
		})
	}
}

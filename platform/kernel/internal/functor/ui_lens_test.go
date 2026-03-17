package functor

import (
	"testing"

	"moos/platform/kernel/internal/cat"
)

func TestUILens_Name(t *testing.T) {
	lens := UILens{}
	if got := lens.Name(); got != "FUN02_ui_lens" {
		t.Errorf("Name() = %q, want %q", got, "FUN02_ui_lens")
	}
}

func TestUILens_Project_Empty(t *testing.T) {
	lens := UILens{}
	state := cat.NewGraphState()
	result, err := lens.Project(state)
	if err != nil {
		t.Fatalf("Project() error = %v", err)
	}
	proj := result.(UIProjection)
	if len(proj.Nodes) != 0 {
		t.Errorf("expected 0 nodes, got %d", len(proj.Nodes))
	}
	if len(proj.Edges) != 0 {
		t.Errorf("expected 0 edges, got %d", len(proj.Edges))
	}
}

func TestUILens_StructurePreservation(t *testing.T) {
	// The functor F must preserve: |F(Ob(C))| = |Ob(V)|, |F(Mor(C))| = |Mor(V)|
	state := cat.NewGraphState()
	state.Nodes["urn:moos:test:a"] = cat.Node{
		URN:     "urn:moos:test:a",
		TypeID:  "node_container",
		Stratum: cat.S2,
		Payload: map[string]any{"name": "Alpha"},
	}
	state.Nodes["urn:moos:test:b"] = cat.Node{
		URN:     "urn:moos:test:b",
		TypeID:  "system_tool",
		Stratum: cat.S2,
		Payload: map[string]any{"label": "Beta Tool"},
	}
	w := cat.Wire{
		SourceURN:  "urn:moos:test:a",
		SourcePort: "LINK_NODES",
		TargetURN:  "urn:moos:test:b",
		TargetPort: "LINK_NODES",
	}
	state.Wires[w.Key()] = w

	lens := UILens{}
	proj := lens.ProjectUI(state)

	// Structure preservation: bijection on objects and morphisms
	if len(proj.Nodes) != 2 {
		t.Fatalf("F(Ob) count = %d, want 2", len(proj.Nodes))
	}
	if len(proj.Edges) != 1 {
		t.Fatalf("F(Mor) count = %d, want 1", len(proj.Edges))
	}
}

func TestUILens_TypeIDMapping(t *testing.T) {
	tests := []struct {
		typeID       cat.TypeID
		wantCategory string
	}{
		{"user", "identity"},
		{"collider_admin", "identity"},
		{"superadmin", "identity"},
		{"agent_spec", "identity"},
		{"app_template", "structure"},
		{"node_container", "structure"},
		{"agnostic_model", "compute"},
		{"system_tool", "compute"},
		{"compute_resource", "compute"},
		{"provider", "compute"},
		{"ui_lens", "surface"},
		{"runtime_surface", "surface"},
		{"protocol_adapter", "protocol"},
		{"infra_service", "infra"},
		{"memory_store", "memory"},
		{"platform_config", "platform"},
		{"workstation_config", "platform"},
		{"preference", "config"},
		{"benchmark_suite", "evaluation"},
		{"benchmark_task", "evaluation"},
		{"benchmark_score", "evaluation"},
		{"industry_entity", "industry"},
		{"something_new", "unknown"},
	}
	for _, tt := range tests {
		t.Run(string(tt.typeID), func(t *testing.T) {
			got := broadCategory(tt.typeID)
			if got != tt.wantCategory {
				t.Errorf("broadCategory(%q) = %q, want %q", tt.typeID, got, tt.wantCategory)
			}
		})
	}
}

func TestUILens_DeterministicLayout(t *testing.T) {
	state := cat.NewGraphState()
	state.Nodes["urn:moos:test:stable"] = cat.Node{
		URN:    "urn:moos:test:stable",
		TypeID: "node_container",
	}

	lens := UILens{}
	p1 := lens.ProjectUI(state)
	p2 := lens.ProjectUI(state)

	if p1.Nodes[0].X != p2.Nodes[0].X || p1.Nodes[0].Y != p2.Nodes[0].Y {
		t.Error("layout is not deterministic across calls")
	}
}

func TestUILens_LabelExtraction(t *testing.T) {
	tests := []struct {
		name    string
		payload map[string]any
		want    string
	}{
		{"name field", map[string]any{"name": "Foo"}, "Foo"},
		{"label field", map[string]any{"label": "Bar"}, "Bar"},
		{"name wins over label", map[string]any{"name": "Foo", "label": "Bar"}, "Foo"},
		{"fallback to URN", map[string]any{"other": "x"}, "urn:moos:test:fallback"},
		{"nil payload", nil, "urn:moos:test:fallback"},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			n := cat.Node{
				URN:     "urn:moos:test:fallback",
				TypeID:  "node_container",
				Payload: tt.payload,
			}
			got := extractLabel(n)
			if got != tt.want {
				t.Errorf("extractLabel() = %q, want %q", got, tt.want)
			}
		})
	}
}

func TestUILens_SortedOutput(t *testing.T) {
	state := cat.NewGraphState()
	state.Nodes["urn:moos:test:z"] = cat.Node{URN: "urn:moos:test:z", TypeID: "user"}
	state.Nodes["urn:moos:test:a"] = cat.Node{URN: "urn:moos:test:a", TypeID: "user"}
	state.Nodes["urn:moos:test:m"] = cat.Node{URN: "urn:moos:test:m", TypeID: "user"}

	lens := UILens{}
	proj := lens.ProjectUI(state)

	for i := 1; i < len(proj.Nodes); i++ {
		if proj.Nodes[i-1].ID >= proj.Nodes[i].ID {
			t.Errorf("nodes not sorted: %q >= %q", proj.Nodes[i-1].ID, proj.Nodes[i].ID)
		}
	}
}

func TestUILens_EdgePortPreservation(t *testing.T) {
	state := cat.NewGraphState()
	state.Nodes["urn:a"] = cat.Node{URN: "urn:a", TypeID: "node_container"}
	state.Nodes["urn:b"] = cat.Node{URN: "urn:b", TypeID: "node_container"}
	w := cat.Wire{
		SourceURN:  "urn:a",
		SourcePort: "OWNS",
		TargetURN:  "urn:b",
		TargetPort: "OWNS",
	}
	state.Wires[w.Key()] = w

	lens := UILens{}
	proj := lens.ProjectUI(state)

	edge := proj.Edges[0]
	if edge.Source != "urn:a" || edge.Target != "urn:b" {
		t.Errorf("edge endpoints wrong: %q → %q", edge.Source, edge.Target)
	}
	if edge.SourcePort != "OWNS" || edge.TargetPort != "OWNS" {
		t.Errorf("port topology not preserved: %q → %q", edge.SourcePort, edge.TargetPort)
	}
}

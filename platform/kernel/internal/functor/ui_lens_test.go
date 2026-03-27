package functor

import (
	"reflect"
	"testing"
	"time"

	"moos/platform/kernel/internal/cat"
	"moos/platform/kernel/internal/fold"
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
		{"kernel_instance", "infra"},
		{"memory_store", "memory"},
		{"platform_config", "platform"},
		{"workstation_config", "platform"},
		{"preference", "config"},
		{"benchmark_suite", "evaluation"},
		{"benchmark_task", "evaluation"},
		{"benchmark_score", "evaluation"},
		{"industry_entity", "industry"},
		{"agent_session", "identity"},
		{"prg_task", "structure"},
		{"calendar_event", "structure"},
		{"keep_note", "structure"},
		{"channel_message", "structure"},
		{"ptp_family", "ontology"},
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

// ---------------------------------------------------------------------------
// PRG034 — Naturality Harness (CI-2)
//
// The commuting square:
//
//   C  ——Apply(M)——→  C'
//   |                  |
//   F                  F
//   ↓                  ↓
//   V  ——   ==   ——→  V'
//
// For every morphism M and state S:
//   F(Apply(M, S)) == F(S') where S' is the post-evaluation state.
//
// We verify this by:
//   1. Build initial state S₀
//   2. Create envelope M
//   3. S₁ = Evaluate(S₀, M)
//   4. P  = F(S₁)          ← left path: evaluate then project
//   5. Independently construct S₁' from scratch
//   6. P' = F(S₁')         ← right path: project the expected state
//   7. Assert P == P'
// ---------------------------------------------------------------------------

func TestUILens_Naturality_ADD(t *testing.T) {
	lens := UILens{}
	now := time.Now()

	// Start from empty state
	s0 := cat.NewGraphState()

	// Morphism: ADD a node
	env := cat.Envelope{
		Type:  cat.ADD,
		Actor: "urn:moos:agent:test",
		Add: &cat.AddPayload{
			URN:     "urn:moos:test:nat-add",
			TypeID:  "system_tool",
			Stratum: cat.S2,
			Payload: map[string]any{"name": "NatTest"},
		},
	}

	// Left path: Apply then Project
	result, err := fold.Evaluate(s0, env, now)
	if err != nil {
		t.Fatalf("Evaluate(ADD) error: %v", err)
	}
	left := lens.ProjectUI(result.State)

	// Right path: construct expected state independently, then Project
	expected := cat.NewGraphState()
	expected.Nodes["urn:moos:test:nat-add"] = cat.Node{
		URN:       "urn:moos:test:nat-add",
		TypeID:    "system_tool",
		Stratum:   cat.S2,
		Payload:   map[string]any{"name": "NatTest"},
		Version:   1,
		CreatedAt: now,
		UpdatedAt: now,
	}
	right := lens.ProjectUI(expected)

	if !reflect.DeepEqual(left, right) {
		t.Errorf("naturality violated for ADD\nleft  = %+v\nright = %+v", left, right)
	}
}

func TestUILens_Naturality_LINK(t *testing.T) {
	lens := UILens{}
	now := time.Now()

	// Build base state with two nodes
	s0 := cat.NewGraphState()
	s0.Nodes["urn:moos:test:src"] = cat.Node{
		URN: "urn:moos:test:src", TypeID: "node_container", Stratum: cat.S2, Version: 1,
	}
	s0.Nodes["urn:moos:test:tgt"] = cat.Node{
		URN: "urn:moos:test:tgt", TypeID: "system_tool", Stratum: cat.S2, Version: 1,
	}

	// Morphism: LINK src → tgt
	env := cat.Envelope{
		Type:  cat.LINK,
		Actor: "urn:moos:agent:test",
		Link: &cat.LinkPayload{
			SourceURN:  "urn:moos:test:src",
			SourcePort: "OWNS",
			TargetURN:  "urn:moos:test:tgt",
			TargetPort: "OWNS",
		},
	}

	result, err := fold.Evaluate(s0, env, now)
	if err != nil {
		t.Fatalf("Evaluate(LINK) error: %v", err)
	}
	left := lens.ProjectUI(result.State)

	// Independently construct expected state
	expected := s0.Clone()
	w := cat.Wire{
		SourceURN: "urn:moos:test:src", SourcePort: "OWNS",
		TargetURN: "urn:moos:test:tgt", TargetPort: "OWNS",
		CreatedAt: now,
	}
	expected.Wires[w.Key()] = w
	right := lens.ProjectUI(expected)

	if !reflect.DeepEqual(left, right) {
		t.Errorf("naturality violated for LINK\nleft  = %+v\nright = %+v", left, right)
	}
}

func TestUILens_Naturality_MUTATE(t *testing.T) {
	lens := UILens{}
	now := time.Now()

	// Base state: one node at S2, version 1
	s0 := cat.NewGraphState()
	s0.Nodes["urn:moos:test:mut"] = cat.Node{
		URN:     "urn:moos:test:mut",
		TypeID:  "system_tool",
		Stratum: cat.S2,
		Payload: map[string]any{"name": "Before"},
		Version: 1,
	}

	// Morphism: MUTATE payload
	env := cat.Envelope{
		Type:  cat.MUTATE,
		Actor: "urn:moos:agent:test",
		Mutate: &cat.MutatePayload{
			URN:             "urn:moos:test:mut",
			ExpectedVersion: 1,
			Payload:         map[string]any{"name": "After"},
		},
	}

	result, err := fold.Evaluate(s0, env, now)
	if err != nil {
		t.Fatalf("Evaluate(MUTATE) error: %v", err)
	}
	left := lens.ProjectUI(result.State)

	// Independently construct expected state
	expected := cat.NewGraphState()
	expected.Nodes["urn:moos:test:mut"] = cat.Node{
		URN:       "urn:moos:test:mut",
		TypeID:    "system_tool",
		Stratum:   cat.S2,
		Payload:   map[string]any{"name": "After"},
		Version:   2,
		UpdatedAt: now,
	}
	right := lens.ProjectUI(expected)

	if !reflect.DeepEqual(left, right) {
		t.Errorf("naturality violated for MUTATE\nleft  = %+v\nright = %+v", left, right)
	}
}

func TestUILens_Naturality_UNLINK(t *testing.T) {
	lens := UILens{}
	now := time.Now()

	// Base state: two nodes + one wire
	s0 := cat.NewGraphState()
	s0.Nodes["urn:moos:test:a"] = cat.Node{
		URN: "urn:moos:test:a", TypeID: "node_container", Stratum: cat.S2, Version: 1,
	}
	s0.Nodes["urn:moos:test:b"] = cat.Node{
		URN: "urn:moos:test:b", TypeID: "node_container", Stratum: cat.S2, Version: 1,
	}
	w := cat.Wire{
		SourceURN: "urn:moos:test:a", SourcePort: "LINK_NODES",
		TargetURN: "urn:moos:test:b", TargetPort: "LINK_NODES",
	}
	s0.Wires[w.Key()] = w

	// Morphism: UNLINK the wire
	env := cat.Envelope{
		Type:  cat.UNLINK,
		Actor: "urn:moos:agent:test",
		Unlink: &cat.UnlinkPayload{
			SourceURN:  "urn:moos:test:a",
			SourcePort: "LINK_NODES",
			TargetURN:  "urn:moos:test:b",
			TargetPort: "LINK_NODES",
		},
	}

	result, err := fold.Evaluate(s0, env, now)
	if err != nil {
		t.Fatalf("Evaluate(UNLINK) error: %v", err)
	}
	left := lens.ProjectUI(result.State)

	// Independently construct expected state: just the two nodes, no wire
	expected := cat.NewGraphState()
	expected.Nodes["urn:moos:test:a"] = cat.Node{
		URN: "urn:moos:test:a", TypeID: "node_container", Stratum: cat.S2, Version: 1,
	}
	expected.Nodes["urn:moos:test:b"] = cat.Node{
		URN: "urn:moos:test:b", TypeID: "node_container", Stratum: cat.S2, Version: 1,
	}
	right := lens.ProjectUI(expected)

	if !reflect.DeepEqual(left, right) {
		t.Errorf("naturality violated for UNLINK\nleft  = %+v\nright = %+v", left, right)
	}
}

// TestUILens_Naturality_Composition verifies that naturality holds for
// composed morphisms: F(Apply(M₂, Apply(M₁, S))) == F(S₂) where S₂ is
// independently constructed from the sequential application of M₁ then M₂.
func TestUILens_Naturality_Composition(t *testing.T) {
	lens := UILens{}
	now := time.Now()

	s0 := cat.NewGraphState()

	// M₁: ADD node A
	env1 := cat.Envelope{
		Type: cat.ADD, Actor: "urn:moos:agent:test",
		Add: &cat.AddPayload{
			URN: "urn:moos:test:comp-a", TypeID: "node_container", Stratum: cat.S2,
			Payload: map[string]any{"name": "CompA"},
		},
	}
	r1, err := fold.Evaluate(s0, env1, now)
	if err != nil {
		t.Fatalf("Evaluate(ADD A) error: %v", err)
	}

	// M₂: ADD node B
	env2 := cat.Envelope{
		Type: cat.ADD, Actor: "urn:moos:agent:test",
		Add: &cat.AddPayload{
			URN: "urn:moos:test:comp-b", TypeID: "system_tool", Stratum: cat.S2,
			Payload: map[string]any{"name": "CompB"},
		},
	}
	r2, err := fold.Evaluate(r1.State, env2, now)
	if err != nil {
		t.Fatalf("Evaluate(ADD B) error: %v", err)
	}

	// M₃: LINK A → B
	env3 := cat.Envelope{
		Type: cat.LINK, Actor: "urn:moos:agent:test",
		Link: &cat.LinkPayload{
			SourceURN: "urn:moos:test:comp-a", SourcePort: "OWNS",
			TargetURN: "urn:moos:test:comp-b", TargetPort: "OWNS",
		},
	}
	r3, err := fold.Evaluate(r2.State, env3, now)
	if err != nil {
		t.Fatalf("Evaluate(LINK) error: %v", err)
	}

	left := lens.ProjectUI(r3.State)

	// Independent expected state
	expected := cat.NewGraphState()
	expected.Nodes["urn:moos:test:comp-a"] = cat.Node{
		URN: "urn:moos:test:comp-a", TypeID: "node_container", Stratum: cat.S2,
		Payload: map[string]any{"name": "CompA"}, Version: 1,
		CreatedAt: now, UpdatedAt: now,
	}
	expected.Nodes["urn:moos:test:comp-b"] = cat.Node{
		URN: "urn:moos:test:comp-b", TypeID: "system_tool", Stratum: cat.S2,
		Payload: map[string]any{"name": "CompB"}, Version: 1,
		CreatedAt: now, UpdatedAt: now,
	}
	ew := cat.Wire{
		SourceURN: "urn:moos:test:comp-a", SourcePort: "OWNS",
		TargetURN: "urn:moos:test:comp-b", TargetPort: "OWNS",
		CreatedAt: now,
	}
	expected.Wires[ew.Key()] = ew
	right := lens.ProjectUI(expected)

	if !reflect.DeepEqual(left, right) {
		t.Errorf("naturality violated for composition (ADD+ADD+LINK)\nleft  = %+v\nright = %+v", left, right)
	}
}

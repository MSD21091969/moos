package lens_test

import (
	"testing"

	"moos/platform/kernel/internal/cat"
	"moos/platform/kernel/internal/lens"
	"moos/platform/kernel/internal/operad"
)

func makeRegistry() *operad.Registry {
	return &operad.Registry{
		Types: map[cat.TypeID]operad.TypeSpec{
			"agnostic_model": {
				Mutable:       true,
				AllowedStrata: []cat.Stratum{"S2", "S3"},
				Ports: map[cat.Port]operad.PortSpec{
					"CLASSIFIES": {
						Direction: "out",
						Targets: []operad.PortTarget{
							{TypeID: "provider", Port: "CLASSIFIED_BY"},
						},
					},
					"CLASSIFIED_BY": {
						Direction: "in",
						Targets:   []operad.PortTarget{},
					},
				},
			},
			"provider": {
				Mutable:       true,
				AllowedStrata: []cat.Stratum{"S2", "S3"},
				Ports: map[cat.Port]operad.PortSpec{
					"CLASSIFIED_BY": {
						Direction: "in",
						Targets:   []operad.PortTarget{},
					},
					"HOSTS": {
						Direction: "out",
						Targets: []operad.PortTarget{
							{TypeID: "agnostic_model", Port: "HOSTED_BY"},
						},
					},
				},
			},
			"user": {
				Mutable:       true,
				AllowedStrata: []cat.Stratum{"S2", "S3"},
				// No ports defined — should be omitted from results.
			},
		},
	}
}

func TestComputeSaturation_AllPortsWired(t *testing.T) {
	state := cat.NewGraphState()
	state.Nodes[cat.URN("urn:moos:model:gpt4")] = cat.Node{
		URN: "urn:moos:model:gpt4", TypeID: "agnostic_model", Stratum: "S2",
	}
	state.Nodes[cat.URN("urn:moos:provider:openai")] = cat.Node{
		URN: "urn:moos:provider:openai", TypeID: "provider", Stratum: "S2",
	}

	// Wire: model --CLASSIFIES--> provider
	wk := cat.WireKey("urn:moos:model:gpt4", "CLASSIFIES", "urn:moos:provider:openai", "CLASSIFIED_BY")
	state.Wires[wk] = cat.Wire{
		SourceURN: "urn:moos:model:gpt4", SourcePort: "CLASSIFIES",
		TargetURN: "urn:moos:provider:openai", TargetPort: "CLASSIFIED_BY",
	}

	reg := makeRegistry()
	result := lens.ComputeSaturation(state, reg)

	// Model node: CLASSIFIES should be saturated (1 target, 1 wire)
	modelSat, ok := result[cat.URN("urn:moos:model:gpt4")]
	if !ok {
		t.Fatal("expected saturation entry for model node")
	}
	classifiesPort := modelSat.Ports[cat.Port("CLASSIFIES")]
	if !classifiesPort.Saturated {
		t.Error("CLASSIFIES port should be saturated")
	}
	if classifiesPort.ActualWires != 1 {
		t.Errorf("CLASSIFIES actual_wires = %d, want 1", classifiesPort.ActualWires)
	}

	// Model node: CLASSIFIED_BY has 0 targets defined, should NOT be saturated
	classifiedBy := modelSat.Ports[cat.Port("CLASSIFIED_BY")]
	if classifiedBy.Saturated {
		t.Error("CLASSIFIED_BY should not be saturated (0 defined targets)")
	}

	// Provider node: CLASSIFIED_BY should have 1 actual wire (incoming)
	provSat := result[cat.URN("urn:moos:provider:openai")]
	provCB := provSat.Ports[cat.Port("CLASSIFIED_BY")]
	if provCB.ActualWires != 1 {
		t.Errorf("provider CLASSIFIED_BY actual_wires = %d, want 1", provCB.ActualWires)
	}
}

func TestComputeSaturation_UnwiredPorts(t *testing.T) {
	state := cat.NewGraphState()
	state.Nodes[cat.URN("urn:moos:provider:openai")] = cat.Node{
		URN: "urn:moos:provider:openai", TypeID: "provider", Stratum: "S2",
	}
	// No wires at all.

	reg := makeRegistry()
	result := lens.ComputeSaturation(state, reg)

	provSat, ok := result[cat.URN("urn:moos:provider:openai")]
	if !ok {
		t.Fatal("expected saturation entry for provider node")
	}

	// Both ports should have 0 wires.
	if provSat.TotalWired != 0 {
		t.Errorf("total_wired = %d, want 0", provSat.TotalWired)
	}

	// Gaps: both ports should be in gaps.
	if len(provSat.Gaps) != 2 {
		t.Errorf("gaps count = %d, want 2", len(provSat.Gaps))
	}

	// HOSTS port: 1 defined target, 0 actual → not saturated.
	hostsPort := provSat.Ports[cat.Port("HOSTS")]
	if hostsPort.Saturated {
		t.Error("HOSTS should not be saturated (0 wires)")
	}
	if hostsPort.DefinedTargets != 1 {
		t.Errorf("HOSTS defined_targets = %d, want 1", hostsPort.DefinedTargets)
	}
}

func TestComputeSaturation_NodeNotInRegistry(t *testing.T) {
	state := cat.NewGraphState()
	state.Nodes[cat.URN("urn:moos:custom:thing")] = cat.Node{
		URN: "urn:moos:custom:thing", TypeID: "unknown_type", Stratum: "S2",
	}

	reg := makeRegistry()
	result := lens.ComputeSaturation(state, reg)

	if _, ok := result[cat.URN("urn:moos:custom:thing")]; ok {
		t.Error("node with unknown TypeID should be omitted from saturation")
	}
}

func TestComputeSaturation_NodeWithNoPortSpec(t *testing.T) {
	state := cat.NewGraphState()
	state.Nodes[cat.URN("urn:moos:user:sam")] = cat.Node{
		URN: "urn:moos:user:sam", TypeID: "user", Stratum: "S2",
	}

	reg := makeRegistry()
	result := lens.ComputeSaturation(state, reg)

	// user has TypeSpec but no ports — should be omitted.
	if _, ok := result[cat.URN("urn:moos:user:sam")]; ok {
		t.Error("node with 0 ports should be omitted from saturation")
	}
}

func TestComputeSaturation_EmptyGraph(t *testing.T) {
	state := cat.NewGraphState()
	reg := makeRegistry()
	result := lens.ComputeSaturation(state, reg)

	if len(result) != 0 {
		t.Errorf("empty graph should produce empty saturation, got %d entries", len(result))
	}
}

func TestComputeSaturation_NilRegistry(t *testing.T) {
	state := cat.NewGraphState()
	state.Nodes[cat.URN("urn:moos:model:x")] = cat.Node{
		URN: "urn:moos:model:x", TypeID: "agnostic_model", Stratum: "S2",
	}

	result := lens.ComputeSaturation(state, nil)
	if len(result) != 0 {
		t.Errorf("nil registry should produce empty saturation, got %d entries", len(result))
	}
}

func TestComputeNodeSaturation_SingleNode(t *testing.T) {
	state := cat.NewGraphState()
	state.Nodes[cat.URN("urn:moos:model:gpt4")] = cat.Node{
		URN: "urn:moos:model:gpt4", TypeID: "agnostic_model", Stratum: "S2",
	}
	state.Nodes[cat.URN("urn:moos:provider:openai")] = cat.Node{
		URN: "urn:moos:provider:openai", TypeID: "provider", Stratum: "S2",
	}

	reg := makeRegistry()

	sat, ok := lens.ComputeNodeSaturation(state, reg, "urn:moos:model:gpt4")
	if !ok {
		t.Fatal("expected saturation for model node")
	}
	if sat.TypeID != "agnostic_model" {
		t.Errorf("type_id = %s, want agnostic_model", sat.TypeID)
	}

	// Non-existent node.
	_, ok = lens.ComputeNodeSaturation(state, reg, "urn:moos:nope")
	if ok {
		t.Error("non-existent node should return false")
	}
}

func TestComputeSaturation_GapsSorted(t *testing.T) {
	state := cat.NewGraphState()
	state.Nodes[cat.URN("urn:moos:provider:x")] = cat.Node{
		URN: "urn:moos:provider:x", TypeID: "provider", Stratum: "S2",
	}

	reg := makeRegistry()
	result := lens.ComputeSaturation(state, reg)
	sat := result[cat.URN("urn:moos:provider:x")]

	// Gaps should be sorted: CLASSIFIED_BY < HOSTS.
	if len(sat.Gaps) < 2 {
		t.Fatalf("expected 2 gaps, got %d", len(sat.Gaps))
	}
	if sat.Gaps[0] >= sat.Gaps[1] {
		t.Errorf("gaps not sorted: %v", sat.Gaps)
	}
}

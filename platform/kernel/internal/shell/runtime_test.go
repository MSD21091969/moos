package shell

import (
	"path/filepath"
	"testing"

	"moos/platform/kernel/internal/core"
)

func TestRuntimeReplaysLog(t *testing.T) {
	logPath := filepath.Join(t.TempDir(), "morphism-log.jsonl")
	runtime, err := NewRuntime(logPath)
	if err != nil {
		t.Fatalf("new runtime failed: %v", err)
	}

	if _, err := runtime.Apply(core.Envelope{Type: core.MorphismAdd, Actor: "actor:test", Add: &core.AddPayload{URN: "urn:a", Kind: "Node"}}); err != nil {
		t.Fatalf("apply add failed: %v", err)
	}

	reloaded, err := NewRuntime(logPath)
	if err != nil {
		t.Fatalf("reload failed: %v", err)
	}
	node, ok := reloaded.Node("urn:a")
	if !ok || node.URN != "urn:a" {
		t.Fatalf("expected replayed node urn:a, got %+v", node)
	}
}

func TestRuntimeQueryProjections(t *testing.T) {
	logPath := filepath.Join(t.TempDir(), "morphism-log.jsonl")
	runtime, err := NewRuntime(logPath)
	if err != nil {
		t.Fatalf("new runtime failed: %v", err)
	}

	for _, envelope := range []core.Envelope{
		{Type: core.MorphismAdd, Actor: "actor:test", Add: &core.AddPayload{URN: "urn:a", Kind: "Node"}},
		{Type: core.MorphismAdd, Actor: "actor:test", Add: &core.AddPayload{URN: "urn:b", Kind: "Node", Stratum: core.StratumValidated}},
		{Type: core.MorphismLink, Actor: "actor:test", Link: &core.LinkPayload{SourceURN: "urn:a", SourcePort: "out", TargetURN: "urn:b", TargetPort: "in"}},
	} {
		if _, err := runtime.Apply(envelope); err != nil {
			t.Fatalf("apply failed: %v", err)
		}
	}

	snapshot := runtime.Snapshot()
	if len(snapshot.Nodes) != 2 || len(snapshot.Wires) != 1 {
		t.Fatalf("unexpected snapshot sizes: %+v", snapshot)
	}

	nodes := runtime.Nodes("Node", string(core.StratumValidated))
	if len(nodes) != 1 || nodes[0].URN != "urn:b" {
		t.Fatalf("expected filtered node urn:b, got %+v", nodes)
	}

	outgoing := runtime.OutgoingWires("urn:a")
	if len(outgoing) != 1 || outgoing[0].TargetURN != "urn:b" {
		t.Fatalf("expected outgoing wire to urn:b, got %+v", outgoing)
	}

	incoming := runtime.IncomingWires("urn:b")
	if len(incoming) != 1 || incoming[0].SourceURN != "urn:a" {
		t.Fatalf("expected incoming wire from urn:a, got %+v", incoming)
	}
}

func TestRuntimeApplyProgramIsAtomic(t *testing.T) {
	logPath := filepath.Join(t.TempDir(), "morphism-log.jsonl")
	runtime, err := NewRuntime(logPath)
	if err != nil {
		t.Fatalf("new runtime failed: %v", err)
	}

	program := core.Program{
		Actor: "actor:test",
		Envelopes: []core.Envelope{
			{Type: core.MorphismAdd, Add: &core.AddPayload{URN: "urn:good", Kind: "Node"}},
			{Type: core.MorphismLink, Link: &core.LinkPayload{SourceURN: "urn:good", SourcePort: "out", TargetURN: "urn:missing", TargetPort: "in"}},
		},
	}

	_, err = runtime.ApplyProgram(program)
	if err == nil {
		t.Fatal("expected apply program to fail")
	}
	if _, exists := runtime.Node("urn:good"); exists {
		t.Fatal("expected no partial state after failed program")
	}
	if len(runtime.LogEntries()) != 0 {
		t.Fatalf("expected no log entries after failed program, got %d", len(runtime.LogEntries()))
	}
}

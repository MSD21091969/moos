package shell_test

import (
	"errors"
	"os"
	"path/filepath"
	"testing"

	"moos/kernel_v2/internal/cat"
	"moos/kernel_v2/internal/shell"
)

var testActor = cat.URN("urn:moos:identity:test-actor")

func newTestRuntime(t *testing.T) *shell.Runtime {
	t.Helper()
	store := shell.NewMemStore()
	rt, err := shell.NewRuntime(store, nil)
	if err != nil {
		t.Fatalf("NewRuntime: %v", err)
	}
	return rt
}

func TestRuntime_Apply_ADD(t *testing.T) {
	rt := newTestRuntime(t)
	env := cat.Envelope{
		Type:  cat.ADD,
		Actor: testActor,
		Add:   &cat.AddPayload{URN: "urn:a", TypeID: "node_container"},
	}
	result, err := rt.Apply(env)
	if err != nil {
		t.Fatalf("Apply: %v", err)
	}
	if result.Node == nil || result.Node.URN != "urn:a" {
		t.Error("expected node urn:a in result")
	}
	if len(rt.Nodes()) != 1 {
		t.Errorf("expected 1 node, got %d", len(rt.Nodes()))
	}
}

func TestRuntime_SeedIfAbsent(t *testing.T) {
	rt := newTestRuntime(t)
	env := cat.Envelope{
		Type:  cat.ADD,
		Actor: testActor,
		Add:   &cat.AddPayload{URN: "urn:seed", TypeID: "node_container"},
	}
	if err := rt.SeedIfAbsent(env); err != nil {
		t.Fatalf("first seed: %v", err)
	}
	// Second seed should be absorbed (idempotent)
	if err := rt.SeedIfAbsent(env); err != nil {
		t.Fatalf("second seed should be idempotent: %v", err)
	}
	if len(rt.Nodes()) != 1 {
		t.Errorf("expected 1 node after double seed, got %d", len(rt.Nodes()))
	}
}

func TestRuntime_ApplyProgram(t *testing.T) {
	rt := newTestRuntime(t)
	prog := cat.Program{
		Actor: testActor,
		Envelopes: []cat.Envelope{
			{Type: cat.ADD, Add: &cat.AddPayload{URN: "urn:x", TypeID: "node_container"}},
			{Type: cat.ADD, Add: &cat.AddPayload{URN: "urn:y", TypeID: "node_container"}},
			{Type: cat.LINK, Link: &cat.LinkPayload{SourceURN: "urn:x", SourcePort: "out", TargetURN: "urn:y", TargetPort: "in"}},
		},
	}
	result, err := rt.ApplyProgram(prog)
	if err != nil {
		t.Fatalf("ApplyProgram: %v", err)
	}
	if len(result.State.Nodes) != 2 {
		t.Errorf("expected 2 nodes, got %d", len(result.State.Nodes))
	}
	if len(result.State.Wires) != 1 {
		t.Errorf("expected 1 wire, got %d", len(result.State.Wires))
	}
	if rt.LogLen() != 3 {
		t.Errorf("expected log length 3, got %d", rt.LogLen())
	}
}

func TestRuntime_Apply_Duplicate(t *testing.T) {
	rt := newTestRuntime(t)
	env := cat.Envelope{
		Type:  cat.ADD,
		Actor: testActor,
		Add:   &cat.AddPayload{URN: "urn:dup", TypeID: "node_container"},
	}
	rt.Apply(env)
	_, err := rt.Apply(env)
	if !errors.Is(err, cat.ErrNodeExists) {
		t.Errorf("expected ErrNodeExists, got %v", err)
	}
}

func TestRuntime_OutgoingIncomingWires(t *testing.T) {
	rt := newTestRuntime(t)
	prog := cat.Program{
		Actor: testActor,
		Envelopes: []cat.Envelope{
			{Type: cat.ADD, Add: &cat.AddPayload{URN: "urn:src", TypeID: "node_container"}},
			{Type: cat.ADD, Add: &cat.AddPayload{URN: "urn:tgt", TypeID: "node_container"}},
			{Type: cat.LINK, Link: &cat.LinkPayload{SourceURN: "urn:src", SourcePort: "out", TargetURN: "urn:tgt", TargetPort: "in"}},
		},
	}
	rt.ApplyProgram(prog)

	if out := rt.OutgoingWires("urn:src"); len(out) != 1 {
		t.Errorf("expected 1 outgoing wire from urn:src, got %d", len(out))
	}
	if in := rt.IncomingWires("urn:tgt"); len(in) != 1 {
		t.Errorf("expected 1 incoming wire to urn:tgt, got %d", len(in))
	}
}

func TestLogStore_RoundTrip(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "test.jsonl")

	store, err := shell.NewLogStore(path)
	if err != nil {
		t.Fatalf("NewLogStore: %v", err)
	}

	entries := []cat.PersistedEnvelope{
		{Envelope: cat.Envelope{Type: cat.ADD, Actor: testActor, Add: &cat.AddPayload{URN: "urn:ls", TypeID: "node_container"}}},
	}

	if err := store.Append(entries); err != nil {
		t.Fatalf("Append: %v", err)
	}

	got, err := store.ReadAll()
	if err != nil {
		t.Fatalf("ReadAll: %v", err)
	}
	if len(got) != 1 {
		t.Fatalf("expected 1 entry, got %d", len(got))
	}
	if got[0].Envelope.Add.URN != "urn:ls" {
		t.Errorf("round-trip URN mismatch")
	}
}

func TestLogStore_EmptyFile(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "empty.jsonl")

	store, err := shell.NewLogStore(path)
	if err != nil {
		t.Fatalf("NewLogStore: %v", err)
	}
	// No file => empty log
	entries, err := store.ReadAll()
	if err != nil {
		t.Fatalf("ReadAll on nonexistent: %v", err)
	}
	if len(entries) != 0 {
		t.Errorf("expected 0 entries, got %d", len(entries))
	}
}

func TestLogStore_Replay(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "replay.jsonl")
	store, _ := shell.NewLogStore(path)

	// Create runtime, add nodes, verify state persists
	rt1, _ := shell.NewRuntime(store, nil)
	rt1.Apply(cat.Envelope{Type: cat.ADD, Actor: testActor, Add: &cat.AddPayload{URN: "urn:persist", TypeID: "node_container"}})

	// New runtime from same store should replay
	rt2, err := shell.NewRuntime(store, nil)
	if err != nil {
		t.Fatalf("NewRuntime replay: %v", err)
	}
	if _, ok := rt2.Node("urn:persist"); !ok {
		t.Error("node urn:persist not found after replay")
	}
}

func TestLogStore_Cleanup(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "cleanup.jsonl")
	store, _ := shell.NewLogStore(path)
	store.Append([]cat.PersistedEnvelope{
		{Envelope: cat.Envelope{Type: cat.ADD, Actor: testActor, Add: &cat.AddPayload{URN: "urn:c", TypeID: "node_container"}}},
	})
	if _, err := os.Stat(path); os.IsNotExist(err) {
		t.Error("expected log file to exist")
	}
}

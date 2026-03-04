package morphism

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"testing"

	"github.com/collider/moos/internal/container"
)

type fakeStore struct {
	records   map[string]container.Record
	wires     map[string]container.WireRecord
	logs      []container.MorphismLogRecord
	appendErr error
	createErr error
	linkErr   error
	unlinkErr error
}

func wireKey(w container.WireRecord) string {
	return w.FromContainerURN + "|" + w.FromPort + "|" + w.ToContainerURN + "|" + w.ToPort
}

func (store *fakeStore) Create(ctx context.Context, record container.Record) error {
	if store.createErr != nil {
		return store.createErr
	}
	store.records[record.URN] = record
	return nil
}

func (store *fakeStore) MutateKernel(ctx context.Context, urn string, expectedVersion int64, kernelJSON json.RawMessage) (int64, error) {
	record, ok := store.records[urn]
	if !ok {
		return 0, container.ErrNotFound
	}
	if record.Version != expectedVersion {
		return record.Version, container.ErrVersionConflict
	}
	record.KernelJSON = kernelJSON
	record.Version++
	store.records[urn] = record
	return record.Version, nil
}

func (store *fakeStore) Link(ctx context.Context, wire container.WireRecord) error {
	if store.linkErr != nil {
		return store.linkErr
	}
	if _, ok := store.records[wire.FromContainerURN]; !ok {
		return container.ErrNotFound
	}
	if _, ok := store.records[wire.ToContainerURN]; !ok {
		return container.ErrNotFound
	}
	key := wireKey(wire)
	if _, exists := store.wires[key]; exists {
		return container.ErrAlreadyExists
	}
	store.wires[key] = wire
	return nil
}

func (store *fakeStore) Unlink(ctx context.Context, wire container.WireRecord) error {
	if store.unlinkErr != nil {
		return store.unlinkErr
	}
	key := wireKey(wire)
	if _, exists := store.wires[key]; !exists {
		return container.ErrNotFound
	}
	delete(store.wires, key)
	return nil
}

func (store *fakeStore) AppendMorphismLog(ctx context.Context, record container.MorphismLogRecord) error {
	if store.appendErr != nil {
		return store.appendErr
	}
	store.logs = append(store.logs, record)
	return nil
}

func TestExecutorAddWritesLog(t *testing.T) {
	store := &fakeStore{records: map[string]container.Record{}, wires: map[string]container.WireRecord{}}
	executor := NewExecutor(store, "urn:moos:actor:system")

	err := executor.Add(context.Background(), container.Record{URN: "urn:moos:test:add", Kind: "data", ParentURN: sql.NullString{}})
	if err != nil {
		t.Fatalf("expected no error, got %v", err)
	}
	if len(store.logs) != 1 || store.logs[0].Type != "ADD" {
		t.Fatalf("expected ADD log entry")
	}
}

func TestExecutorMutateConflictDoesNotLog(t *testing.T) {
	store := &fakeStore{records: map[string]container.Record{
		"urn:moos:test:mutate": {URN: "urn:moos:test:mutate", Kind: "data", Version: 2},
	}, wires: map[string]container.WireRecord{}}
	executor := NewExecutor(store, "urn:moos:actor:system")

	_, err := executor.Mutate(context.Background(), "urn:moos:test:mutate", 1, json.RawMessage(`{"ok":true}`))
	if !errors.Is(err, container.ErrVersionConflict) {
		t.Fatalf("expected version conflict, got %v", err)
	}
	if len(store.logs) != 0 {
		t.Fatalf("expected no log entry on conflict")
	}
}

func TestExecutorLinkWritesLog(t *testing.T) {
	store := &fakeStore{records: map[string]container.Record{
		"urn:moos:test:from": {URN: "urn:moos:test:from", Kind: "composite", Version: 1},
		"urn:moos:test:to":   {URN: "urn:moos:test:to", Kind: "data", Version: 1},
	}, wires: map[string]container.WireRecord{}}
	executor := NewExecutor(store, "urn:moos:actor:system")

	err := executor.Link(context.Background(), container.WireRecord{FromContainerURN: "urn:moos:test:from", FromPort: "out", ToContainerURN: "urn:moos:test:to", ToPort: "in"})
	if err != nil {
		t.Fatalf("expected no error, got %v", err)
	}
	if len(store.logs) != 1 || store.logs[0].Type != "LINK" {
		t.Fatalf("expected LINK log entry")
	}
}

func TestExecutorUnlinkWritesLog(t *testing.T) {
	wire := container.WireRecord{FromContainerURN: "urn:moos:test:from", FromPort: "out", ToContainerURN: "urn:moos:test:to", ToPort: "in"}
	store := &fakeStore{records: map[string]container.Record{
		"urn:moos:test:from": {URN: "urn:moos:test:from", Kind: "composite", Version: 1},
		"urn:moos:test:to":   {URN: "urn:moos:test:to", Kind: "data", Version: 1},
	}, wires: map[string]container.WireRecord{wireKey(wire): wire}}
	executor := NewExecutor(store, "urn:moos:actor:system")

	err := executor.Unlink(context.Background(), wire)
	if err != nil {
		t.Fatalf("expected no error, got %v", err)
	}
	if len(store.logs) != 1 || store.logs[0].Type != "UNLINK" {
		t.Fatalf("expected UNLINK log entry")
	}
}

func TestExecutorMutateAppendError(t *testing.T) {
	store := &fakeStore{records: map[string]container.Record{
		"urn:moos:test:mutate": {URN: "urn:moos:test:mutate", Kind: "data", Version: 1},
	}, wires: map[string]container.WireRecord{}, appendErr: errors.New("append failed")}
	executor := NewExecutor(store, "urn:moos:actor:system")

	_, err := executor.Mutate(context.Background(), "urn:moos:test:mutate", 1, json.RawMessage(`{"ok":true}`))
	if err == nil || err.Error() != "append failed" {
		t.Fatalf("expected append failure, got %v", err)
	}
}

func TestExecutorApplyDispatch(t *testing.T) {
	store := &fakeStore{records: map[string]container.Record{
		"urn:moos:test:from":   {URN: "urn:moos:test:from", Kind: "composite", Version: 1},
		"urn:moos:test:to":     {URN: "urn:moos:test:to", Kind: "data", Version: 1},
		"urn:moos:test:mutate": {URN: "urn:moos:test:mutate", Kind: "data", Version: 1},
	}, wires: map[string]container.WireRecord{}}
	executor := NewExecutor(store, "urn:moos:actor:system")

	if _, err := executor.Apply(context.Background(), Envelope{Type: "ADD", Add: &AddPayload{Container: container.Record{URN: "urn:moos:test:add2", Kind: "data"}}}); err != nil {
		t.Fatalf("expected add apply success, got %v", err)
	}
	if _, err := executor.Apply(context.Background(), Envelope{Type: "LINK", Link: &LinkPayload{Wire: container.WireRecord{FromContainerURN: "urn:moos:test:from", FromPort: "out", ToContainerURN: "urn:moos:test:to", ToPort: "in"}}}); err != nil {
		t.Fatalf("expected link apply success, got %v", err)
	}
	if _, err := executor.Apply(context.Background(), Envelope{Type: "MUTATE", Mutate: &MutatePayload{URN: "urn:moos:test:mutate", ExpectedVersion: 1, KernelJSON: json.RawMessage(`{"m":1}`)}}); err != nil {
		t.Fatalf("expected mutate apply success, got %v", err)
	}
	if _, err := executor.Apply(context.Background(), Envelope{Type: "UNLINK", Unlink: &UnlinkPayload{Wire: container.WireRecord{FromContainerURN: "urn:moos:test:from", FromPort: "out", ToContainerURN: "urn:moos:test:to", ToPort: "in"}}}); err != nil {
		t.Fatalf("expected unlink apply success, got %v", err)
	}

	if len(store.logs) != 4 {
		t.Fatalf("expected 4 log entries, got %d", len(store.logs))
	}
}

func TestExecutorApplyInvalidEnvelope(t *testing.T) {
	store := &fakeStore{records: map[string]container.Record{}, wires: map[string]container.WireRecord{}}
	executor := NewExecutor(store, "urn:moos:actor:system")

	_, err := executor.Apply(context.Background(), Envelope{Type: "MUTATE"})
	if !errors.Is(err, ErrInvalidEnvelope) {
		t.Fatalf("expected ErrInvalidEnvelope, got %v", err)
	}
	_, err = executor.Apply(context.Background(), Envelope{Type: "UNKNOWN"})
	if !errors.Is(err, ErrInvalidEnvelope) {
		t.Fatalf("expected ErrInvalidEnvelope, got %v", err)
	}
}

func TestExecutorApplyMissingPayloadVariants(t *testing.T) {
	store := &fakeStore{records: map[string]container.Record{}, wires: map[string]container.WireRecord{}}
	executor := NewExecutor(store, "urn:moos:actor:system")

	_, err := executor.Apply(context.Background(), Envelope{Type: "ADD"})
	if !errors.Is(err, ErrInvalidEnvelope) {
		t.Fatalf("expected ErrInvalidEnvelope for ADD, got %v", err)
	}
	_, err = executor.Apply(context.Background(), Envelope{Type: "LINK"})
	if !errors.Is(err, ErrInvalidEnvelope) {
		t.Fatalf("expected ErrInvalidEnvelope for LINK, got %v", err)
	}
	_, err = executor.Apply(context.Background(), Envelope{Type: "UNLINK"})
	if !errors.Is(err, ErrInvalidEnvelope) {
		t.Fatalf("expected ErrInvalidEnvelope for UNLINK, got %v", err)
	}
}

func TestExecutorAddLinkUnlinkAppendError(t *testing.T) {
	store := &fakeStore{records: map[string]container.Record{
		"urn:from": {URN: "urn:from", Kind: "composite", Version: 1},
		"urn:to":   {URN: "urn:to", Kind: "data", Version: 1},
	}, wires: map[string]container.WireRecord{}, appendErr: errors.New("append fail")}
	executor := NewExecutor(store, "urn:moos:actor:system")

	if err := executor.Add(context.Background(), container.Record{URN: "urn:add", Kind: "data"}); err == nil {
		t.Fatalf("expected add append error")
	}
	if err := executor.Link(context.Background(), container.WireRecord{FromContainerURN: "urn:from", FromPort: "out", ToContainerURN: "urn:to", ToPort: "in"}); err == nil {
		t.Fatalf("expected link append error")
	}

	store.wires[wireKey(container.WireRecord{FromContainerURN: "urn:from", FromPort: "out", ToContainerURN: "urn:to", ToPort: "in"})] = container.WireRecord{FromContainerURN: "urn:from", FromPort: "out", ToContainerURN: "urn:to", ToPort: "in"}
	if err := executor.Unlink(context.Background(), container.WireRecord{FromContainerURN: "urn:from", FromPort: "out", ToContainerURN: "urn:to", ToPort: "in"}); err == nil {
		t.Fatalf("expected unlink append error")
	}
}

func TestExecutorOperationStoreErrors(t *testing.T) {
	executor := NewExecutor(&fakeStore{records: map[string]container.Record{}, wires: map[string]container.WireRecord{}, createErr: errors.New("create failed")}, "urn:moos:actor:system")
	if err := executor.Add(context.Background(), container.Record{URN: "urn:add", Kind: "data"}); err == nil {
		t.Fatalf("expected add store error")
	}

	executor = NewExecutor(&fakeStore{records: map[string]container.Record{}, wires: map[string]container.WireRecord{}, linkErr: errors.New("link failed")}, "urn:moos:actor:system")
	if err := executor.Link(context.Background(), container.WireRecord{}); err == nil {
		t.Fatalf("expected link store error")
	}

	executor = NewExecutor(&fakeStore{records: map[string]container.Record{}, wires: map[string]container.WireRecord{}, unlinkErr: errors.New("unlink failed")}, "urn:moos:actor:system")
	if err := executor.Unlink(context.Background(), container.WireRecord{}); err == nil {
		t.Fatalf("expected unlink store error")
	}
}

func TestExecutorAppendMarshalError(t *testing.T) {
	store := &fakeStore{records: map[string]container.Record{}, wires: map[string]container.WireRecord{}}
	executor := NewExecutor(store, "urn:moos:actor:system")
	badPayload := map[string]any{"bad": make(chan int)}
	if err := executor.append(context.Background(), "ADD", "urn:scope", nil, badPayload); err == nil {
		t.Fatalf("expected marshal error")
	}
}

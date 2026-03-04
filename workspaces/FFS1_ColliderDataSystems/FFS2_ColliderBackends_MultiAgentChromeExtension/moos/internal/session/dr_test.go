package session

import (
	"context"
	"encoding/json"
	"errors"
	"io"
	"log/slog"
	"testing"
	"time"

	"github.com/collider/moos/internal/container"
	"github.com/collider/moos/internal/model"
)

func TestDR_RestoreWithCorruptedMessages(t *testing.T) {
	// Simulate corrupted morphism (bad JSON)
	msgBytes, _ := json.Marshal(model.Message{Role: "user", Content: "persisted"})

	store := &fakeContainerStore{
		records: []container.Record{
			{URN: "urn:moos:session:s_dr", Kind: "SESSION"},
		},
		children: []container.Record{
			{URN: "urn:moos:message:1", Kind: "MESSAGE", KernelJSON: msgBytes},
			{URN: "urn:moos:message:corrupted", Kind: "MESSAGE", KernelJSON: []byte(`{"role":"user","content":bad_json`)}, // Corrupted
			{URN: "urn:moos:message:2", Kind: "MESSAGE", KernelJSON: msgBytes},
		},
	}

	manager := NewManagerWithContainerStore(&fakeExecutor{}, model.NewDispatcher("anthropic", model.AnthropicAdapter{}), time.Minute, 25*time.Millisecond, slog.New(slog.NewTextHandler(io.Discard, nil)), store)
	defer manager.Shutdown()

	list := manager.List()
	if len(list) != 1 {
		t.Fatalf("expected 1 session restored, got %d", len(list))
	}

	// Verify the session only loaded the 2 valid messages
	manager.mu.RLock()
	state := manager.sessions["s_dr"]
	manager.mu.RUnlock()

	if len(state.messages) != 2 {
		t.Fatalf("expected 2 valid messages, got %d", len(state.messages))
	}
}

func TestDR_PostgresFailureGraceful(t *testing.T) {
	// Simulate database down during restore
	store := &fakeContainerStoreErr{
		err: errors.New("connection refused"),
	}

	// Should not panic or crash
	manager := NewManagerWithContainerStore(&fakeExecutor{}, model.NewDispatcher("anthropic", model.AnthropicAdapter{}), time.Minute, 25*time.Millisecond, slog.New(slog.NewTextHandler(io.Discard, nil)), store)
	defer manager.Shutdown()

	list := manager.List()
	if len(list) != 0 {
		t.Fatalf("expected 0 sessions on db failure, got %d", len(list))
	}
}

type fakeContainerStoreErr struct {
	err error
}

func (f *fakeContainerStoreErr) ListByKind(ctx context.Context, kind string, limit int) ([]container.Record, error) {
	return nil, f.err
}

func (f *fakeContainerStoreErr) ListChildren(ctx context.Context, parentURN string) ([]container.Record, error) {
	return nil, f.err
}

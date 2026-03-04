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
	"github.com/collider/moos/internal/morphism"
)

type fakeExecutor struct {
	calls int
	err   error
}

func (executor *fakeExecutor) Apply(ctx context.Context, envelope morphism.Envelope) (int64, error) {
	_ = ctx
	_ = envelope
	executor.calls++
	if executor.err != nil {
		return 0, executor.err
	}
	return 1, nil
}

type fakeContainerStore struct {
	records  []container.Record
	children []container.Record
}

func (f *fakeContainerStore) ListByKind(ctx context.Context, kind string, limit int) ([]container.Record, error) {
	return f.records, nil
}

func (f *fakeContainerStore) ListChildren(ctx context.Context, parentURN string) ([]container.Record, error) {
	return f.children, nil
}

func TestManagerCreateSendAndList(t *testing.T) {
	executor := &fakeExecutor{}
	dispatcher := model.NewDispatcher("anthropic", model.AnthropicAdapter{}, model.GeminiAdapter{})
	manager := NewManager(executor, dispatcher, time.Minute, 25*time.Millisecond, slog.New(slog.NewTextHandler(io.Discard, nil)))
	defer manager.Shutdown()

	events := make([]Event, 0)
	manager.SetBroadcaster(func(sessionID string, event Event) {
		_ = sessionID
		events = append(events, event)
	})

	summary, err := manager.Create()
	if err != nil {
		t.Fatalf("expected create success, got %v", err)
	}
	if summary.SessionID == "" {
		t.Fatalf("expected session id")
	}
	if err := manager.Send(summary.SessionID, "hello"); err != nil {
		t.Fatalf("expected send success, got %v", err)
	}

	time.Sleep(120 * time.Millisecond)
	if len(manager.List()) != 1 {
		t.Fatalf("expected one active session")
	}
	if len(events) == 0 {
		t.Fatalf("expected streamed events")
	}
}

func TestManagerApplyMorphismFromPrompt(t *testing.T) {
	executor := &fakeExecutor{}
	dispatcher := model.NewDispatcher("gemini", model.GeminiAdapter{})
	manager := NewManager(executor, dispatcher, time.Minute, 25*time.Millisecond, slog.New(slog.NewTextHandler(io.Discard, nil)))
	defer manager.Shutdown()

	summary, _ := manager.Create()
	payload := "```json\n{\"type\":\"ADD\",\"add\":{\"container\":{\"URN\":\"urn:moos:s:1\",\"Kind\":\"data\"}}}\n```"
	if err := manager.Send(summary.SessionID, payload); err != nil {
		t.Fatalf("expected send success, got %v", err)
	}

	time.Sleep(120 * time.Millisecond)
	if executor.calls == 0 {
		t.Fatalf("expected morphism apply call")
	}
}

func TestManagerSendUnknownSession(t *testing.T) {
	manager := NewManager(&fakeExecutor{}, model.NewDispatcher("anthropic", model.AnthropicAdapter{}), time.Minute, 25*time.Millisecond, slog.New(slog.NewTextHandler(io.Discard, nil)))
	defer manager.Shutdown()

	if err := manager.Send("missing", "hi"); err == nil {
		t.Fatalf("expected unknown session error")
	}
}

func TestManagerExecutorErrorEmitsEvent(t *testing.T) {
	executor := &fakeExecutor{err: errors.New("apply failed")}
	dispatcher := model.NewDispatcher("anthropic", model.AnthropicAdapter{})
	manager := NewManager(executor, dispatcher, time.Minute, 25*time.Millisecond, slog.New(slog.NewTextHandler(io.Discard, nil)))
	defer manager.Shutdown()

	hasError := false
	manager.SetBroadcaster(func(sessionID string, event Event) {
		_ = sessionID
		if event.Method == "stream.error" {
			hasError = true
		}
	})

	summary, _ := manager.Create()
	payload := "```json\n{\"type\":\"ADD\",\"add\":{\"container\":{\"URN\":\"urn:moos:s:2\",\"Kind\":\"data\"}}}\n```"
	_ = manager.Send(summary.SessionID, payload)
	time.Sleep(120 * time.Millisecond)

	if !hasError {
		t.Fatalf("expected stream.error event")
	}
}

func TestManagerToolDispatchStubEvent(t *testing.T) {
	executor := &fakeExecutor{}
	dispatcher := model.NewDispatcher("gemini", model.GeminiAdapter{})
	manager := NewManager(executor, dispatcher, time.Minute, 25*time.Millisecond, slog.New(slog.NewTextHandler(io.Discard, nil)))
	defer manager.Shutdown()

	hasToolResult := false
	manager.SetBroadcaster(func(sessionID string, event Event) {
		_ = sessionID
		if event.Method == "stream.tool_result" {
			hasToolResult = true
		}
	})

	summary, _ := manager.Create()
	_ = manager.Send(summary.SessionID, `tool:echo {"value":"hello"}`)
	time.Sleep(120 * time.Millisecond)

	if !hasToolResult {
		t.Fatalf("expected stream.tool_result event")
	}
}

func TestManagerRestoresFromStore(t *testing.T) {
	msgBytes, _ := json.Marshal(model.Message{Role: "user", Content: "persisted"})

	store := &fakeContainerStore{
		records: []container.Record{
			{URN: "urn:moos:session:s_restore", Kind: "SESSION"},
		},
		children: []container.Record{
			{URN: "urn:moos:message:1", Kind: "MESSAGE", KernelJSON: msgBytes},
		},
	}

	manager := NewManagerWithContainerStore(&fakeExecutor{}, model.NewDispatcher("anthropic", model.AnthropicAdapter{}), time.Minute, 25*time.Millisecond, slog.New(slog.NewTextHandler(io.Discard, nil)), store)
	defer manager.Shutdown()

	list := manager.List()
	if len(list) == 0 {
		t.Fatalf("expected restored session")
	}
}

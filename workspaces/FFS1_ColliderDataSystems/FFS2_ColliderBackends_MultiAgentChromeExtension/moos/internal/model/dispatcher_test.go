package model

import (
	"context"
	"errors"
	"strings"
	"testing"
)

type failingAdapter struct {
	name string
}

func (adapter failingAdapter) Name() string { return adapter.name }

func (adapter failingAdapter) Complete(ctx context.Context, request CompletionRequest) (CompletionResult, error) {
	_ = ctx
	_ = request
	return CompletionResult{}, errors.New("provider failed")
}

func TestDispatcherFallsBackToSecondary(t *testing.T) {
	dispatcher := NewDispatcher("anthropic", failingAdapter{name: "anthropic"}, GeminiAdapter{})
	result, err := dispatcher.Complete(context.Background(), CompletionRequest{Messages: []Message{{Role: "user", Content: "hello"}}})
	if err != nil {
		t.Fatalf("expected fallback success, got %v", err)
	}
	if result.Text == "" {
		t.Fatalf("expected non-empty fallback response")
	}
}

func TestParseToolCalls(t *testing.T) {
	toolCalls := parseToolCalls("tool:echo {\"value\":\"x\"}")
	if len(toolCalls) != 1 {
		t.Fatalf("expected 1 tool call")
	}
	if toolCalls[0].Name != "echo" {
		t.Fatalf("expected echo tool")
	}
}

// ---------------------------------------------------------------------------
// Extended dispatcher tests
// ---------------------------------------------------------------------------

func TestDispatcher_NoAdapters(t *testing.T) {
	dispatcher := NewDispatcher("anthropic")
	_, err := dispatcher.Complete(context.Background(), CompletionRequest{
		Messages: []Message{{Role: "user", Content: "hello"}},
	})
	if err == nil {
		t.Fatal("expected error with no adapters")
	}
	if !strings.Contains(err.Error(), "no model adapters configured") {
		t.Errorf("expected 'no model adapters configured', got %v", err)
	}
}

func TestDispatcher_AllAdaptersFail(t *testing.T) {
	dispatcher := NewDispatcher("anthropic",
		failingAdapter{name: "anthropic"},
		failingAdapter{name: "gemini"},
	)
	_, err := dispatcher.Complete(context.Background(), CompletionRequest{
		Messages: []Message{{Role: "user", Content: "hello"}},
	})
	if err == nil {
		t.Fatal("expected error when all adapters fail")
	}
	if !strings.Contains(err.Error(), "all model adapters failed") {
		t.Errorf("expected 'all model adapters failed', got %v", err)
	}
}

func TestDispatcher_PrimarySucceeds(t *testing.T) {
	dispatcher := NewDispatcher("gemini", GeminiAdapter{}, failingAdapter{name: "anthropic"})
	result, err := dispatcher.Complete(context.Background(), CompletionRequest{
		Messages: []Message{{Role: "user", Content: "test"}},
	})
	if err != nil {
		t.Fatalf("expected success, got %v", err)
	}
	if !strings.Contains(result.Text, "test") {
		t.Errorf("expected primary result, got %q", result.Text)
	}
}

func TestDispatcher_PrimaryNotRegistered(t *testing.T) {
	dispatcher := NewDispatcher("openai", GeminiAdapter{})
	result, err := dispatcher.Complete(context.Background(), CompletionRequest{
		Messages: []Message{{Role: "user", Content: "hello"}},
	})
	if err != nil {
		t.Fatalf("expected success via available adapter, got %v", err)
	}
	if result.Text == "" {
		t.Error("expected non-empty text from fallback")
	}
}

func TestDispatcher_ProviderOrder(t *testing.T) {
	dispatcher := NewDispatcher("anthropic",
		failingAdapter{name: "anthropic"},
		failingAdapter{name: "beta"},
		GeminiAdapter{},
	)
	result, err := dispatcher.Complete(context.Background(), CompletionRequest{
		Messages: []Message{{Role: "user", Content: "hi"}},
	})
	if err != nil {
		t.Fatalf("expected success from gemini, got %v", err)
	}
	if !strings.Contains(result.Text, "gemini") {
		t.Errorf("expected gemini result, got %q", result.Text)
	}
}

func TestDispatcher_EmptyPrimaryDefaultsToAnthropic(t *testing.T) {
	dispatcher := NewDispatcher("", GeminiAdapter{})
	// Primary defaults to "anthropic" which is not registered.
	// Should still fall back to gemini.
	result, err := dispatcher.Complete(context.Background(), CompletionRequest{
		Messages: []Message{{Role: "user", Content: "hi"}},
	})
	if err != nil {
		t.Fatalf("expected success, got %v", err)
	}
	if result.Text == "" {
		t.Error("expected non-empty text")
	}
}

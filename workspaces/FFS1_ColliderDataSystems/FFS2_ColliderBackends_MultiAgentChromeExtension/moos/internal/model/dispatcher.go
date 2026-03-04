package model

import (
	"context"
	"fmt"
	"sort"

	"github.com/collider/moos/internal/morphism"
)

type Message struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type CompletionRequest struct {
	SessionID string
	Messages  []Message
}

type CompletionResult struct {
	Text      string
	Morphisms []morphism.Envelope
	ToolCalls []ToolCall
}

type ToolCall struct {
	Name      string         `json:"name"`
	Arguments map[string]any `json:"arguments,omitempty"`
}

// Chunk is a single streaming unit emitted by a model adapter.
// Text holds a partial token or sentence fragment. Morphisms are included
// once the full response has been accumulated and parsed. ToolCalls are
// populated when the model or user input triggers a tool invocation.
// Done signals that the stream has completed cleanly.
type Chunk struct {
	Text      string
	Morphisms []morphism.Envelope
	ToolCalls []ToolCall
	Done      bool
	Error     error
}

// completionToStream wraps a blocking Complete() call as a Chunk channel,
// enabling non-streaming adapters to satisfy the streaming interface.
func completionToStream(ctx context.Context, adapter Adapter, request CompletionRequest) (<-chan Chunk, error) {
	result, err := adapter.Complete(ctx, request)
	if err != nil {
		return nil, err
	}
	ch := make(chan Chunk, 2)
	go func() {
		defer close(ch)
		if result.Text != "" || len(result.Morphisms) > 0 || len(result.ToolCalls) > 0 {
			ch <- Chunk{Text: result.Text, Morphisms: result.Morphisms, ToolCalls: result.ToolCalls}
		}
		ch <- Chunk{Done: true}
	}()
	return ch, nil
}

type Adapter interface {
	Name() string
	Complete(ctx context.Context, request CompletionRequest) (CompletionResult, error)
	// Stream yields Chunks in real time as the model generates tokens.
	// The channel is closed after the final Chunk with Done=true is sent.
	Stream(ctx context.Context, request CompletionRequest) (<-chan Chunk, error)
}

type Dispatcher struct {
	adapters map[string]Adapter
	primary  string
}

func NewDispatcher(primary string, adapters ...Adapter) *Dispatcher {
	mapped := map[string]Adapter{}
	for _, adapter := range adapters {
		mapped[adapter.Name()] = adapter
	}
	if primary == "" {
		primary = "anthropic"
	}
	if _, ok := mapped[primary]; !ok {
		if _, hasAnthropic := mapped["anthropic"]; hasAnthropic {
			primary = "anthropic"
		}
	}
	return &Dispatcher{adapters: mapped, primary: primary}
}

func (dispatcher *Dispatcher) Complete(ctx context.Context, request CompletionRequest) (CompletionResult, error) {
	order := dispatcher.providerOrder()
	if len(order) == 0 {
		return CompletionResult{}, fmt.Errorf("no model adapters configured")
	}
	var lastErr error
	for _, name := range order {
		adapter := dispatcher.adapters[name]
		result, err := adapter.Complete(ctx, request)
		if err == nil {
			return result, nil
		}
		lastErr = err
	}
	if lastErr != nil {
		return CompletionResult{}, fmt.Errorf("all model adapters failed: %w", lastErr)
	}
	return CompletionResult{}, fmt.Errorf("model adapter not configured for %s", dispatcher.primary)
}

// Stream calls Stream() on each adapter in priority order, returning the first
// success. If all adapters fail to open a stream, an error is returned.
func (dispatcher *Dispatcher) Stream(ctx context.Context, request CompletionRequest) (<-chan Chunk, error) {
	order := dispatcher.providerOrder()
	if len(order) == 0 {
		return nil, fmt.Errorf("no model adapters configured")
	}
	var lastErr error
	for _, name := range order {
		adapter := dispatcher.adapters[name]
		ch, err := adapter.Stream(ctx, request)
		if err == nil {
			return ch, nil
		}
		lastErr = err
	}
	if lastErr != nil {
		return nil, fmt.Errorf("all model adapters failed: %w", lastErr)
	}
	return nil, fmt.Errorf("model adapter not configured for %s", dispatcher.primary)
}

func (dispatcher *Dispatcher) providerOrder() []string {
	order := make([]string, 0, len(dispatcher.adapters))
	if _, ok := dispatcher.adapters[dispatcher.primary]; ok {
		order = append(order, dispatcher.primary)
	}
	secondary := make([]string, 0, len(dispatcher.adapters))
	for name := range dispatcher.adapters {
		if name == dispatcher.primary {
			continue
		}
		secondary = append(secondary, name)
	}
	sort.Strings(secondary)
	order = append(order, secondary...)
	return order
}

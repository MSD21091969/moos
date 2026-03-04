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

type Adapter interface {
	Name() string
	Complete(ctx context.Context, request CompletionRequest) (CompletionResult, error)
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

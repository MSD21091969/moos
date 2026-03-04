package tool

import (
	"context"
	"errors"
	"testing"
	"time"
)

func TestMCPBridgeToolsCallHonorsTimeout(t *testing.T) {
	registry := NewRegistry()
	if err := registry.Register(Definition{Name: "slow", Description: "slow tool"}, func(ctx context.Context, arguments map[string]any) (map[string]any, error) {
		_ = arguments
		select {
		case <-ctx.Done():
			return nil, ctx.Err()
		case <-time.After(200 * time.Millisecond):
			return map[string]any{"ok": true}, nil
		}
	}); err != nil {
		t.Fatalf("register slow tool: %v", err)
	}

	bridge := NewMCPBridge(registry, Policy{MaxInputBytes: 1024, MaxExecutionMs: 10, BlockedPrefix: []string{"internal_"}})
	_, err := bridge.ToolsCall(context.Background(), "slow", map[string]any{})
	if err == nil {
		t.Fatalf("expected timeout error")
	}
	if !errors.Is(err, context.DeadlineExceeded) {
		t.Fatalf("expected deadline exceeded, got %v", err)
	}
}

func TestMCPBridgeToolsCallBlocksPrefixedTools(t *testing.T) {
	registry := NewRegistry()
	if err := registry.Register(Definition{Name: "internal_secret", Description: "blocked"}, func(ctx context.Context, arguments map[string]any) (map[string]any, error) {
		_ = ctx
		_ = arguments
		return map[string]any{"ok": true}, nil
	}); err != nil {
		t.Fatalf("register blocked tool: %v", err)
	}

	bridge := NewMCPBridge(registry, DefaultPolicy())
	_, err := bridge.ToolsCall(context.Background(), "internal_secret", map[string]any{"x": 1})
	if err == nil {
		t.Fatalf("expected blocked tool error")
	}
}

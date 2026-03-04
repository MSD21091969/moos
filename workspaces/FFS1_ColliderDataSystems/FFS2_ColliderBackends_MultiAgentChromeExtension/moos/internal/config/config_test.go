package config

import (
	"os"
	"testing"
	"time"
)

func TestLoad_Defaults(t *testing.T) {
	t.Setenv("MOOS_HTTP_ADDR", "")
	t.Setenv("MOOS_WS_ADDR", "")
	t.Setenv("DATABASE_URL", "")
	t.Setenv("REDIS_URL", "")
	t.Setenv("MOOS_MIGRATIONS_DIR", "")
	t.Setenv("MOOS_MIGRATIONS_AUTO_APPLY", "")
	t.Setenv("MOOS_BEARER_TOKEN", "")

	cfg := Load()
	if cfg.HTTPAddr != ":8080" {
		t.Fatalf("expected default HTTP addr, got %s", cfg.HTTPAddr)
	}
	if cfg.WebSocketAddr != ":18789" {
		t.Fatalf("expected default websocket addr, got %s", cfg.WebSocketAddr)
	}
	if cfg.RedisURL != "" {
		t.Fatalf("expected empty redis url by default")
	}
	if cfg.MigrationsDir != "./migrations" {
		t.Fatalf("expected default migrations dir, got %s", cfg.MigrationsDir)
	}
	if cfg.MigrationsAutoApply {
		t.Fatalf("expected auto-apply default false")
	}
	if cfg.BearerToken != "" {
		t.Fatalf("expected empty bearer token by default")
	}
	if cfg.ModelProvider != "anthropic" {
		t.Fatalf("expected default model provider anthropic, got %s", cfg.ModelProvider)
	}
	if cfg.SessionTTL != 30*time.Minute {
		t.Fatalf("expected default session ttl 30m, got %s", cfg.SessionTTL)
	}
	if cfg.SessionCleanupEvery != time.Minute {
		t.Fatalf("expected default session cleanup 1m, got %s", cfg.SessionCleanupEvery)
	}
	if cfg.ToolRuntimeAddr != "localhost:50052" {
		t.Fatalf("expected default tool runtime addr, got %s", cfg.ToolRuntimeAddr)
	}
}

func TestLoad_BoolParsing(t *testing.T) {
	t.Setenv("MOOS_MIGRATIONS_AUTO_APPLY", "true")
	if !Load().MigrationsAutoApply {
		t.Fatalf("expected true for 'true'")
	}
	t.Setenv("MOOS_MIGRATIONS_AUTO_APPLY", "1")
	if !Load().MigrationsAutoApply {
		t.Fatalf("expected true for '1'")
	}
	t.Setenv("MOOS_MIGRATIONS_AUTO_APPLY", "no")
	if Load().MigrationsAutoApply {
		t.Fatalf("expected false for 'no'")
	}
}

func TestGetEnvBoolFallback(t *testing.T) {
	_ = os.Unsetenv("TEST_BOOL")
	if !getEnvBool("TEST_BOOL", true) {
		t.Fatalf("expected fallback true when env unset")
	}
}

func TestLoad_BearerToken(t *testing.T) {
	t.Setenv("MOOS_BEARER_TOKEN", "phase1-token")
	if Load().BearerToken != "phase1-token" {
		t.Fatalf("expected configured bearer token")
	}
}

func TestLoad_WebSocketAddr(t *testing.T) {
	t.Setenv("MOOS_WS_ADDR", ":19000")
	if Load().WebSocketAddr != ":19000" {
		t.Fatalf("expected configured websocket addr")
	}
}

func TestLoad_ModelAndSessionSettings(t *testing.T) {
	t.Setenv("MOOS_MODEL_PROVIDER", "gemini")
	t.Setenv("MOOS_SESSION_TTL", "45m")
	t.Setenv("MOOS_SESSION_CLEANUP_EVERY", "10s")
	t.Setenv("REDIS_URL", "redis://localhost:6379/0")
	t.Setenv("MOOS_TOOL_RUNTIME_ADDR", "localhost:60000")

	cfg := Load()
	if cfg.ModelProvider != "gemini" {
		t.Fatalf("expected configured provider")
	}
	if cfg.SessionTTL != 45*time.Minute {
		t.Fatalf("expected configured session ttl")
	}
	if cfg.SessionCleanupEvery != 10*time.Second {
		t.Fatalf("expected configured cleanup interval")
	}
	if cfg.RedisURL != "redis://localhost:6379/0" {
		t.Fatalf("expected configured redis url")
	}
	if cfg.ToolRuntimeAddr != "localhost:60000" {
		t.Fatalf("expected configured tool runtime addr")
	}
}

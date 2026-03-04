package config

import (
	"os"
	"strings"
	"time"
)

type Config struct {
	HTTPAddr            string
	WebSocketAddr       string
	DatabaseURL         string
	RedisURL            string
	MigrationsDir       string
	MigrationsAutoApply bool
	BearerToken         string
	ModelProvider       string
	SessionTTL          time.Duration
	SessionCleanupEvery time.Duration
	ToolRuntimeAddr     string
}

func Load() Config {
	return Config{
		HTTPAddr:            getEnv("MOOS_HTTP_ADDR", ":8080"),
		WebSocketAddr:       getEnv("MOOS_WS_ADDR", ":18789"),
		DatabaseURL:         getEnv("DATABASE_URL", ""),
		RedisURL:            getEnv("REDIS_URL", ""),
		MigrationsDir:       getEnv("MOOS_MIGRATIONS_DIR", "./migrations"),
		MigrationsAutoApply: getEnvBool("MOOS_MIGRATIONS_AUTO_APPLY", false),
		BearerToken:         getEnv("MOOS_BEARER_TOKEN", ""),
		ModelProvider:       getEnv("MOOS_MODEL_PROVIDER", "anthropic"),
		SessionTTL:          getEnvDuration("MOOS_SESSION_TTL", 30*time.Minute),
		SessionCleanupEvery: getEnvDuration("MOOS_SESSION_CLEANUP_EVERY", time.Minute),
		ToolRuntimeAddr:     getEnv("MOOS_TOOL_RUNTIME_ADDR", "localhost:50052"),
	}
}

func getEnv(key string, fallback string) string {
	value, ok := os.LookupEnv(key)
	if !ok || value == "" {
		return fallback
	}
	return value
}

func getEnvBool(key string, fallback bool) bool {
	value, ok := os.LookupEnv(key)
	if !ok || strings.TrimSpace(value) == "" {
		return fallback
	}
	normalized := strings.ToLower(strings.TrimSpace(value))
	return normalized == "1" || normalized == "true" || normalized == "yes" || normalized == "on"
}

func getEnvDuration(key string, fallback time.Duration) time.Duration {
	value, ok := os.LookupEnv(key)
	if !ok || strings.TrimSpace(value) == "" {
		return fallback
	}
	parsed, err := time.ParseDuration(strings.TrimSpace(value))
	if err != nil {
		return fallback
	}
	return parsed
}

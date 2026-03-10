// Package config provides runtime configuration from environment variables.
package config

import (
	"os"
	"path/filepath"
)

// Config holds all runtime configuration.
type Config struct {
	// Store type: "file" (default), "postgres", or "memory"
	StoreType string
	// File store: path to morphism-log.jsonl
	LogPath string
	// Postgres: connection string
	DatabaseURL string
	// Registry: path to ontology.json
	RegistryPath string
	// HTTP listen address
	ListenAddr string
}

// Load reads configuration from environment variables with sensible defaults.
func Load() Config {
	c := Config{
		StoreType:    envOr("MOOS_KERNEL_STORE", "file"),
		LogPath:      envOr("MOOS_KERNEL_LOG_PATH", "data/morphism-log.jsonl"),
		DatabaseURL:  os.Getenv("MOOS_DATABASE_URL"),
		RegistryPath: os.Getenv("MOOS_KERNEL_REGISTRY_PATH"),
		ListenAddr:   envOr("MOOS_KERNEL_ADDR", ":8000"),
	}

	// Resolve log path to absolute
	if !filepath.IsAbs(c.LogPath) {
		if wd, err := os.Getwd(); err == nil {
			c.LogPath = filepath.Join(wd, c.LogPath)
		}
	}

	// Auto-detect registry if not specified
	if c.RegistryPath == "" {
		c.RegistryPath = findRegistry()
	}
	if c.RegistryPath != "" && !filepath.IsAbs(c.RegistryPath) {
		if wd, err := os.Getwd(); err == nil {
			c.RegistryPath = filepath.Join(wd, c.RegistryPath)
		}
	}

	return c
}

func envOr(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

// findRegistry searches for the ontology.json file by walking up from cwd.
func findRegistry() string {
	candidates := []string{
		".agent/knowledge_base/registry/ontology.json",
	}
	// Walk up from cwd looking for the registry
	dir, err := os.Getwd()
	if err != nil {
		return ""
	}
	for i := 0; i < 6; i++ {
		for _, c := range candidates {
			p := filepath.Join(dir, c)
			if _, err := os.Stat(p); err == nil {
				return p
			}
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			break
		}
		dir = parent
	}
	return ""
}

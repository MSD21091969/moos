// Package config loads runtime configuration from a single JSON file.
// The kernel knows nothing about the workspace layout — the installer
// generates the config file with absolute paths.
package config

import (
	"encoding/json"
	"fmt"
	"os"
)

// Config holds all runtime configuration.
type Config struct {
	// Store type: "file" or "memory".
	StoreType string `json:"store_type"`
	// File store: absolute path to the morphism log JSONL file.
	LogPath string `json:"log_path"`
	// Absolute path to the ontology.json registry.
	RegistryPath string `json:"registry_path"`
	// HTTP listen address (e.g. ":8000").
	ListenAddr string `json:"listen_addr"`
	// Seed programs applied idempotently on first boot.
	Seed []json.RawMessage `json:"seed,omitempty"`
}

// LoadFromFile reads and parses the JSON config at path.
// Returns an error if the file is missing or required fields are absent.
func LoadFromFile(path string) (Config, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return Config{}, fmt.Errorf("reading config file: %w", err)
	}
	return Parse(data)
}

// Parse decodes config JSON and validates required fields.
func Parse(data []byte) (Config, error) {
	var c Config
	if err := json.Unmarshal(data, &c); err != nil {
		return Config{}, fmt.Errorf("parsing config: %w", err)
	}
	if c.StoreType == "" {
		return Config{}, fmt.Errorf("store_type is required")
	}
	if c.StoreType != "file" && c.StoreType != "memory" {
		return Config{}, fmt.Errorf("store_type must be \"file\" or \"memory\", got %q", c.StoreType)
	}
	if c.StoreType == "file" && c.LogPath == "" {
		return Config{}, fmt.Errorf("log_path is required when store_type is \"file\"")
	}
	if c.ListenAddr == "" {
		return Config{}, fmt.Errorf("listen_addr is required")
	}
	return c, nil
}

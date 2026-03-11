package config

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
)

// Config holds kernel runtime configuration.
type Config struct {
	StoreType    string `json:"store_type"`     // "file" or "postgres"
	LogPath      string `json:"log_path"`       // JSONL file path (file store)
	RegistryPath string `json:"registry_path"`  // ontology.json path
	ListenAddr   string `json:"listen_addr"`    // e.g. ":8000"
	Seed         *Seed  `json:"seed,omitempty"` // optional boot seed
}

// Seed describes the kernel's identity morphism applied on first boot.
type Seed struct {
	Actor  string `json:"actor"`
	URN    string `json:"urn"`
	TypeID string `json:"type_id"`
}

// LoadFromFile reads JSON config from the given path.
func LoadFromFile(path string) (*Config, error) {
	data, err := os.ReadFile(filepath.Clean(path))
	if err != nil {
		return nil, fmt.Errorf("config: read %s: %w", path, err)
	}
	return Parse(data)
}

// Parse decodes a JSON config from raw bytes.
func Parse(data []byte) (*Config, error) {
	var cfg Config
	if err := json.Unmarshal(data, &cfg); err != nil {
		return nil, fmt.Errorf("config: parse: %w", err)
	}
	if cfg.ListenAddr == "" {
		cfg.ListenAddr = ":8000"
	}
	if cfg.StoreType == "" {
		cfg.StoreType = "file"
	}
	return &cfg, nil
}

// Default returns a minimal working config suitable for dev use.
func Default() *Config {
	return &Config{
		StoreType:  "file",
		LogPath:    "data/morphism-log.jsonl",
		ListenAddr: ":8000",
	}
}

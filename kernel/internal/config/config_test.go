package config

import (
	"testing"
)

func TestParseValid(t *testing.T) {
	raw := `{
		"store_type": "file",
		"log_path": "/tmp/moos/morphism-log.jsonl",
		"registry_path": "/opt/moos/registry/ontology.json",
		"listen_addr": ":8000"
	}`
	cfg, err := Parse([]byte(raw))
	if err != nil {
		t.Fatal(err)
	}
	if cfg.StoreType != "file" {
		t.Fatalf("expected file, got %s", cfg.StoreType)
	}
	if cfg.LogPath != "/tmp/moos/morphism-log.jsonl" {
		t.Fatalf("unexpected log_path: %s", cfg.LogPath)
	}
	if cfg.ListenAddr != ":8000" {
		t.Fatalf("unexpected listen_addr: %s", cfg.ListenAddr)
	}
}

func TestParseMemoryStore(t *testing.T) {
	raw := `{"store_type":"memory","listen_addr":":9000"}`
	cfg, err := Parse([]byte(raw))
	if err != nil {
		t.Fatal(err)
	}
	if cfg.StoreType != "memory" {
		t.Fatalf("expected memory, got %s", cfg.StoreType)
	}
}

func TestParseMissingStoreType(t *testing.T) {
	raw := `{"listen_addr":":8000"}`
	_, err := Parse([]byte(raw))
	if err == nil {
		t.Fatal("expected error for missing store_type")
	}
}

func TestParseMissingListenAddr(t *testing.T) {
	raw := `{"store_type":"memory"}`
	_, err := Parse([]byte(raw))
	if err == nil {
		t.Fatal("expected error for missing listen_addr")
	}
}

func TestParseMissingLogPathForFile(t *testing.T) {
	raw := `{"store_type":"file","listen_addr":":8000"}`
	_, err := Parse([]byte(raw))
	if err == nil {
		t.Fatal("expected error for missing log_path with file store")
	}
}

func TestParseInvalidStoreType(t *testing.T) {
	raw := `{"store_type":"redis","listen_addr":":8000"}`
	_, err := Parse([]byte(raw))
	if err == nil {
		t.Fatal("expected error for invalid store_type")
	}
}

func TestParseSeedPrograms(t *testing.T) {
	raw := `{
		"store_type": "memory",
		"listen_addr": ":8000",
		"seed": [
			{"actor":"urn:a","envelopes":[{"type":"ADD","add":{"urn":"urn:x","kind":"K","stratum":"S2"}}]}
		]
	}`
	cfg, err := Parse([]byte(raw))
	if err != nil {
		t.Fatal(err)
	}
	if len(cfg.Seed) != 1 {
		t.Fatalf("expected 1 seed program, got %d", len(cfg.Seed))
	}
}

func TestParseInvalidJSON(t *testing.T) {
	_, err := Parse([]byte(`not json`))
	if err == nil {
		t.Fatal("expected error for invalid JSON")
	}
}

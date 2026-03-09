package main

import (
	"log"
	"net/http"
	"os"
	"path/filepath"

	"moos/platform/kernel/internal/core"
	"moos/platform/kernel/internal/httpapi"
	"moos/platform/kernel/internal/shell"
)

func main() {
	httpPort := envOrDefault("MOOS_HTTP_PORT", "8000")
	logPath := envOrDefault("MOOS_KERNEL_LOG_PATH", filepath.FromSlash("./data/morphism-log.jsonl"))
	registryPath := envOrDefault("MOOS_KERNEL_REGISTRY_PATH", defaultRegistryPath())
	storeKind := envOrDefault("MOOS_KERNEL_STORE", "file")

	registry, err := shell.LoadRegistry(registryPath)
	if err != nil {
		log.Fatalf("kernel registry load failed: %v", err)
	}

	store, err := openStore(storeKind, logPath, os.Getenv("MOOS_DATABASE_URL"))
	if err != nil {
		log.Fatalf("kernel store initialization failed: %v", err)
	}

	runtime, err := shell.NewRuntimeWithConfig(shell.RuntimeConfig{Store: store, Registry: registry})
	if err != nil {
		log.Fatalf("kernel startup failed: %v", err)
	}
	defer runtime.Close()

	seedKernel(runtime, storeKind)

	server := httpapi.New(runtime)
	address := ":" + httpPort
	log.Printf("moos kernel MVP listening on %s using %s store", address, storeKind)
	if err := http.ListenAndServe(address, server.Handler()); err != nil {
		log.Fatalf("kernel server failed: %v", err)
	}
}

func openStore(storeKind string, logPath string, databaseURL string) (shell.Store, error) {
	switch storeKind {
	case "", "file":
		return shell.LogStore{Path: logPath}, nil
	case "postgres":
		return shell.NewPostgresStore(databaseURL)
	default:
		return nil, &os.PathError{Op: "openStore", Path: storeKind, Err: os.ErrInvalid}
	}
}

func envOrDefault(key string, fallback string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return fallback
}

func seedKernel(runtime *shell.Runtime, storeKind string) {
	const actor = "urn:moos:kernel:self"
	const kernelURN core.URN = "urn:moos:kernel:wave-0"

	seed := func(envelope core.Envelope) {
		if err := runtime.SeedIfAbsent(envelope); err != nil {
			log.Printf("seed skipped (%s %s): %v", envelope.Type, envelope.Actor, err)
		}
	}

	seed(core.Envelope{
		Type:  core.MorphismAdd,
		Actor: actor,
		Add: &core.AddPayload{
			URN:     kernelURN,
			Kind:    "Kernel",
			Stratum: core.StratumMaterialized,
			Payload: map[string]any{"wave": 0, "store": storeKind, "lang": "go"},
		},
	})

	features := []struct {
		urn  string
		name string
	}{
		{"urn:moos:feature:pure-graph-core", "Pure Graph Core"},
		{"urn:moos:feature:append-only-log", "Append-Only Log"},
		{"urn:moos:feature:http-api", "HTTP API"},
		{"urn:moos:feature:program-composition", "Program Composition"},
		{"urn:moos:feature:semantic-registry", "Semantic Registry"},
		{"urn:moos:feature:hydration-materialize", "Hydration Materialize"},
	}

	for _, f := range features {
		urn := core.URN(f.urn)
		seed(core.Envelope{
			Type:  core.MorphismAdd,
			Actor: actor,
			Add: &core.AddPayload{
				URN:     urn,
				Kind:    "Feature",
				Stratum: core.StratumMaterialized,
				Payload: map[string]any{"name": f.name, "wave": 0},
			},
		})
		seed(core.Envelope{
			Type:  core.MorphismLink,
			Actor: actor,
			Link: &core.LinkPayload{
				SourceURN:  urn,
				SourcePort: "implements",
				TargetURN:  kernelURN,
				TargetPort: "feature",
			},
		})
	}
}

func defaultRegistryPath() string {
	candidates := []string{
		filepath.FromSlash("../.agent/knowledge_base/superset/ontology.json"),
		filepath.FromSlash("../../.agent/knowledge_base/superset/ontology.json"),
		filepath.FromSlash("../../../.agent/knowledge_base/superset/ontology.json"),
		filepath.FromSlash("../../../../.agent/knowledge_base/superset/ontology.json"),
	}

	for _, candidate := range candidates {
		if _, err := os.Stat(candidate); err == nil {
			return candidate
		}
	}

	return candidates[0]
}

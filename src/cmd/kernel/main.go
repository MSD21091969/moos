// Entrypoint for the mo:os categorical kernel.
//
// Boot sequence:
//  1. Load config from environment
//  2. Open store (file or postgres)
//  3. Load operad registry from ontology.json
//  4. Create runtime (replay morphism log → reconstruct state)
//  5. Seed kernel identity (idempotent)
//  6. Start HTTP server
package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"

	"moos/src/internal/cat"
	"moos/src/internal/config"
	"moos/src/internal/functor"
	"moos/src/internal/operad"
	"moos/src/internal/shell"
	"moos/src/internal/transport"
)

func main() {
	cfg := config.Load()
	log.Printf("[boot] store=%s addr=%s", cfg.StoreType, cfg.ListenAddr)

	// 1. Open store
	store, cleanup, err := openStore(cfg)
	if err != nil {
		log.Fatalf("[boot] store: %v", err)
	}
	defer cleanup()

	// 2. Load operad registry
	var registry *operad.Registry
	if cfg.RegistryPath != "" {
		registry, err = operad.LoadRegistry(cfg.RegistryPath)
		if err != nil {
			log.Printf("[boot] WARNING: registry load failed: %v", err)
		} else {
			log.Printf("[boot] registry loaded: %d kinds from %s", len(registry.Kinds), cfg.RegistryPath)
		}
	} else {
		log.Printf("[boot] no registry path — running without type constraints")
	}

	// 3. Create runtime (replay)
	rt, err := shell.NewRuntime(store, registry)
	if err != nil {
		log.Fatalf("[boot] runtime: %v", err)
	}

	// 4. Seed kernel identity
	seedKernel(rt)

	// 5. Start HTTP server
	uiLens := functor.MockUILens{}
	srv := transport.NewServer(rt, uiLens)

	// Graceful shutdown
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	go func() {
		if err := srv.ListenAndServe(cfg.ListenAddr); err != nil && err != http.ErrServerClosed {
			log.Fatalf("[transport] %v", err)
		}
	}()

	<-ctx.Done()
	log.Printf("[boot] shutting down...")
	shutdownCtx, cancel := context.WithTimeout(context.Background(), 5e9) // 5s
	defer cancel()
	srv.Shutdown(shutdownCtx)
	log.Printf("[boot] done")
}

func openStore(cfg config.Config) (shell.Store, func(), error) {
	switch cfg.StoreType {
	case "file":
		s, err := shell.NewLogStore(cfg.LogPath)
		if err != nil {
			return nil, nil, err
		}
		log.Printf("[boot] file store: %s", cfg.LogPath)
		return s, func() {}, nil
	case "postgres":
		if cfg.DatabaseURL == "" {
			return nil, nil, fmt.Errorf("MOOS_DATABASE_URL required for postgres store")
		}
		s, err := shell.NewPostgresStore(context.Background(), cfg.DatabaseURL)
		if err != nil {
			return nil, nil, err
		}
		log.Printf("[boot] postgres store connected")
		return s, func() { s.Close() }, nil
	case "memory":
		s := shell.NewMemStore()
		log.Printf("[boot] in-memory store (ephemeral)")
		return s, func() {}, nil
	default:
		return nil, nil, fmt.Errorf("unknown store type: %s", cfg.StoreType)
	}
}

const (
	kernelActor = cat.URN("urn:moos:kernel:self")
	kernelNode  = cat.URN("urn:moos:kernel:wave-0")
)

// seedKernel registers the kernel's own identity in the graph.
// Idempotent — uses SeedIfAbsent so repeated boots are no-ops.
//
// Fix F4: ADD the actor node FIRST so subsequent morphisms have a valid actor.
// Fix F1: Use Kind=Kernel (not a generic kind).
func seedKernel(rt *shell.Runtime) {
	seeds := []cat.Envelope{
		// F4: Actor node must exist before it can be referenced
		{Type: cat.ADD, Actor: kernelActor, Add: &cat.AddPayload{
			URN: kernelActor, Kind: "Actor", Stratum: cat.S2,
			Payload: map[string]any{"label": "Kernel Self-Actor"},
		}},
		// F1: Kernel identity node with correct Kind=Kernel
		{Type: cat.ADD, Actor: kernelActor, Add: &cat.AddPayload{
			URN: kernelNode, Kind: "Kernel", Stratum: cat.S2,
			Payload: map[string]any{"label": "mo:os Kernel — Wave 0"},
		}},
		// Feature nodes
		{Type: cat.ADD, Actor: kernelActor, Add: &cat.AddPayload{
			URN: "urn:moos:feature:catamorphism", Kind: "Feature", Stratum: cat.S2,
			Payload: map[string]any{"label": "Σ-catamorphism (fold)"},
		}},
		{Type: cat.ADD, Actor: kernelActor, Add: &cat.AddPayload{
			URN: "urn:moos:feature:morphism-log", Kind: "Feature", Stratum: cat.S2,
			Payload: map[string]any{"label": "Append-only morphism log"},
		}},
		{Type: cat.ADD, Actor: kernelActor, Add: &cat.AddPayload{
			URN: "urn:moos:feature:semantic-registry", Kind: "Feature", Stratum: cat.S2,
			Payload: map[string]any{"label": "Operad semantic registry"},
		}},
		{Type: cat.ADD, Actor: kernelActor, Add: &cat.AddPayload{
			URN: "urn:moos:feature:http-api", Kind: "RuntimeSurface", Stratum: cat.S2,
			Payload: map[string]any{"label": "HTTP transport API"},
		}},
		{Type: cat.ADD, Actor: kernelActor, Add: &cat.AddPayload{
			URN: "urn:moos:feature:explorer", Kind: "Feature", Stratum: cat.S2,
			Payload: map[string]any{"label": "UI_Lens explorer"},
		}},
		{Type: cat.ADD, Actor: kernelActor, Add: &cat.AddPayload{
			URN: "urn:moos:feature:hydration", Kind: "Feature", Stratum: cat.S2,
			Payload: map[string]any{"label": "Strata materialization pipeline"},
		}},
		// LINK features to kernel
		{Type: cat.LINK, Actor: kernelActor, Link: &cat.LinkPayload{
			SourceURN: kernelNode, SourcePort: "implements",
			TargetURN: "urn:moos:feature:catamorphism", TargetPort: "implements",
		}},
		{Type: cat.LINK, Actor: kernelActor, Link: &cat.LinkPayload{
			SourceURN: kernelNode, SourcePort: "implements",
			TargetURN: "urn:moos:feature:morphism-log", TargetPort: "implements",
		}},
		{Type: cat.LINK, Actor: kernelActor, Link: &cat.LinkPayload{
			SourceURN: kernelNode, SourcePort: "implements",
			TargetURN: "urn:moos:feature:semantic-registry", TargetPort: "implements",
		}},
		{Type: cat.LINK, Actor: kernelActor, Link: &cat.LinkPayload{
			SourceURN: kernelNode, SourcePort: "implements",
			TargetURN: "urn:moos:feature:http-api", TargetPort: "implements",
		}},
		{Type: cat.LINK, Actor: kernelActor, Link: &cat.LinkPayload{
			SourceURN: kernelNode, SourcePort: "implements",
			TargetURN: "urn:moos:feature:explorer", TargetPort: "implements",
		}},
		{Type: cat.LINK, Actor: kernelActor, Link: &cat.LinkPayload{
			SourceURN: kernelNode, SourcePort: "implements",
			TargetURN: "urn:moos:feature:hydration", TargetPort: "implements",
		}},
	}

	for _, env := range seeds {
		if err := rt.SeedIfAbsent(env); err != nil {
			log.Printf("[seed] WARNING: %v", err)
		}
	}

	log.Printf("[seed] kernel identity seeded: %d nodes, %d wires",
		len(rt.Nodes()), len(rt.Wires()))
}

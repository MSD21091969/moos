// Entrypoint for the mo:os kernel v2.
//
// Boot sequence:
//  1. Parse --config flag
//  2. Load config from JSON file
//  3. Load operad registry (if configured)
//  4. Open store (file or memory)
//  5. Create runtime (replay morphism log → reconstruct state)
//  6. Apply seed (idempotent)
//  7. Start HTTP server
package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"

	"moos/kernel_v2/internal/cat"
	"moos/kernel_v2/internal/config"
	"moos/kernel_v2/internal/operad"
	"moos/kernel_v2/internal/shell"
	"moos/kernel_v2/internal/transport"
)

func main() {
	configPath := flag.String("config", "", "path to config.json (required)")
	flag.Parse()

	if *configPath == "" {
		fmt.Fprintln(os.Stderr, "usage: moos --config <path>")
		os.Exit(1)
	}

	cfg, err := config.LoadFromFile(*configPath)
	if err != nil {
		log.Fatalf("[boot] config: %v", err)
	}
	log.Printf("[boot] store=%s addr=%s", cfg.StoreType, cfg.ListenAddr)

	// 1. Load operad registry
	var registry *operad.Registry
	if cfg.RegistryPath != "" {
		data, err := os.ReadFile(cfg.RegistryPath)
		if err != nil {
			log.Printf("[boot] WARNING: registry read failed: %v", err)
		} else {
			registry, err = operad.LoadRegistry(data)
			if err != nil {
				log.Printf("[boot] WARNING: registry load failed: %v", err)
			} else {
				log.Printf("[boot] registry loaded: %d types from %s", len(registry.Types), cfg.RegistryPath)
			}
		}
	} else {
		log.Printf("[boot] no registry path — running without type constraints")
	}

	// 2. Open store
	store, err := openStore(cfg)
	if err != nil {
		log.Fatalf("[boot] store: %v", err)
	}

	// 3. Create runtime (replay)
	rt, err := shell.NewRuntime(store, registry)
	if err != nil {
		log.Fatalf("[boot] runtime: %v", err)
	}

	// 4. Apply seed
	seedKernel(rt, cfg)

	// 5. Start HTTP server
	srv := transport.NewServer(rt)

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

func openStore(cfg *config.Config) (shell.Store, error) {
	switch cfg.StoreType {
	case "file":
		s, err := shell.NewLogStore(cfg.LogPath)
		if err != nil {
			return nil, err
		}
		log.Printf("[boot] file store: %s", cfg.LogPath)
		return s, nil
	case "memory":
		s := shell.NewMemStore()
		log.Printf("[boot] in-memory store (ephemeral)")
		return s, nil
	default:
		return nil, fmt.Errorf("unknown store type: %s", cfg.StoreType)
	}
}

// seedKernel applies the configured seed morphism on first boot (idempotent).
func seedKernel(rt *shell.Runtime, cfg *config.Config) {
	if cfg.Seed == nil {
		return
	}
	env := cat.Envelope{
		Type:  cat.ADD,
		Actor: cat.URN(cfg.Seed.Actor),
		Add: &cat.AddPayload{
			URN:    cat.URN(cfg.Seed.URN),
			TypeID: cat.TypeID(cfg.Seed.TypeID),
		},
	}
	if err := rt.SeedIfAbsent(env); err != nil {
		log.Printf("[seed] WARNING: %v", err)
		return
	}
	log.Printf("[seed] kernel seeded: %s (type=%s)", cfg.Seed.URN, cfg.Seed.TypeID)
}

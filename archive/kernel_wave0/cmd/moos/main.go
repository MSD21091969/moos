// Entrypoint for the mo:os categorical kernel.
//
// Boot sequence:
//  1. Parse --config flag
//  2. Load config from JSON file
//  3. Load operad registry (if configured)
//  4. Open store (file or memory)
//  5. Create runtime (replay morphism log → reconstruct state)
//  6. Apply seed programs (idempotent)
//  7. Start HTTP server
package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"strings"
	"syscall"

	"moos/internal/cat"
	"moos/internal/config"
	"moos/internal/functor"
	"moos/internal/operad"
	"moos/internal/shell"
	"moos/internal/transport"
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
				log.Printf("[boot] registry loaded: %d kinds from %s", len(registry.Kinds), cfg.RegistryPath)
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

	// 4. Apply seed programs from config
	applySeed(rt, cfg)

	// 5. Start HTTP server
	uiLens := functor.MockUILens{}
	srv := transport.NewServer(rt, uiLens)

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

func openStore(cfg config.Config) (shell.Store, error) {
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

// applySeed decodes and applies seed programs from the config.
// Each seed entry is a cat.Program JSON. Applied idempotently via SeedIfAbsent.
func applySeed(rt *shell.Runtime, cfg config.Config) {
	if len(cfg.Seed) == 0 {
		return
	}
	for i, raw := range cfg.Seed {
		var prog cat.Program
		if err := json.Unmarshal(raw, &prog); err != nil {
			log.Printf("[seed] WARNING: seed[%d] parse error: %v", i, err)
			continue
		}
		for _, env := range prog.Envelopes {
			if skip, reason := shouldSkipSeedEnvelope(env); skip {
				log.Printf("[seed] INFO: seed[%d] skipped: %s", i, reason)
				continue
			}
			if env.Actor == "" {
				env.Actor = prog.Actor
			}
			if err := rt.SeedIfAbsent(env); err != nil {
				log.Printf("[seed] WARNING: seed[%d] envelope: %v", i, err)
			}
		}
	}
	log.Printf("[seed] applied %d programs → %d nodes, %d wires",
		len(cfg.Seed), len(rt.Nodes()), len(rt.Wires()))
}

func shouldSkipSeedEnvelope(env cat.Envelope) (bool, string) {
	switch env.Type {
	case cat.ADD:
		if env.Add == nil {
			return false, ""
		}
		if strings.HasPrefix(string(env.Add.URN), "urn:moos:cat:") {
			return true, fmt.Sprintf("glossary seed blocked (urn=%s)", env.Add.URN)
		}
		if string(env.Add.Kind) == "Kernel" || string(env.Add.Kind) == "Feature" {
			return true, fmt.Sprintf("legacy kind blocked (urn=%s kind=%s)", env.Add.URN, env.Add.Kind)
		}
		if isLegacySystemURN(env.Add.URN) {
			return true, fmt.Sprintf("legacy system urn blocked (urn=%s)", env.Add.URN)
		}
	case cat.LINK:
		if env.Link == nil {
			return false, ""
		}
		if isGlossaryURN(env.Link.SourceURN) || isGlossaryURN(env.Link.TargetURN) {
			return true, "glossary wire blocked"
		}
		if isLegacySystemURN(env.Link.SourceURN) || isLegacySystemURN(env.Link.TargetURN) {
			return true, "legacy system wire blocked"
		}
	case cat.MUTATE:
		if env.Mutate == nil {
			return false, ""
		}
		if isGlossaryURN(env.Mutate.URN) {
			return true, "glossary mutate blocked"
		}
		if isLegacySystemURN(env.Mutate.URN) {
			return true, "legacy system mutate blocked"
		}
	case cat.UNLINK:
		if env.Unlink == nil {
			return false, ""
		}
		if isGlossaryURN(env.Unlink.SourceURN) || isGlossaryURN(env.Unlink.TargetURN) {
			return true, "glossary unlink blocked"
		}
		if isLegacySystemURN(env.Unlink.SourceURN) || isLegacySystemURN(env.Unlink.TargetURN) {
			return true, "legacy system unlink blocked"
		}
	}
	return false, ""
}

func isGlossaryURN(urn cat.URN) bool {
	return strings.HasPrefix(string(urn), "urn:moos:cat:")
}

func isLegacySystemURN(urn cat.URN) bool {
	s := string(urn)
	if strings.HasPrefix(s, "urn:moos:feature:") {
		return true
	}
	return s == "urn:moos:kernel:wave-0"
}

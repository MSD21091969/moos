// Entrypoint for the mo:os kernel v2.
//
// Boot sequence:
//  1. Parse --config or --kb flag (--config wins if both provided)
//  2. Load config (from file or derived from KB root)
//  3. Load operad registry (if configured)
//  4. Open store (file or memory)
//  5. Create runtime (replay morphism log → reconstruct state)
//  6. Apply seed (idempotent)
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
	"path/filepath"
	"strings"
	"syscall"

	"moos/platform/kernel/internal/cat"
	"moos/platform/kernel/internal/config"
	"moos/platform/kernel/internal/hydration"
	"moos/platform/kernel/internal/mcp"
	"moos/platform/kernel/internal/operad"
	"moos/platform/kernel/internal/shell"
	"moos/platform/kernel/internal/transport"
)

func main() {
	configPath := flag.String("config", "", "path to config.json")
	kbPath := flag.String("kb", "", "path to knowledge base root (derives registry + config)")
	hydrateFlag := flag.Bool("hydrate", false, "auto-apply Tier-2 instance hydration on boot (requires --kb)")
	mcpStdioFlag := flag.Bool("mcp-stdio", false, "enable newline-delimited JSON-RPC over stdin/stdout")
	flag.Parse()

	var (
		cfg *config.Config
		err error
	)
	switch {
	case *configPath != "":
		cfg, err = config.LoadFromFile(*configPath)
		if err != nil {
			log.Fatalf("[boot] config: %v", err)
		}
	case *kbPath != "":
		cfg, err = config.LoadFromKB(*kbPath)
		if err != nil {
			log.Fatalf("[boot] kb: %v", err)
		}
		log.Printf("[boot] kb=%s", *kbPath)
	default:
		fmt.Fprintln(os.Stderr, "usage: moos --config <path> | --kb <kb-root>")
		os.Exit(1)
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
	seedAgentNodes(rt)
	seedSourceNodes(rt, *kbPath, rootSeedURN(cfg))

	// 5. Optionally hydrate Tier-2 instance files from the KB.
	if *hydrateFlag && *kbPath != "" {
		if err := hydration.HydrateAll(*kbPath, "", rt); err != nil {
			log.Printf("[boot] hydration warning: %v", err)
		}
	}

	// 6. Start HTTP server
	srv := transport.NewServer(rt, *kbPath)

	// 7. Start MCP bridge
	mcpSrv := mcp.NewServer(rt)

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	go func() {
		if err := srv.ListenAndServe(cfg.ListenAddr); err != nil && err != http.ErrServerClosed {
			log.Fatalf("[transport] %v", err)
		}
	}()
	go func() {
		if err := mcpSrv.ListenAndServe(":8080"); err != nil && err != http.ErrServerClosed {
			log.Fatalf("[mcp] %v", err)
		}
	}()
	if *mcpStdioFlag {
		go func() {
			log.Printf("[mcp] stdio transport enabled")
			if err := mcpSrv.HandleStdio(ctx, os.Stdin, os.Stdout); err != nil && err != context.Canceled {
				log.Printf("[mcp-stdio] %v", err)
			}
		}()
	}

	<-ctx.Done()
	log.Printf("[boot] shutting down...")
	shutdownCtx, cancel := context.WithTimeout(context.Background(), 5e9) // 5s
	defer cancel()
	srv.Shutdown(shutdownCtx)
	mcpSrv.Shutdown(shutdownCtx)
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

// seedAgentNodes seeds the three canonical agent nodes idempotently.
// Errors are non-fatal; the kernel continues without them.
func seedAgentNodes(rt *shell.Runtime) {
	const actor = cat.URN("urn:moos:identity:kernel")
	agents := []struct{ urn, label string }{
		{"urn:moos:agent:claude-code", "Claude Code (strategic AI)"},
		{"urn:moos:agent:vscode-ai", "VS Code AI — Sonnet 4.6 (execution AI)"},
		{"urn:moos:agent:antigraviti", "Antigraviti — Gemini 3.1 Pro (UX testing AI)"},
	}
	for _, a := range agents {
		env := cat.Envelope{
			Type:  cat.ADD,
			Actor: actor,
			Add: &cat.AddPayload{
				URN:      cat.URN(a.urn),
				TypeID:   "agent_spec",
				Metadata: map[string]any{"label": a.label},
			},
		}
		if err := rt.SeedIfAbsent(env); err != nil {
			log.Printf("[seed] agent %s: %v", a.urn, err)
		}
	}
	log.Printf("[seed] agent nodes seeded")
}

type sourceSeedFile struct {
	Entries []sourceSeedEntry `json:"entries"`
}

type sourceSeedEntry struct {
	ID     string `json:"id"`
	Label  string `json:"label"`
	Domain string `json:"domain"`
	URL    string `json:"url"`
}

func rootSeedURN(cfg *config.Config) string {
	if cfg != nil && cfg.Seed != nil && strings.TrimSpace(cfg.Seed.URN) != "" {
		return cfg.Seed.URN
	}
	return "urn:moos:kernel:wave-0"
}

func seedSourceNodes(rt *shell.Runtime, kbRoot, rootURN string) {
	if strings.TrimSpace(kbRoot) == "" {
		return
	}
	path := filepath.Join(kbRoot, "superset", "sources.json")
	data, err := os.ReadFile(filepath.Clean(path))
	if err != nil {
		log.Printf("[seed] sources skipped: %v", err)
		return
	}

	var doc sourceSeedFile
	if err := json.Unmarshal(data, &doc); err != nil {
		log.Printf("[seed] sources parse skipped: %v", err)
		return
	}

	for _, src := range doc.Entries {
		urn := strings.TrimSpace(src.ID)
		if urn == "" {
			continue
		}
		label := strings.TrimSpace(src.Label)
		if label == "" {
			label = urn
		}

		if err := rt.SeedIfAbsent(cat.Envelope{
			Type:  cat.ADD,
			Actor: cat.URN("urn:moos:identity:kernel"),
			Add: &cat.AddPayload{
				URN:     cat.URN(urn),
				TypeID:  "node_container",
				Stratum: cat.S2,
				Payload: map[string]any{
					"label":  label,
					"domain": src.Domain,
					"url":    src.URL,
				},
			},
		}); err != nil {
			log.Printf("[seed] source add %s: %v", urn, err)
		}

		if strings.TrimSpace(rootURN) != "" {
			if err := rt.SeedIfAbsent(cat.Envelope{
				Type:  cat.LINK,
				Actor: cat.URN("urn:moos:identity:kernel"),
				Link: &cat.LinkPayload{
					SourceURN:  cat.URN(rootURN),
					SourcePort: "owns",
					TargetURN:  cat.URN(urn),
					TargetPort: "child",
				},
			}); err != nil {
				log.Printf("[seed] source link %s -> %s: %v", rootURN, urn, err)
			}
		}
	}

	log.Printf("[seed] source nodes seeded: %d", len(doc.Entries))
}

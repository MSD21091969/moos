// Package hydration — batch applies all Tier-2 KB instance files idempotently.
// HydrateAll encodes doctrine/install.md Programs 5–11 and uses SeedIfAbsent
// so the operation is safe to repeat on every boot.
package hydration

import (
	"fmt"
	"log"

	"moos/platform/kernel/internal/shell"
)

// InstanceOrder defines the canonical processing order for KB instance files.
// Providers must precede models; surfaces before tools; tools before agents.
var InstanceOrder = []string{
	"identities.json",
	"providers.json",
	"surfaces.json",
	"preferences.json",
	"tools.json",
	"agents.json",
	"benchmarks.json",
	"distribution.json",
	"workstation.json",
	"compute.json",
	"containers.json",
	"infra.json",
	"memory.json",
	"models.json",
	"templates.json",
	"glossary.json",
	"categories.json",
	"kinds.json",
}

// HydrateAll applies Tier-2 instance hydration for every KB instance file.
//
// kbRoot is the knowledge-base root directory (the .agent/knowledge_base path).
// rootURN is the kernel root node URN from the Seed config; if empty the
// compile-time default "urn:moos:kernel:wave-0" is used.
// rt is the live shell.Runtime that receives the resulting envelopes.
//
// Each envelope is applied via rt.SeedIfAbsent so the call is idempotent:
// duplicate nodes and wires are silently absorbed.
// Per-file errors are logged and skipped; the function returns a combined error
// only when every file that was found and parsed resulted in a failure during
// envelope application.
func HydrateAll(kbRoot, rootURN string, rt *shell.Runtime) error {
	if rootURN == "" {
		rootURN = defaultRootURN
	}

	registry := rt.Registry()
	var errs []string
	var applied, total int

	for _, filename := range InstanceOrder {
		req, err := LoadInstanceFile(kbRoot, filename, rootURN)
		if err != nil {
			log.Printf("[hydration] skip %s: %v", filename, err)
			continue
		}
		if len(req.Nodes) == 0 {
			log.Printf("[hydration] %s: no nodes, skipping", filename)
			continue
		}

		result, err := Materialize(req, registry, false)
		if err != nil {
			msg := fmt.Sprintf("%s: materialize failed: %v", filename, err)
			log.Printf("[hydration] %s", msg)
			errs = append(errs, msg)
			continue
		}

		for _, env := range result.Program.Envelopes {
			total++
			if err := rt.SeedIfAbsent(env); err != nil {
				msg := fmt.Sprintf("%s: envelope %s: %v", filename, env.Type, err)
				log.Printf("[hydration] %s", msg)
				errs = append(errs, msg)
			} else {
				applied++
			}
		}

		log.Printf("[hydration] %s: %d/%d envelopes applied (nodes=%d wires=%d)",
			filename, applied, total, result.NodeCount, result.WireCount)
	}

	if len(errs) > 0 {
		return fmt.Errorf("hydration completed with %d error(s): %s", len(errs), errs[0])
	}
	return nil
}

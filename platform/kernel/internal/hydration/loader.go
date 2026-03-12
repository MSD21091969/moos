// Package hydration — loader transforms knowledge-base instance files
// into MaterializeRequests following doctrine/install.md Programs 5–11.
// All domain mappings and port conventions are derived from the install doctrine.
package hydration

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
)

// defaultRootURN is the kernel root node seeded on first boot (Programme 4 / Tier 1).
// Used when a caller does not supply an explicit rootURN.
const defaultRootURN = "urn:moos:kernel:wave-0"

// demoSeederURN is the actor that owns Tier-2 user-space entities
// (preferences, agents) as declared in doctrine/install.md.
const demoSeederURN = "urn:moos:user:demo-seeder"

// kernelHTTPSurfaceURN is the surface used for CAN_ROUTE wires from tools.
const kernelHTTPSurfaceURN = "urn:moos:surface:kernel-http"

// instanceRecord is the top-level structure of a KB instance JSON file.
type instanceRecord struct {
	Domain  string           `json:"domain"`
	Entries []map[string]any `json:"entries"`
}

// LoadInstanceFile reads a KB instance file and returns a MaterializeRequest
// encoding Programs 5–11 (per doctrine/install.md) for the given domain.
//
// kbRoot is the knowledge-base root directory.
// filename is the bare filename inside kbRoot/instances/ (e.g. "providers.json").
// rootURN is the kernel root node URN; if empty, defaultRootURN is used.
func LoadInstanceFile(kbRoot, filename, rootURN string) (MaterializeRequest, error) {
	if rootURN == "" {
		rootURN = defaultRootURN
	}

	path := filepath.Join(kbRoot, "instances", filename)
	data, err := os.ReadFile(filepath.Clean(path))
	if err != nil {
		return MaterializeRequest{}, fmt.Errorf("read %s: %w", filename, err)
	}

	var inst instanceRecord
	if err := json.Unmarshal(data, &inst); err != nil {
		return MaterializeRequest{}, fmt.Errorf("parse %s: %w", filename, err)
	}

	req := MaterializeRequest{Actor: demoSeederURN}

	switch inst.Domain {
	case "providers":
		buildProviders(&req, inst.Entries, rootURN) // Program 5
	case "runtime_surfaces":
		buildSurfaces(&req, inst.Entries, rootURN) // Program 6
	case "preferences":
		buildPreferences(&req, inst.Entries) // Program 7 — owned by demo-seeder
	case "tools":
		buildTools(&req, inst.Entries, rootURN) // Program 8
	case "agents":
		buildAgents(&req, inst.Entries) // Program 9 — owned by demo-seeder
	case "benchmarks":
		buildBenchmarks(&req, inst.Entries, rootURN) // Program 10
	case "models":
		buildModels(&req, inst.Entries) // provider_ref → model OWNS wires
	default:
		buildGeneric(&req, inst.Entries, rootURN) // Programs 11 + generic fallback
	}

	return req, nil
}

// --- wire constructors (port names from doctrine/install.md) ---

func ownsWire(sourceURN, targetURN string) WireRequest {
	return WireRequest{
		SourceURN:  sourceURN,
		SourcePort: "owns",
		TargetURN:  targetURN,
		TargetPort: "child",
	}
}

func canRouteWire(sourceURN, targetURN string) WireRequest {
	return WireRequest{
		SourceURN:  sourceURN,
		SourcePort: "can_route",
		TargetURN:  targetURN,
		TargetPort: "transport",
	}
}

// --- domain builders ---

// buildProviders handles providers.json (Program 5).
// Each provider entry: ADD provider + LINK owns(root→provider).
// Each nested model: ADD model + LINK owns(provider→model).
func buildProviders(req *MaterializeRequest, entries []map[string]any, rootURN string) {
	for _, e := range entries {
		id := strField(e, "id")
		typeID := strField(e, "type_id")
		if id == "" || typeID == "" {
			continue
		}
		req.Nodes = append(req.Nodes, NodeRequest{
			URN:     id,
			TypeID:  typeID,
			Payload: entryPayload(e),
		})
		req.Wires = append(req.Wires, ownsWire(rootURN, id))

		// Nested models array within the provider entry.
		models, _ := e["models"].([]any)
		for _, m := range models {
			model, ok := m.(map[string]any)
			if !ok {
				continue
			}
			mid := strField(model, "id")
			mtypeID := strField(model, "type_id")
			if mid == "" || mtypeID == "" {
				continue
			}
			req.Nodes = append(req.Nodes, NodeRequest{
				URN:     mid,
				TypeID:  mtypeID,
				Payload: entryPayload(model),
			})
			req.Wires = append(req.Wires, ownsWire(id, mid))
		}
	}
}

// buildSurfaces handles surfaces.json (Program 6).
// Each surface: ADD surface + LINK owns(root→surface).
func buildSurfaces(req *MaterializeRequest, entries []map[string]any, rootURN string) {
	for _, e := range entries {
		id := strField(e, "id")
		typeID := strField(e, "type_id")
		if id == "" || typeID == "" {
			continue
		}
		req.Nodes = append(req.Nodes, NodeRequest{
			URN:     id,
			TypeID:  typeID,
			Stratum: strField(e, "stratum"),
			Payload: entryPayload(e),
		})
		req.Wires = append(req.Wires, ownsWire(rootURN, id))
	}
}

// buildPreferences handles preferences.json (Program 7).
// Each pref: ADD pref + LINK owns(demo-seeder→pref) [NOT root].
func buildPreferences(req *MaterializeRequest, entries []map[string]any) {
	for _, e := range entries {
		id := strField(e, "id")
		typeID := strField(e, "type_id")
		if id == "" || typeID == "" {
			continue
		}
		req.Nodes = append(req.Nodes, NodeRequest{
			URN:     id,
			TypeID:  typeID,
			Payload: entryPayload(e),
		})
		req.Wires = append(req.Wires, ownsWire(demoSeederURN, id))
	}
}

// buildTools handles tools.json (Program 8).
// Each tool: ADD tool + LINK owns(root→tool) + LINK can_route(tool→kernel-http).
func buildTools(req *MaterializeRequest, entries []map[string]any, rootURN string) {
	for _, e := range entries {
		id := strField(e, "id")
		typeID := strField(e, "type_id")
		if id == "" || typeID == "" {
			continue
		}
		req.Nodes = append(req.Nodes, NodeRequest{
			URN:     id,
			TypeID:  typeID,
			Payload: entryPayload(e),
		})
		req.Wires = append(req.Wires, ownsWire(rootURN, id))
		req.Wires = append(req.Wires, canRouteWire(id, kernelHTTPSurfaceURN))
	}
}

// buildAgents handles agents.json (Program 9).
// Each agent: ADD agent + LINK owns(demo-seeder→agent) + LINK can_route(agent→each tool).
func buildAgents(req *MaterializeRequest, entries []map[string]any) {
	for _, e := range entries {
		id := strField(e, "id")
		typeID := strField(e, "type_id")
		if id == "" || typeID == "" {
			continue
		}
		req.Nodes = append(req.Nodes, NodeRequest{
			URN:     id,
			TypeID:  typeID,
			Payload: entryPayload(e),
		})
		req.Wires = append(req.Wires, ownsWire(demoSeederURN, id))

		toolRouting, _ := e["tool_routing"].([]any)
		for _, t := range toolRouting {
			toolURN, ok := t.(string)
			if !ok || toolURN == "" {
				continue
			}
			req.Wires = append(req.Wires, canRouteWire(id, toolURN))
		}
	}
}

// buildBenchmarks handles benchmarks.json (Program 10).
// benchmark_suite: ADD suite + LINK owns(root→suite) + LINK owns(suite→each task URN).
// benchmark_task:  ADD task only (task URN already referenced by suite).
func buildBenchmarks(req *MaterializeRequest, entries []map[string]any, rootURN string) {
	for _, e := range entries {
		id := strField(e, "id")
		typeID := strField(e, "type_id")
		if id == "" || typeID == "" {
			continue
		}
		req.Nodes = append(req.Nodes, NodeRequest{
			URN:     id,
			TypeID:  typeID,
			Payload: entryPayload(e),
		})
		switch typeID {
		case "benchmark_suite":
			req.Wires = append(req.Wires, ownsWire(rootURN, id))
			tasks, _ := e["tasks"].([]any)
			for _, t := range tasks {
				taskURN, ok := t.(string)
				if !ok || taskURN == "" {
					continue
				}
				req.Wires = append(req.Wires, ownsWire(id, taskURN))
			}
		case "benchmark_task":
			// task is wired to suite via suite.tasks — no additional base wire here
		}
	}
}

// buildModels handles models.json.
// Each model: ADD model + LINK owns(provider_ref→model) using the entry's provider_ref field.
func buildModels(req *MaterializeRequest, entries []map[string]any) {
	for _, e := range entries {
		id := strField(e, "id")
		typeID := strField(e, "type_id")
		if id == "" || typeID == "" {
			continue
		}
		req.Nodes = append(req.Nodes, NodeRequest{
			URN:     id,
			TypeID:  typeID,
			Stratum: strField(e, "stratum"),
			Payload: entryPayload(e),
		})
		providerRef := strField(e, "provider_ref")
		if providerRef != "" {
			req.Wires = append(req.Wires, ownsWire(providerRef, id))
		}
	}
}

// buildGeneric handles distribution.json, workstation.json, compute.json, and any
// other domains without a specific Program number (Program 11 + fallback).
// Each entry: ADD node + LINK owns(root→node).
func buildGeneric(req *MaterializeRequest, entries []map[string]any, rootURN string) {
	for _, e := range entries {
		id := strField(e, "id")
		typeID := strField(e, "type_id")
		if id == "" || typeID == "" {
			continue
		}
		req.Nodes = append(req.Nodes, NodeRequest{
			URN:     id,
			TypeID:  typeID,
			Stratum: strField(e, "stratum"),
			Payload: entryPayload(e),
		})
		req.Wires = append(req.Wires, ownsWire(rootURN, id))
	}
}

// --- utilities ---

// strField safely extracts a string value from a map.
func strField(m map[string]any, key string) string {
	v, _ := m[key].(string)
	return v
}

// entryPayload returns a shallow copy of the entry map with structural fields removed.
// The payload is stored as the node's state_payload in the graph.
func entryPayload(entry map[string]any) map[string]any {
	p := make(map[string]any, len(entry))
	for k, v := range entry {
		p[k] = v
	}
	delete(p, "id")
	delete(p, "type_id")
	delete(p, "stratum")
	return p
}

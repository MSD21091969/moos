// Port saturation analysis — read-path projection over graph state × operad registry.
//
// For each node, computes per-port wire counts against the operad-defined port
// signatures. Identifies gaps (0-wire ports) and saturation (actual >= defined).
//
// This is a LENS concern (read-only projection), not an operad concern (validation).
// The operad defines what COULD be wired; saturation measures what IS wired.
package lens

import (
	"sort"

	"moos/platform/kernel/internal/cat"
	"moos/platform/kernel/internal/operad"
)

// PortSaturation describes the wiring status of a single port on a node.
type PortSaturation struct {
	Direction      string   `json:"direction"`
	DefinedTargets int      `json:"defined_targets"`
	ActualWires    int      `json:"actual_wires"`
	Saturated      bool     `json:"saturated"`
	WireKeys       []string `json:"wires"`
}

// NodeSaturation describes the aggregate wiring status of all ports on a node.
type NodeSaturation struct {
	TypeID       cat.TypeID                    `json:"type_id"`
	Ports        map[cat.Port]PortSaturation   `json:"ports"`
	TotalDefined int                           `json:"total_defined"`
	TotalWired   int                           `json:"total_wired"`
	Gaps         []cat.Port                    `json:"gaps"`
}

// ComputeSaturation analyses every node in state against the operad registry.
// Nodes whose TypeID has no TypeSpec in the registry are omitted from output.
// Result is deterministic: Gaps and WireKeys are sorted.
func ComputeSaturation(state cat.GraphState, reg *operad.Registry) map[cat.URN]NodeSaturation {
	if reg == nil {
		return map[cat.URN]NodeSaturation{}
	}

	// Build wire index: (urn, port, direction) → []wireKey
	type portKey struct {
		urn  cat.URN
		port cat.Port
		dir  string // "out" for source side, "in" for target side
	}
	wireIndex := map[portKey][]string{}
	for key, w := range state.Wires {
		wireIndex[portKey{w.SourceURN, w.SourcePort, "out"}] = append(
			wireIndex[portKey{w.SourceURN, w.SourcePort, "out"}], key)
		wireIndex[portKey{w.TargetURN, w.TargetPort, "in"}] = append(
			wireIndex[portKey{w.TargetURN, w.TargetPort, "in"}], key)
	}

	out := make(map[cat.URN]NodeSaturation, len(state.Nodes))
	for urn, node := range state.Nodes {
		spec, ok := reg.Types[node.TypeID]
		if !ok || len(spec.Ports) == 0 {
			continue
		}

		ns := NodeSaturation{
			TypeID: node.TypeID,
			Ports:  make(map[cat.Port]PortSaturation, len(spec.Ports)),
		}

		for port, ps := range spec.Ports {
			pk := portKey{urn, port, ps.Direction}
			wires := wireIndex[pk]

			// Sort wire keys for determinism.
			sorted := make([]string, len(wires))
			copy(sorted, wires)
			sort.Strings(sorted)

			defined := len(ps.Targets)
			actual := len(wires)
			saturated := actual >= defined && defined > 0

			ns.Ports[port] = PortSaturation{
				Direction:      ps.Direction,
				DefinedTargets: defined,
				ActualWires:    actual,
				Saturated:      saturated,
				WireKeys:       sorted,
			}

			ns.TotalDefined += defined
			ns.TotalWired += actual

			if actual == 0 {
				ns.Gaps = append(ns.Gaps, port)
			}
		}

		// Sort gaps for determinism.
		sort.Slice(ns.Gaps, func(i, j int) bool { return ns.Gaps[i] < ns.Gaps[j] })

		out[urn] = ns
	}

	return out
}

// ComputeNodeSaturation computes saturation for a single node.
// Returns the result and true if the node exists and has a TypeSpec, otherwise false.
func ComputeNodeSaturation(state cat.GraphState, reg *operad.Registry, urn cat.URN) (NodeSaturation, bool) {
	if reg == nil {
		return NodeSaturation{}, false
	}
	node, exists := state.Nodes[urn]
	if !exists {
		return NodeSaturation{}, false
	}
	spec, ok := reg.Types[node.TypeID]
	if !ok || len(spec.Ports) == 0 {
		return NodeSaturation{}, false
	}

	// Single-node: just filter the full computation would be wasteful.
	// Build a mini-state with only the relevant node.
	full := ComputeSaturation(state, reg)
	ns, found := full[urn]
	return ns, found
}

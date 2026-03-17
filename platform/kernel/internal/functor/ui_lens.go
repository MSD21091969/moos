// FUN02 — UI_Lens functor.
//
// F: C → V (CAT01 → CAT15)
//
// Structure-preserving map from the universal graph category to the visual
// category. Objects (Nodes) map to UINodes; morphisms (Wires) map to UIEdges.
// Output lives at S4 (Projected) — NEVER ground truth.
//
// Position is a derived property: category-grid layout from broadCategory × stratum.
// BroadCategory is derived from TypeID via the ontology's groupings.
package functor

import (
	"sort"

	"moos/platform/kernel/internal/cat"
)

// UINode is an object in the visual category V.
// F(Node) = UINode — preserves URN identity, TypeID classification, stratum level.
type UINode struct {
	ID            string         `json:"id"`
	Kind          string         `json:"kind"`           // string(Node.TypeID)
	BroadCategory string         `json:"broad_category"` // ontology grouping
	Stratum       string         `json:"stratum"`
	Label         string         `json:"label"`
	X             float64        `json:"x"`
	Y             float64        `json:"y"`
	Data          map[string]any `json:"data,omitempty"`
}

// UIEdge is a morphism in the visual category V.
// F(Wire) = UIEdge — preserves source/target URN and port topology.
type UIEdge struct {
	ID         string `json:"id"`
	Source     string `json:"source"`
	Target     string `json:"target"`
	SourcePort string `json:"source_port"`
	TargetPort string `json:"target_port"`
	Label      string `json:"label"`
}

// UIProjection is the codomain object of FUN02: F(GraphState) → UIProjection.
type UIProjection struct {
	Nodes []UINode `json:"nodes"`
	Edges []UIEdge `json:"edges"`
}

// UILens implements the FUN02 render functor.
type UILens struct{}

// Name returns the functor identifier per ontology convention.
func (u UILens) Name() string { return "FUN02_ui_lens" }

// Project applies the functor: GraphState → UIProjection.
// Objects map to UINodes; morphisms map to UIEdges.
// Deterministic output: nodes and edges are sorted by ID.
func (u UILens) Project(state cat.GraphState) (any, error) {
	return u.ProjectUI(state), nil
}

// ProjectUI is the typed projection for direct use.
func (u UILens) ProjectUI(state cat.GraphState) UIProjection {
	// Sort URNs first for deterministic bucket ordering.
	urns := make([]cat.URN, 0, len(state.Nodes))
	for urn := range state.Nodes {
		urns = append(urns, urn)
	}
	sort.Slice(urns, func(i, j int) bool { return urns[i] < urns[j] })

	bucketCount := map[string]int{}
	nodes := make([]UINode, 0, len(state.Nodes))
	for _, urn := range urns {
		n := state.Nodes[urn]
		bk := broadCategory(n.TypeID) + ":" + string(n.Stratum)
		idx := bucketCount[bk]
		bucketCount[bk]++
		x, y := categoryGridPosition(n.TypeID, string(n.Stratum), idx)
		label := extractLabel(n)
		nodes = append(nodes, UINode{
			ID:            string(n.URN),
			Kind:          string(n.TypeID),
			BroadCategory: broadCategory(n.TypeID),
			Stratum:       string(n.Stratum),
			Label:         label,
			X:             x,
			Y:             y,
			Data:          n.Payload,
		})
	}
	sort.Slice(nodes, func(i, j int) bool { return nodes[i].ID < nodes[j].ID })

	edges := make([]UIEdge, 0, len(state.Wires))
	for key, w := range state.Wires {
		edges = append(edges, UIEdge{
			ID:         key,
			Source:     string(w.SourceURN),
			Target:     string(w.TargetURN),
			SourcePort: string(w.SourcePort),
			TargetPort: string(w.TargetPort),
			Label:      string(w.SourcePort) + " → " + string(w.TargetPort),
		})
	}
	sort.Slice(edges, func(i, j int) bool { return edges[i].ID < edges[j].ID })

	return UIProjection{Nodes: nodes, Edges: edges}
}

// categoryGridPosition places nodes on a semantic grid.
// X = broad_category column, Y = stratum row, with intra-cell offset.
// This is a layout heuristic — position is NOT categorical structure.
func categoryGridPosition(tid cat.TypeID, stratum string, index int) (float64, float64) {
	col := categoryColumnIndex(broadCategory(tid))
	row := stratumRowIndex(stratum)

	const colW, rowH = 180.0, 200.0
	const cellCols = 4
	cx := float64(index%cellCols) * 40
	cy := float64(index/cellCols) * 40

	return float64(col)*colW + cx + 40, float64(row)*rowH + cy + 40
}

func categoryColumnIndex(cat string) int {
	switch cat {
	case "identity":
		return 0
	case "structure":
		return 1
	case "protocol":
		return 2
	case "compute":
		return 3
	case "surface":
		return 4
	case "infra":
		return 5
	case "memory":
		return 6
	case "platform":
		return 7
	case "config":
		return 8
	case "evaluation":
		return 9
	default:
		return 10
	}
}

func stratumRowIndex(s string) int {
	switch s {
	case "S0":
		return 0
	case "S1":
		return 1
	case "S2":
		return 2
	case "S3":
		return 3
	case "S4":
		return 4
	default:
		return 2
	}
}

// extractLabel picks a human-readable label from the node.
func extractLabel(n cat.Node) string {
	if n.Payload != nil {
		if name, ok := n.Payload["name"].(string); ok && name != "" {
			return name
		}
		if label, ok := n.Payload["label"].(string); ok && label != "" {
			return label
		}
	}
	return string(n.URN)
}

// broadCategory maps TypeID → ontology broad_category.
// Derived from superset/ontology.json — the SOT that always wins.
func broadCategory(tid cat.TypeID) string {
	switch tid {
	// identity
	case "user", "collider_admin", "superadmin", "agent_spec":
		return "identity"
	// structure
	case "app_template", "node_container":
		return "structure"
	// compute
	case "agnostic_model", "system_tool", "compute_resource", "provider":
		return "compute"
	// surface
	case "ui_lens", "runtime_surface":
		return "surface"
	// protocol
	case "protocol_adapter":
		return "protocol"
	// infra
	case "infra_service":
		return "infra"
	// memory
	case "memory_store":
		return "memory"
	// platform
	case "platform_config", "workstation_config":
		return "platform"
	// config
	case "preference":
		return "config"
	// evaluation
	case "benchmark_suite", "benchmark_task", "benchmark_score":
		return "evaluation"
	// industry
	case "industry_entity":
		return "industry"
	default:
		return "unknown"
	}
}

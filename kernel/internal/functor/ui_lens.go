package functor

import (
	"hash/fnv"

	"moos/internal/cat"
)

// UINode is a projected node for the UI_Lens functor.
type UINode struct {
	ID    string         `json:"id"`
	Kind  string         `json:"kind"`
	Label string         `json:"label"`
	X     float64        `json:"x"`
	Y     float64        `json:"y"`
	Data  map[string]any `json:"data,omitempty"`
}

// UIEdge is a projected wire for the UI_Lens functor.
type UIEdge struct {
	ID         string `json:"id"`
	Source     string `json:"source"`
	Target     string `json:"target"`
	SourcePort string `json:"source_port"`
	TargetPort string `json:"target_port"`
	Label      string `json:"label"`
}

// UIProjection is the output of the UI_Lens functor.
type UIProjection struct {
	Nodes []UINode `json:"nodes"`
	Edges []UIEdge `json:"edges"`
}

// UILens projects a GraphState into a UI-renderable structure.
type UILens interface {
	Projector
	ProjectUI(state cat.GraphState) UIProjection
}

// MockUILens is a deterministic mock of the UI_Lens functor.
// Every Node → UINode at a hash-based grid position.
// Every Wire → UIEdge.
type MockUILens struct{}

func (m MockUILens) Name() string { return "UI_Lens" }

func (m MockUILens) Project(state cat.GraphState) (any, error) {
	return m.ProjectUI(state), nil
}

func (m MockUILens) ProjectUI(state cat.GraphState) UIProjection {
	nodes := make([]UINode, 0, len(state.Nodes))
	for _, node := range state.Nodes {
		h := fnv.New32a()
		h.Write([]byte(node.URN))
		hash := h.Sum32()
		nodes = append(nodes, UINode{
			ID:    string(node.URN),
			Kind:  string(node.Kind),
			Label: string(node.URN),
			X:     float64(hash%20) * 50,
			Y:     float64((hash/20)%20) * 50,
			Data:  node.Payload,
		})
	}
	edges := make([]UIEdge, 0, len(state.Wires))
	for key, wire := range state.Wires {
		edges = append(edges, UIEdge{
			ID:         key,
			Source:     string(wire.SourceURN),
			Target:     string(wire.TargetURN),
			SourcePort: string(wire.SourcePort),
			TargetPort: string(wire.TargetPort),
			Label:      string(wire.SourcePort) + " → " + string(wire.TargetPort),
		})
	}
	return UIProjection{Nodes: nodes, Edges: edges}
}

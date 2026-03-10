package functor

import (
	"sort"

	"moos/src/internal/cat"
)

// DAGResult is the output of the Structure functor (FUN04: F_struct: subgraph → DAG).
type DAGResult struct {
	TopologicalOrder []cat.URN   `json:"topological_order"`
	Layers           [][]cat.URN `json:"layers"`
}

// StructureMap analyzes graph topology.
type StructureMap interface {
	Analyze(state cat.GraphState) DAGResult
}

// MockStructureMap returns nodes sorted by URN (trivial topological ordering).
type MockStructureMap struct{}

func (m MockStructureMap) Analyze(state cat.GraphState) DAGResult {
	urns := make([]cat.URN, 0, len(state.Nodes))
	for urn := range state.Nodes {
		urns = append(urns, urn)
	}
	sort.Slice(urns, func(i, j int) bool { return urns[i] < urns[j] })
	return DAGResult{
		TopologicalOrder: urns,
		Layers:           [][]cat.URN{urns},
	}
}

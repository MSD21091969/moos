package cat

// GraphState is the carrier algebra — the current materialized state of Category C.
// Nodes map implements Ob(C); Wires map implements Hom(C).
//
// Per AX3, this state is always reconstructible from the morphism log via catamorphism:
//
//	state = fold(∅, morphism_log)
type GraphState struct {
	Nodes map[URN]Node    `json:"nodes"`
	Wires map[string]Wire `json:"wires"`
}

// NewGraphState returns an empty carrier (initial object).
func NewGraphState() GraphState {
	return GraphState{
		Nodes: map[URN]Node{},
		Wires: map[string]Wire{},
	}
}

// Clone produces a deep copy of the graph state.
// Required for pure evaluation — the fold must never mutate its input.
func (gs GraphState) Clone() GraphState {
	c := NewGraphState()
	for urn, node := range gs.Nodes {
		c.Nodes[urn] = Node{
			URN:      node.URN,
			Kind:     node.Kind,
			Stratum:  node.Stratum,
			Payload:  cloneMap(node.Payload),
			Metadata: cloneMap(node.Metadata),
			Version:  node.Version,
		}
	}
	for key, wire := range gs.Wires {
		c.Wires[key] = Wire{
			SourceURN:  wire.SourceURN,
			SourcePort: wire.SourcePort,
			TargetURN:  wire.TargetURN,
			TargetPort: wire.TargetPort,
			Config:     cloneMap(wire.Config),
		}
	}
	return c
}

func cloneMap(m map[string]any) map[string]any {
	if len(m) == 0 {
		return nil
	}
	out := make(map[string]any, len(m))
	for k, v := range m {
		out[k] = cloneValue(v)
	}
	return out
}

func cloneValue(v any) any {
	switch t := v.(type) {
	case map[string]any:
		return cloneMap(t)
	case []any:
		c := make([]any, len(t))
		for i, item := range t {
			c[i] = cloneValue(item)
		}
		return c
	default:
		return t
	}
}

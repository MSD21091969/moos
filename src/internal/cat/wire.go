package cat

// Wire is a Morphism in Hom(C) — an edge in the typed hypergraph (CAT01).
//
// Per AX4 (Hypergraph_Superposition), the graph is the superposition of all
// projected graphs. Multiple wires between the same (A,B) are distinguished by
// ports. UNIQUE on the 4-tuple (SourceURN, SourcePort, TargetURN, TargetPort).
type Wire struct {
	SourceURN  URN            `json:"source_urn"`
	SourcePort Port           `json:"source_port"`
	TargetURN  URN            `json:"target_urn"`
	TargetPort Port           `json:"target_port"`
	Config     map[string]any `json:"config,omitempty"`
}

// WireKey produces the unique composite key for a wire (AX4 4-tuple).
func WireKey(src URN, sp Port, tgt URN, tp Port) string {
	return string(src) + "|" + string(sp) + "|" + string(tgt) + "|" + string(tp)
}

// Key returns the WireKey for this wire.
func (w Wire) Key() string {
	return WireKey(w.SourceURN, w.SourcePort, w.TargetURN, w.TargetPort)
}

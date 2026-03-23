package cat

import "time"

// Wire is a directed edge in the typed hypergraph — a morphism between Nodes.
// Multiple wires between the same (A,B) are distinguished by ports.
// UNIQUE on the 4-tuple (SourceURN, SourcePort, TargetURN, TargetPort).
type Wire struct {
	SourceURN  URN            `json:"source_urn"`
	SourcePort Port           `json:"source_port"`
	TargetURN  URN            `json:"target_urn"`
	TargetPort Port           `json:"target_port"`
	Config     map[string]any `json:"config,omitempty"`
	CreatedAt  time.Time      `json:"created_at"`
}

// WireKey produces the unique composite key for a wire (4-tuple).
func WireKey(src URN, sp Port, tgt URN, tp Port) string {
	return string(src) + "|" + string(sp) + "|" + string(tgt) + "|" + string(tp)
}

// Key returns the WireKey for this wire.
func (w Wire) Key() string {
	return WireKey(w.SourceURN, w.SourcePort, w.TargetURN, w.TargetPort)
}

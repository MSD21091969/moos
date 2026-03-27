package shell

import (
	"time"

	"moos/platform/kernel/internal/cat"
	"moos/platform/kernel/internal/operad"
)

// InspectSubstrate provides read-only graph access for inspect paths.
type InspectSubstrate interface {
	State() cat.GraphState
	Node(urn cat.URN) (cat.Node, bool)
	Nodes() map[cat.URN]cat.Node
	Wires() map[string]cat.Wire
	OutgoingWires(urn cat.URN) []cat.Wire
	IncomingWires(urn cat.URN) []cat.Wire
	ScopedSubgraph(actor cat.URN) cat.GraphState
	Log() []cat.PersistedEnvelope
	LogLen() int
	Epoch() time.Time
	Registry() *operad.Registry
	Subscribe() (string, <-chan cat.PersistedEnvelope)
	Unsubscribe(id string)
}

// RunSubstrate provides mutation entry points for run paths.
type RunSubstrate interface {
	Apply(envelope cat.Envelope) (cat.EvalResult, error)
	ApplyProgram(program cat.Program) (cat.ProgramResult, error)
}

var _ InspectSubstrate = (*Runtime)(nil)
var _ RunSubstrate = (*Runtime)(nil)

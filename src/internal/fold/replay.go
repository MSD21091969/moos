package fold

import (
	"moos/src/internal/cat"
	"moos/src/internal/operad"
)

// Replay is the full catamorphism: fold from the initial object (∅) over the
// morphism log, producing the current graph state.
//
// Per AX3: state(x, t) = fold(morphism_log(x, 0..t))
func Replay(entries []cat.PersistedEnvelope) (cat.GraphState, error) {
	return ReplayWithRegistry(entries, nil)
}

// ReplayWithRegistry replays the morphism log with operad constraint checking.
func ReplayWithRegistry(entries []cat.PersistedEnvelope, registry *operad.Registry) (cat.GraphState, error) {
	state := cat.NewGraphState()
	for _, entry := range entries {
		result, err := EvaluateWithRegistry(state, entry.Envelope, entry.IssuedAt, registry)
		if err != nil {
			return cat.GraphState{}, err
		}
		state = result.State
	}
	return state, nil
}

package fold

import (
	"errors"
	"log"

	"moos/platform/kernel/internal/cat"
	"moos/platform/kernel/internal/operad"
)

// Replay is the full catamorphism: fold from the initial object (∅) over the
// morphism log, producing the current graph state.
func Replay(entries []cat.PersistedEnvelope) (cat.GraphState, error) {
	return ReplayWithRegistry(entries, nil)
}

// ReplayWithRegistry replays the morphism log with operad constraint checking.
// Idempotency errors (ErrNodeExists on ADD, ErrWireExists on LINK,
// ErrNodeNotFound/ErrWireNotFound on UNLINK) are skipped — they indicate
// duplicate log entries and do not corrupt state.
func ReplayWithRegistry(entries []cat.PersistedEnvelope, registry *operad.Registry) (cat.GraphState, error) {
	state := cat.NewGraphState()
	for _, entry := range entries {
		result, err := EvaluateWithRegistry(state, entry.Envelope, entry.IssuedAt, registry)
		if err != nil {
			if isIdempotentReplayError(entry.Envelope.Type, err) {
				log.Printf("[replay] skipping duplicate entry (type=%s): %v", entry.Envelope.Type, err)
				continue
			}
			return cat.GraphState{}, err
		}
		state = result.State
	}
	return state, nil
}

// isIdempotentReplayError returns true for errors that indicate a morphism was
// already applied — safe to skip during log replay without corrupting state.
func isIdempotentReplayError(mt cat.MorphismType, err error) bool {
	switch mt {
	case cat.ADD:
		return errors.Is(err, cat.ErrNodeExists)
	case cat.LINK:
		return errors.Is(err, cat.ErrWireExists)
	case cat.UNLINK:
		return errors.Is(err, cat.ErrWireNotFound)
	case cat.MUTATE:
		return errors.Is(err, cat.ErrVersionConflict)
	}
	return false
}

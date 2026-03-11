// Package shell is the effect boundary — the only layer with IO, locks, and persistence.
// It wraps the pure fold with a RWMutex-guarded runtime, a pluggable Store, and the
// semantic operad registry.
//
// Architectural constraint: All state mutation goes through Apply or SeedIfAbsent.
// Both delegate to fold.EvaluateWithRegistry for the pure step, then persist.
package shell

import (
	"moos/kernel_v2/internal/cat"
)

// Store is the persistence interface for the morphism log (the free monoid over NTs).
// Two implementations: LogStore (JSONL file) and MemStore (testing).
type Store interface {
	// Append persists a batch of morphism log entries.
	Append(entries []cat.PersistedEnvelope) error
	// ReadAll loads the full morphism log for replay.
	ReadAll() ([]cat.PersistedEnvelope, error)
}

package shell

import (
	"sync"

	"moos/platform/kernel/internal/cat"
)

// MemStore is an in-memory Store for testing. Not thread-safe on its own
// (the Runtime provides the lock).
type MemStore struct {
	mu      sync.Mutex
	entries []cat.PersistedEnvelope
}

// NewMemStore creates an empty in-memory store.
func NewMemStore() *MemStore {
	return &MemStore{}
}

// Append stores envelopes in memory, preserving insertion order.
func (m *MemStore) Append(entries []cat.PersistedEnvelope) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.entries = append(m.entries, entries...)
	return nil
}

// ReadAll returns a copy of all in-memory envelopes.
func (m *MemStore) ReadAll() ([]cat.PersistedEnvelope, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	out := make([]cat.PersistedEnvelope, len(m.entries))
	copy(out, m.entries)
	return out, nil
}

package shell

import (
	"sync"

	"moos/kernel_v2/internal/cat"
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

func (m *MemStore) Append(entries []cat.PersistedEnvelope) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.entries = append(m.entries, entries...)
	return nil
}

func (m *MemStore) ReadAll() ([]cat.PersistedEnvelope, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	out := make([]cat.PersistedEnvelope, len(m.entries))
	copy(out, m.entries)
	return out, nil
}

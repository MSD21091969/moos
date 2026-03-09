package shell

import "moos/platform/kernel/internal/core"

type Store interface {
	Load() ([]core.PersistedEnvelope, error)
	AppendBatch(entries []core.PersistedEnvelope) error
}

type RuntimeConfig struct {
	Store    Store
	Registry *core.SemanticRegistry
}

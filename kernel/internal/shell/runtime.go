package shell

import (
	"errors"
	"fmt"
	"log"
	"sync"
	"time"

	"moos/internal/cat"
	"moos/internal/fold"
	"moos/internal/operad"
)

// Runtime is the effect shell wrapping the pure catamorphism.
// All shared state is guarded by RWMutex. Read paths use RLock; writes use Lock.
type Runtime struct {
	mu       sync.RWMutex
	state    cat.GraphState
	store    Store
	registry *operad.Registry
	log      []cat.PersistedEnvelope
}

// NewRuntime constructs a Runtime by replaying the morphism log from the store.
// If a registry is provided, replay enforces operad constraints.
func NewRuntime(store Store, registry *operad.Registry) (*Runtime, error) {
	entries, err := store.ReadAll()
	if err != nil {
		return nil, fmt.Errorf("reading morphism log: %w", err)
	}

	state, err := fold.ReplayWithRegistry(entries, registry)
	if err != nil {
		return nil, fmt.Errorf("replaying morphism log: %w", err)
	}

	log.Printf("[shell] replayed %d morphisms → %d nodes, %d wires",
		len(entries), len(state.Nodes), len(state.Wires))

	return &Runtime{
		state:    state,
		store:    store,
		registry: registry,
		log:      entries,
	}, nil
}

// Apply evaluates a single envelope, persists it, and updates the runtime state.
func (r *Runtime) Apply(envelope cat.Envelope) (cat.EvalResult, error) {
	r.mu.Lock()
	defer r.mu.Unlock()

	now := time.Now().UTC()
	result, err := fold.EvaluateWithRegistry(r.state, envelope, now, r.registry)
	if err != nil {
		return cat.EvalResult{}, err
	}

	if err := r.store.Append([]cat.PersistedEnvelope{result.Persisted}); err != nil {
		return cat.EvalResult{}, fmt.Errorf("persisting morphism: %w", err)
	}

	r.state = result.State
	r.log = append(r.log, result.Persisted)
	return result, nil
}

// ApplyProgram evaluates an atomic batch of envelopes.
func (r *Runtime) ApplyProgram(program cat.Program) (cat.ProgramResult, error) {
	r.mu.Lock()
	defer r.mu.Unlock()

	now := time.Now().UTC()
	result, err := fold.EvaluateProgramWithRegistry(r.state, program, now, r.registry)
	if err != nil {
		return cat.ProgramResult{}, err
	}

	if err := r.store.Append(result.Persisted); err != nil {
		return cat.ProgramResult{}, fmt.Errorf("persisting program: %w", err)
	}

	r.state = result.State
	r.log = append(r.log, result.Persisted...)
	return result, nil
}

// SeedIfAbsent applies an envelope but absorbs ErrNodeExists and ErrWireExists.
// Used at boot time for idempotent seeding — repeated boots don't fail.
func (r *Runtime) SeedIfAbsent(envelope cat.Envelope) error {
	_, err := r.Apply(envelope)
	if err == nil {
		return nil
	}
	if errors.Is(err, cat.ErrNodeExists) || errors.Is(err, cat.ErrWireExists) {
		return nil
	}
	return err
}

// State returns a read-only snapshot of the current graph state.
func (r *Runtime) State() cat.GraphState {
	r.mu.RLock()
	defer r.mu.RUnlock()
	return r.state.Clone()
}

// Node returns a single node by URN.
func (r *Runtime) Node(urn cat.URN) (cat.Node, bool) {
	r.mu.RLock()
	defer r.mu.RUnlock()
	node, ok := r.state.Nodes[urn]
	return node, ok
}

// Nodes returns all nodes.
func (r *Runtime) Nodes() map[cat.URN]cat.Node {
	r.mu.RLock()
	defer r.mu.RUnlock()
	out := make(map[cat.URN]cat.Node, len(r.state.Nodes))
	for k, v := range r.state.Nodes {
		out[k] = v
	}
	return out
}

// Wires returns all wires.
func (r *Runtime) Wires() map[string]cat.Wire {
	r.mu.RLock()
	defer r.mu.RUnlock()
	out := make(map[string]cat.Wire, len(r.state.Wires))
	for k, v := range r.state.Wires {
		out[k] = v
	}
	return out
}

// OutgoingWires returns wires originating from a given node.
func (r *Runtime) OutgoingWires(urn cat.URN) []cat.Wire {
	r.mu.RLock()
	defer r.mu.RUnlock()
	var out []cat.Wire
	for _, wire := range r.state.Wires {
		if wire.SourceURN == urn {
			out = append(out, wire)
		}
	}
	return out
}

// IncomingWires returns wires terminating at a given node.
func (r *Runtime) IncomingWires(urn cat.URN) []cat.Wire {
	r.mu.RLock()
	defer r.mu.RUnlock()
	var out []cat.Wire
	for _, wire := range r.state.Wires {
		if wire.TargetURN == urn {
			out = append(out, wire)
		}
	}
	return out
}

// Log returns the full morphism log.
func (r *Runtime) Log() []cat.PersistedEnvelope {
	r.mu.RLock()
	defer r.mu.RUnlock()
	out := make([]cat.PersistedEnvelope, len(r.log))
	copy(out, r.log)
	return out
}

// LogLen returns the number of entries in the morphism log.
func (r *Runtime) LogLen() int {
	r.mu.RLock()
	defer r.mu.RUnlock()
	return len(r.log)
}

// Registry returns the operad registry (may be nil).
func (r *Runtime) Registry() *operad.Registry {
	return r.registry
}

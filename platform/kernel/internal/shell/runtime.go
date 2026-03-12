package shell

import (
	"errors"
	"fmt"
	"log"
	"sync"
	"time"

	"moos/platform/kernel/internal/cat"
	"moos/platform/kernel/internal/fold"
	"moos/platform/kernel/internal/operad"
)

// Runtime is the effect shell wrapping the pure catamorphism.
// All shared state is guarded by RWMutex. Read paths use RLock; writes use Lock.
type Runtime struct {
	mu           sync.RWMutex
	state        cat.GraphState
	store        Store
	registry     *operad.Registry
	log          []cat.PersistedEnvelope
	subscriberMu sync.Mutex // separate from state RWMutex to avoid deadlock
	subscribers  map[string]chan cat.PersistedEnvelope
	nextSubID    int
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
		state:       state,
		store:       store,
		registry:    registry,
		log:         entries,
		subscribers: make(map[string]chan cat.PersistedEnvelope),
	}, nil
}

// Apply evaluates a single envelope, persists it, and updates the runtime state.
func (r *Runtime) Apply(envelope cat.Envelope) (cat.EvalResult, error) {
	r.mu.Lock()

	now := time.Now().UTC()
	result, err := fold.EvaluateWithRegistry(r.state, envelope, now, r.registry)
	if err != nil {
		r.mu.Unlock()
		return cat.EvalResult{}, err
	}

	if err := r.store.Append([]cat.PersistedEnvelope{result.Persisted}); err != nil {
		r.mu.Unlock()
		return cat.EvalResult{}, fmt.Errorf("persisting morphism: %w", err)
	}

	r.state = result.State
	r.log = append(r.log, result.Persisted)
	r.mu.Unlock()

	r.broadcast(result.Persisted)
	return result, nil
}

// ApplyProgram evaluates an atomic batch of envelopes.
func (r *Runtime) ApplyProgram(program cat.Program) (cat.ProgramResult, error) {
	r.mu.Lock()

	now := time.Now().UTC()
	result, err := fold.EvaluateProgramWithRegistry(r.state, program, now, r.registry)
	if err != nil {
		r.mu.Unlock()
		return cat.ProgramResult{}, err
	}

	if err := r.store.Append(result.Persisted); err != nil {
		r.mu.Unlock()
		return cat.ProgramResult{}, fmt.Errorf("persisting program: %w", err)
	}

	r.state = result.State
	r.log = append(r.log, result.Persisted...)
	r.mu.Unlock()

	r.broadcast(result.Persisted...)
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

// ScopedSubgraph returns the full subcategory owned by actor.
// BFS follows outgoing wires where SourcePort == "OWNS", collecting all
// transitively owned nodes and any wires whose both endpoints are in the set.
// Returns an empty GraphState if actor is not found.
func (r *Runtime) ScopedSubgraph(actor cat.URN) cat.GraphState {
	r.mu.RLock()
	defer r.mu.RUnlock()

	result := cat.NewGraphState()
	if _, ok := r.state.Nodes[actor]; !ok {
		return result
	}

	// BFS from actor following OWNS wires
	visited := map[cat.URN]bool{actor: true}
	queue := []cat.URN{actor}

	for len(queue) > 0 {
		current := queue[0]
		queue = queue[1:]
		result.Nodes[current] = r.state.Nodes[current]

		for _, w := range r.state.Wires {
			if w.SourceURN == current && w.SourcePort == "OWNS" && !visited[w.TargetURN] {
				if _, exists := r.state.Nodes[w.TargetURN]; exists {
					visited[w.TargetURN] = true
					queue = append(queue, w.TargetURN)
				}
			}
		}
	}

	// Collect wires where both endpoints are in the visited set
	for key, w := range r.state.Wires {
		if visited[w.SourceURN] && visited[w.TargetURN] {
			result.Wires[key] = w
		}
	}

	return result
}

// Registry returns the operad registry (may be nil).
func (r *Runtime) Registry() *operad.Registry {
	return r.registry
}

// Subscribe registers a new observer and returns its id and receive-only channel.
// The channel is buffered (64) so brief bursts don't block the kernel.
func (r *Runtime) Subscribe() (string, <-chan cat.PersistedEnvelope) {
	r.subscriberMu.Lock()
	defer r.subscriberMu.Unlock()
	r.nextSubID++
	id := fmt.Sprintf("sub-%d", r.nextSubID)
	ch := make(chan cat.PersistedEnvelope, 64)
	r.subscribers[id] = ch
	return id, ch
}

// Unsubscribe closes and removes a subscriber channel.
func (r *Runtime) Unsubscribe(id string) {
	r.subscriberMu.Lock()
	defer r.subscriberMu.Unlock()
	if ch, ok := r.subscribers[id]; ok {
		close(ch)
		delete(r.subscribers, id)
	}
}

// broadcast delivers entries to all subscriber channels using non-blocking sends.
// A slow or unresponsive subscriber is silently dropped for that entry.
func (r *Runtime) broadcast(entries ...cat.PersistedEnvelope) {
	r.subscriberMu.Lock()
	defer r.subscriberMu.Unlock()
	for _, entry := range entries {
		for _, ch := range r.subscribers {
			select {
			case ch <- entry:
			default:
			}
		}
	}
}

package shell

import (
	"errors"
	"fmt"
	"sort"
	"sync"
	"time"

	"moos/platform/kernel/internal/core"
)

type Runtime struct {
	mu       sync.RWMutex
	state    core.GraphState
	store    Store
	registry *core.SemanticRegistry
	logs     []core.PersistedEnvelope
}

func NewRuntime(logPath string) (*Runtime, error) {
	return NewRuntimeWithConfig(RuntimeConfig{Store: LogStore{Path: logPath}})
}

func NewRuntimeWithConfig(config RuntimeConfig) (*Runtime, error) {
	if config.Store == nil {
		return nil, fmt.Errorf("runtime store is required")
	}
	runtime := &Runtime{
		state:    core.NewGraphState(),
		store:    config.Store,
		registry: config.Registry,
		logs:     []core.PersistedEnvelope{},
	}
	entries, err := runtime.store.Load()
	if err != nil {
		return nil, err
	}
	for _, entry := range entries {
		result, err := core.EvaluateWithRegistry(runtime.state, entry.Envelope, entry.IssuedAt, runtime.registry)
		if err != nil {
			return nil, fmt.Errorf("replay failed: %w", err)
		}
		runtime.state = result.State
		runtime.logs = append(runtime.logs, entry)
	}
	return runtime, nil
}

func (runtime *Runtime) Apply(envelope core.Envelope) (core.EvalResult, error) {
	runtime.mu.Lock()
	defer runtime.mu.Unlock()

	issuedAt := time.Now().UTC()
	result, err := core.EvaluateWithRegistry(runtime.state, envelope, issuedAt, runtime.registry)
	if err != nil {
		return core.EvalResult{}, err
	}
	if err := runtime.store.AppendBatch([]core.PersistedEnvelope{result.Persisted}); err != nil {
		return core.EvalResult{}, err
	}
	runtime.state = result.State
	runtime.logs = append(runtime.logs, result.Persisted)
	return result, nil
}

func (runtime *Runtime) ApplyProgram(program core.Program) (core.ProgramResult, error) {
	runtime.mu.Lock()
	defer runtime.mu.Unlock()

	issuedAt := time.Now().UTC()
	result, err := core.EvaluateProgramWithRegistry(runtime.state, program, issuedAt, runtime.registry)
	if err != nil {
		return core.ProgramResult{}, err
	}
	if err := runtime.store.AppendBatch(result.Persisted); err != nil {
		return core.ProgramResult{}, err
	}
	runtime.state = result.State
	runtime.logs = append(runtime.logs, result.Persisted...)
	return result, nil
}

func (runtime *Runtime) Summary() map[string]any {
	runtime.mu.RLock()
	defer runtime.mu.RUnlock()
	return map[string]any{
		"nodes":       len(runtime.state.Nodes),
		"wires":       len(runtime.state.Wires),
		"log_entries": len(runtime.logs),
	}
}

func (runtime *Runtime) Snapshot() core.GraphState {
	runtime.mu.RLock()
	defer runtime.mu.RUnlock()
	return runtime.state.Clone()
}

func (runtime *Runtime) Nodes(kind string, stratum string) []core.Node {
	runtime.mu.RLock()
	defer runtime.mu.RUnlock()

	nodes := make([]core.Node, 0, len(runtime.state.Nodes))
	for _, node := range runtime.state.Nodes {
		if kind != "" && string(node.Kind) != kind {
			continue
		}
		if stratum != "" && string(node.Stratum) != stratum {
			continue
		}
		nodes = append(nodes, node)
	}

	sort.Slice(nodes, func(left int, right int) bool {
		return nodes[left].URN < nodes[right].URN
	})
	return nodes
}

func (runtime *Runtime) Node(urn string) (core.Node, bool) {
	runtime.mu.RLock()
	defer runtime.mu.RUnlock()
	node, ok := runtime.state.Nodes[core.URN(urn)]
	return node, ok
}

func (runtime *Runtime) Wires() []core.Wire {
	runtime.mu.RLock()
	defer runtime.mu.RUnlock()
	return sortedWires(runtime.state.Wires, nil)
}

func (runtime *Runtime) OutgoingWires(urn string) []core.Wire {
	runtime.mu.RLock()
	defer runtime.mu.RUnlock()
	return sortedWires(runtime.state.Wires, func(wire core.Wire) bool {
		return wire.SourceURN == core.URN(urn)
	})
}

func (runtime *Runtime) IncomingWires(urn string) []core.Wire {
	runtime.mu.RLock()
	defer runtime.mu.RUnlock()
	return sortedWires(runtime.state.Wires, func(wire core.Wire) bool {
		return wire.TargetURN == core.URN(urn)
	})
}

func (runtime *Runtime) LogEntries() []core.PersistedEnvelope {
	runtime.mu.RLock()
	defer runtime.mu.RUnlock()
	entries := make([]core.PersistedEnvelope, len(runtime.logs))
	copy(entries, runtime.logs)
	return entries
}

func (runtime *Runtime) Registry() *core.SemanticRegistry {
	runtime.mu.RLock()
	defer runtime.mu.RUnlock()
	return runtime.registry
}

// SeedIfAbsent applies the envelope only when its target does not already exist.
// It is safe to call on every boot; existing nodes and wires are silently skipped.
func (runtime *Runtime) SeedIfAbsent(envelope core.Envelope) error {
	_, err := runtime.Apply(envelope)
	if errors.Is(err, core.ErrNodeExists) || errors.Is(err, core.ErrWireExists) {
		return nil
	}
	return err
}

func (runtime *Runtime) Close() error {
	if closer, ok := runtime.store.(interface{ Close() error }); ok {
		return closer.Close()
	}
	return nil
}

func sortedWires(wiresByKey map[string]core.Wire, include func(core.Wire) bool) []core.Wire {
	wires := make([]core.Wire, 0, len(wiresByKey))
	for _, wire := range wiresByKey {
		if include != nil && !include(wire) {
			continue
		}
		wires = append(wires, wire)
	}
	sort.Slice(wires, func(left int, right int) bool {
		leftKey := core.WireKey(wires[left].SourceURN, wires[left].SourcePort, wires[left].TargetURN, wires[left].TargetPort)
		rightKey := core.WireKey(wires[right].SourceURN, wires[right].SourcePort, wires[right].TargetURN, wires[right].TargetPort)
		return leftKey < rightKey
	})
	return wires
}

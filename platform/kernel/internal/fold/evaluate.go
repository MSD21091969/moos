// Package fold implements the Σ-catamorphism — the unique fold from the initial
// algebra (morphism log) to the carrier algebra (GraphState).
//
// PURITY INVARIANT: This package has ZERO imports of os, net, sync, or any
// persistence layer. Functions take state and return new state. Nothing else.
package fold

import (
	"fmt"
	"time"

	"moos/platform/kernel/internal/cat"
	"moos/platform/kernel/internal/operad"
)

// Evaluate applies a single envelope to a graph state, producing a new state.
// This is one step of the catamorphism: GraphState × Envelope → GraphState.
// No registry validation — use EvaluateWithRegistry for constrained evaluation.
func Evaluate(state cat.GraphState, envelope cat.Envelope, issuedAt time.Time) (cat.EvalResult, error) {
	return EvaluateWithRegistry(state, envelope, issuedAt, nil)
}

// EvaluateWithRegistry applies a single envelope with operad constraint checking.
// If registry is nil, operates without type constraints.
func EvaluateWithRegistry(state cat.GraphState, envelope cat.Envelope, issuedAt time.Time, registry *operad.Registry) (cat.EvalResult, error) {
	if err := envelope.Validate(); err != nil {
		return cat.EvalResult{}, err
	}

	next := state.Clone()
	result := cat.EvalResult{
		State: next,
		Persisted: cat.PersistedEnvelope{
			Envelope: envelope,
			IssuedAt: issuedAt.UTC(),
		},
	}

	switch envelope.Type {
	case cat.ADD:
		node, err := applyAdd(&next, envelope.Add, registry)
		if err != nil {
			return cat.EvalResult{}, err
		}
		result.Node = &node
		result.Summary = "node added"

	case cat.LINK:
		wire, err := applyLink(&next, envelope.Link, registry)
		if err != nil {
			return cat.EvalResult{}, err
		}
		result.Wire = &wire
		result.Summary = "wire linked"

	case cat.MUTATE:
		node, err := applyMutate(&next, envelope.Mutate, registry)
		if err != nil {
			return cat.EvalResult{}, err
		}
		result.Node = &node
		result.Summary = "node mutated"

	case cat.UNLINK:
		wire, err := applyUnlink(&next, envelope.Unlink)
		if err != nil {
			return cat.EvalResult{}, err
		}
		result.Wire = &wire
		result.Summary = "wire unlinked"

	default:
		return cat.EvalResult{}, fmt.Errorf("%w: %s", cat.ErrUnsupportedMorphism, envelope.Type)
	}

	result.State = next
	return result, nil
}

// applyAdd: ∅ → Node. Creates a new Node.
func applyAdd(state *cat.GraphState, p *cat.AddPayload, reg *operad.Registry) (cat.Node, error) {
	if _, exists := state.Nodes[p.URN]; exists {
		return cat.Node{}, fmt.Errorf("%w: %s", cat.ErrNodeExists, p.URN)
	}
	stratum := cat.NormalizeStratum(p.Stratum)
	if !cat.ValidStratum(stratum) {
		return cat.Node{}, fmt.Errorf("%w: %s", cat.ErrInvalidStratum, stratum)
	}
	if err := validateAdd(reg, p); err != nil {
		return cat.Node{}, err
	}
	node := cat.Node{
		URN:      p.URN,
		TypeID:   p.TypeID,
		Stratum:  stratum,
		Payload:  deepCopy(p.Payload),
		Metadata: deepCopy(p.Metadata),
		Version:  1,
	}
	state.Nodes[p.URN] = node
	return node, nil
}

// applyLink: N × N → Wire. Creates a new Wire.
func applyLink(state *cat.GraphState, p *cat.LinkPayload, reg *operad.Registry) (cat.Wire, error) {
	src, ok := state.Nodes[p.SourceURN]
	if !ok {
		return cat.Wire{}, fmt.Errorf("%w: source %s", cat.ErrNodeNotFound, p.SourceURN)
	}
	tgt, ok := state.Nodes[p.TargetURN]
	if !ok {
		return cat.Wire{}, fmt.Errorf("%w: target %s", cat.ErrNodeNotFound, p.TargetURN)
	}
	if err := validateLink(reg, src, tgt, p); err != nil {
		return cat.Wire{}, err
	}
	key := cat.WireKey(p.SourceURN, p.SourcePort, p.TargetURN, p.TargetPort)
	if _, exists := state.Wires[key]; exists {
		return cat.Wire{}, fmt.Errorf("%w: %s", cat.ErrWireExists, key)
	}
	wire := cat.Wire{
		SourceURN:  p.SourceURN,
		SourcePort: p.SourcePort,
		TargetURN:  p.TargetURN,
		TargetPort: p.TargetPort,
		Config:     deepCopy(p.Config),
	}
	state.Wires[key] = wire
	return wire, nil
}

// applyMutate: N → N. Updates a Node's payload (endomorphism with version CAS).
func applyMutate(state *cat.GraphState, p *cat.MutatePayload, reg *operad.Registry) (cat.Node, error) {
	node, ok := state.Nodes[p.URN]
	if !ok {
		return cat.Node{}, fmt.Errorf("%w: %s", cat.ErrNodeNotFound, p.URN)
	}
	if node.Stratum == cat.S0 {
		return cat.Node{}, fmt.Errorf("%w: %s", cat.ErrMutationBlocked, p.URN)
	}
	if err := validateMutate(reg, node); err != nil {
		return cat.Node{}, err
	}
	if node.Version != p.ExpectedVersion {
		return cat.Node{}, fmt.Errorf("%w: expected %d, current %d",
			cat.ErrVersionConflict, p.ExpectedVersion, node.Version)
	}
	node.Payload = deepCopy(p.Payload)
	node.Metadata = deepCopy(p.Metadata)
	node.Version++
	state.Nodes[p.URN] = node
	return node, nil
}

// applyUnlink: Wire → ∅. Removes a wire.
func applyUnlink(state *cat.GraphState, p *cat.UnlinkPayload) (cat.Wire, error) {
	key := cat.WireKey(p.SourceURN, p.SourcePort, p.TargetURN, p.TargetPort)
	wire, ok := state.Wires[key]
	if !ok {
		return cat.Wire{}, fmt.Errorf("%w: %s", cat.ErrWireNotFound, key)
	}
	delete(state.Wires, key)
	return wire, nil
}

// --- registry delegation helpers (nil-safe) ---

func validateAdd(reg *operad.Registry, p *cat.AddPayload) error {
	if reg == nil {
		return nil
	}
	return reg.ValidateAdd(p)
}

func validateLink(reg *operad.Registry, src, tgt cat.Node, p *cat.LinkPayload) error {
	if reg == nil {
		return nil
	}
	return reg.ValidateLink(src, tgt, p)
}

func validateMutate(reg *operad.Registry, node cat.Node) error {
	if reg == nil {
		return nil
	}
	return reg.ValidateMutate(node)
}

// deepCopy clones a map[string]any tree.
func deepCopy(m map[string]any) map[string]any {
	if len(m) == 0 {
		return nil
	}
	out := make(map[string]any, len(m))
	for k, v := range m {
		out[k] = copyVal(v)
	}
	return out
}

func copyVal(v any) any {
	switch t := v.(type) {
	case map[string]any:
		return deepCopy(t)
	case []any:
		c := make([]any, len(t))
		for i, item := range t {
			c[i] = copyVal(item)
		}
		return c
	default:
		return t
	}
}

package core

import (
	"fmt"
	"time"
)

func Evaluate(state GraphState, envelope Envelope, issuedAt time.Time) (EvalResult, error) {
	return EvaluateWithRegistry(state, envelope, issuedAt, nil)
}

func EvaluateWithRegistry(state GraphState, envelope Envelope, issuedAt time.Time, registry *SemanticRegistry) (EvalResult, error) {
	if err := envelope.Validate(); err != nil {
		return EvalResult{}, err
	}

	nextState := state.Clone()
	result := EvalResult{
		State: nextState,
		Persisted: PersistedEnvelope{
			Envelope: envelope,
			IssuedAt: issuedAt.UTC(),
		},
	}

	switch envelope.Type {
	case MorphismAdd:
		node, err := applyAdd(&nextState, envelope.Add, registry)
		if err != nil {
			return EvalResult{}, err
		}
		result.Node = &node
		result.Summary = "node added"
	case MorphismLink:
		wire, err := applyLink(&nextState, envelope.Link, registry)
		if err != nil {
			return EvalResult{}, err
		}
		result.Wire = &wire
		result.Summary = "wire linked"
	case MorphismMutate:
		node, err := applyMutate(&nextState, envelope.Mutate, registry)
		if err != nil {
			return EvalResult{}, err
		}
		result.Node = &node
		result.Summary = "node mutated"
	case MorphismUnlink:
		wire, err := applyUnlink(&nextState, envelope.Unlink)
		if err != nil {
			return EvalResult{}, err
		}
		result.Wire = &wire
		result.Summary = "wire unlinked"
	default:
		return EvalResult{}, fmt.Errorf("%w: %s", ErrUnsupportedMorphism, envelope.Type)
	}

	result.State = nextState
	return result, nil
}

func applyAdd(state *GraphState, payload *AddPayload, registry *SemanticRegistry) (Node, error) {
	if _, exists := state.Nodes[payload.URN]; exists {
		return Node{}, fmt.Errorf("%w: %s", ErrNodeExists, payload.URN)
	}
	stratum := NormalizeStratum(payload.Stratum)
	if !isValidStratum(stratum) {
		return Node{}, fmt.Errorf("%w: %s", ErrInvalidStratum, stratum)
	}
	if err := registry.ValidateAdd(payload); err != nil {
		return Node{}, err
	}
	node := Node{
		URN:      payload.URN,
		Kind:     payload.Kind,
		Stratum:  stratum,
		Payload:  cloneMap(payload.Payload),
		Metadata: cloneMap(payload.Metadata),
		Version:  1,
	}
	state.Nodes[payload.URN] = node
	return node, nil
}

func applyLink(state *GraphState, payload *LinkPayload, registry *SemanticRegistry) (Wire, error) {
	sourceNode, exists := state.Nodes[payload.SourceURN]
	if !exists {
		return Wire{}, fmt.Errorf("%w: source %s", ErrNodeNotFound, payload.SourceURN)
	}
	targetNode, exists := state.Nodes[payload.TargetURN]
	if !exists {
		return Wire{}, fmt.Errorf("%w: target %s", ErrNodeNotFound, payload.TargetURN)
	}
	if err := registry.ValidateLink(sourceNode, targetNode, payload); err != nil {
		return Wire{}, err
	}
	key := WireKey(payload.SourceURN, payload.SourcePort, payload.TargetURN, payload.TargetPort)
	if _, exists := state.Wires[key]; exists {
		return Wire{}, fmt.Errorf("%w: %s", ErrWireExists, key)
	}
	wire := Wire{
		SourceURN:  payload.SourceURN,
		SourcePort: payload.SourcePort,
		TargetURN:  payload.TargetURN,
		TargetPort: payload.TargetPort,
		Config:     cloneMap(payload.Config),
	}
	state.Wires[key] = wire
	return wire, nil
}

func applyMutate(state *GraphState, payload *MutatePayload, registry *SemanticRegistry) (Node, error) {
	node, exists := state.Nodes[payload.URN]
	if !exists {
		return Node{}, fmt.Errorf("%w: %s", ErrNodeNotFound, payload.URN)
	}
	if node.Stratum == StratumAuthored {
		return Node{}, fmt.Errorf("%w: %s", ErrMutationBlocked, payload.URN)
	}
	if err := registry.ValidateMutate(node); err != nil {
		return Node{}, err
	}
	if node.Version != payload.ExpectedVersion {
		return Node{}, fmt.Errorf("%w: expected %d, current %d", ErrVersionConflict, payload.ExpectedVersion, node.Version)
	}
	node.Payload = cloneMap(payload.Payload)
	node.Metadata = cloneMap(payload.Metadata)
	node.Version++
	state.Nodes[payload.URN] = node
	return node, nil
}

func applyUnlink(state *GraphState, payload *UnlinkPayload) (Wire, error) {
	key := WireKey(payload.SourceURN, payload.SourcePort, payload.TargetURN, payload.TargetPort)
	wire, exists := state.Wires[key]
	if !exists {
		return Wire{}, fmt.Errorf("%w: %s", ErrWireNotFound, key)
	}
	delete(state.Wires, key)
	return wire, nil
}

func isValidStratum(stratum Stratum) bool {
	switch stratum {
	case StratumAuthored, StratumValidated, StratumMaterialized, StratumEvaluated, StratumProjected:
		return true
	default:
		return false
	}
}

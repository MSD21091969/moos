package hydration

import (
	"fmt"
	"time"

	"moos/platform/kernel/internal/core"
)

type MaterializeRequest struct {
	Actor     core.URN         `json:"actor"`
	Scope     core.URN         `json:"scope,omitempty"`
	Apply     bool             `json:"apply,omitempty"`
	Nodes     []AuthoredNode   `json:"nodes,omitempty"`
	Wires     []AuthoredWire   `json:"wires,omitempty"`
	Mutations []AuthoredMutate `json:"mutations,omitempty"`
}

type AuthoredNode struct {
	URN      core.URN       `json:"urn"`
	Kind     core.Kind      `json:"kind"`
	Payload  map[string]any `json:"payload,omitempty"`
	Metadata map[string]any `json:"metadata,omitempty"`
}

type AuthoredWire struct {
	SourceURN  core.URN       `json:"source_urn"`
	SourcePort core.Port      `json:"source_port"`
	TargetURN  core.URN       `json:"target_urn"`
	TargetPort core.Port      `json:"target_port"`
	Config     map[string]any `json:"config,omitempty"`
}

type AuthoredMutate struct {
	URN             core.URN       `json:"urn"`
	ExpectedVersion int64          `json:"expected_version,omitempty"`
	Payload         map[string]any `json:"payload,omitempty"`
	Metadata        map[string]any `json:"metadata,omitempty"`
}

type MaterializeResult struct {
	Program core.Program    `json:"program"`
	Stages  HydrationStages `json:"stages"`
	Summary string          `json:"summary"`
}

type HydrationStages struct {
	Authored     int `json:"authored"`
	Validated    int `json:"validated"`
	Materialized int `json:"materialized"`
}

func Materialize(request MaterializeRequest, registry *core.SemanticRegistry) (MaterializeResult, error) {
	if request.Actor == "" {
		return MaterializeResult{}, fmt.Errorf("%w: actor", core.ErrInvalidActor)
	}
	if len(request.Nodes) == 0 && len(request.Wires) == 0 && len(request.Mutations) == 0 {
		return MaterializeResult{}, fmt.Errorf("%w: authored request must contain nodes, wires, or mutations", core.ErrInvalidProgram)
	}

	knownNodes := make(map[core.URN]struct{}, len(request.Nodes))
	envelopes := make([]core.Envelope, 0, len(request.Nodes)+len(request.Wires)+len(request.Mutations))

	for index, node := range request.Nodes {
		if node.URN == "" || node.Kind == "" {
			return MaterializeResult{}, fmt.Errorf("%w: node %d requires urn and kind", core.ErrInvalidProgram, index)
		}
		if _, exists := knownNodes[node.URN]; exists {
			return MaterializeResult{}, fmt.Errorf("%w: duplicate authored node %s", core.ErrNodeExists, node.URN)
		}
		knownNodes[node.URN] = struct{}{}
		envelopes = append(envelopes, core.Envelope{
			Type:  core.MorphismAdd,
			Actor: request.Actor,
			Scope: request.Scope,
			Add: &core.AddPayload{
				URN:      node.URN,
				Kind:     node.Kind,
				Stratum:  core.StratumMaterialized,
				Payload:  node.Payload,
				Metadata: node.Metadata,
			},
		})
	}

	for index, wire := range request.Wires {
		if _, exists := knownNodes[wire.SourceURN]; !exists {
			return MaterializeResult{}, fmt.Errorf("%w: authored wire %d source %s must be declared in request", core.ErrNodeNotFound, index, wire.SourceURN)
		}
		if _, exists := knownNodes[wire.TargetURN]; !exists {
			return MaterializeResult{}, fmt.Errorf("%w: authored wire %d target %s must be declared in request", core.ErrNodeNotFound, index, wire.TargetURN)
		}
		envelopes = append(envelopes, core.Envelope{
			Type:  core.MorphismLink,
			Actor: request.Actor,
			Scope: request.Scope,
			Link: &core.LinkPayload{
				SourceURN:  wire.SourceURN,
				SourcePort: wire.SourcePort,
				TargetURN:  wire.TargetURN,
				TargetPort: wire.TargetPort,
				Config:     wire.Config,
			},
		})
	}

	for index, mutate := range request.Mutations {
		expectedVersion := mutate.ExpectedVersion
		if _, exists := knownNodes[mutate.URN]; exists && expectedVersion == 0 {
			expectedVersion = 1
		}
		if expectedVersion == 0 {
			return MaterializeResult{}, fmt.Errorf("%w: mutation %d requires expected_version when node is not authored in the same request", core.ErrInvalidProgram, index)
		}
		envelopes = append(envelopes, core.Envelope{
			Type:  core.MorphismMutate,
			Actor: request.Actor,
			Scope: request.Scope,
			Mutate: &core.MutatePayload{
				URN:             mutate.URN,
				ExpectedVersion: expectedVersion,
				Payload:         mutate.Payload,
				Metadata:        mutate.Metadata,
			},
		})
	}

	program := core.Program{
		Actor:     request.Actor,
		Scope:     request.Scope,
		Envelopes: envelopes,
	}
	if _, err := core.EvaluateProgramWithRegistry(core.NewGraphState(), program, time.Time{}, registry); err != nil {
		return MaterializeResult{}, err
	}

	stageCount := len(request.Nodes) + len(request.Wires) + len(request.Mutations)
	return MaterializeResult{
		Program: program,
		Stages: HydrationStages{
			Authored:     stageCount,
			Validated:    stageCount,
			Materialized: len(envelopes),
		},
		Summary: fmt.Sprintf("materialized program: %d envelopes", len(envelopes)),
	}, nil
}

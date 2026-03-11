// Package hydration implements the strata materialization pipeline.
// It converts a MaterializeRequest (declarative batch) into a cat.Program,
// validates it, and optionally applies it via the shell.Runtime.
//
// The pipeline walks the request's node/wire declarations and produces
// the minimal set of ADD + LINK envelopes to materialize the subgraph.
package hydration

import (
	"fmt"

	"moos/kernel_v2/internal/cat"
	"moos/kernel_v2/internal/operad"
)

// MaterializeRequest is the input to the hydration pipeline.
type MaterializeRequest struct {
	Actor string        `json:"actor"`
	Scope string        `json:"scope,omitempty"`
	Nodes []NodeRequest `json:"nodes"`
	Wires []WireRequest `json:"wires,omitempty"`
}

// NodeRequest declares a node to materialize.
type NodeRequest struct {
	URN     string         `json:"urn"`
	TypeID  string         `json:"type_id"`
	Stratum string         `json:"stratum,omitempty"`
	Payload map[string]any `json:"payload,omitempty"`
}

// WireRequest declares a wire to materialize.
type WireRequest struct {
	SourceURN  string `json:"source_urn"`
	SourcePort string `json:"source_port"`
	TargetURN  string `json:"target_urn"`
	TargetPort string `json:"target_port"`
}

// MaterializeResult is the output of the hydration pipeline.
type MaterializeResult struct {
	Program   cat.Program `json:"program"`
	DryRun    bool        `json:"dry_run"`
	NodeCount int         `json:"node_count"`
	WireCount int         `json:"wire_count"`
	Errors    []string    `json:"errors,omitempty"`
}

// Materialize converts a MaterializeRequest into a validated Program.
// If registry is non-nil, validates each envelope against the operad.
// Set dryRun=true to validate without producing a Program for execution.
func Materialize(req MaterializeRequest, registry *operad.Registry, dryRun bool) (MaterializeResult, error) {
	if req.Actor == "" {
		return MaterializeResult{}, fmt.Errorf("actor is required")
	}

	var envelopes []cat.Envelope
	var validationErrors []string

	// Phase 1: Generate ADD envelopes for nodes
	for _, nr := range req.Nodes {
		stratum := cat.Stratum(nr.Stratum)
		if stratum == "" {
			stratum = cat.S2
		}
		if !cat.ValidStratum(stratum) {
			stratum = cat.NormalizeStratum(stratum)
		}

		env := cat.Envelope{
			Type:  cat.ADD,
			Actor: cat.URN(req.Actor),
			Scope: cat.URN(req.Scope),
			Add: &cat.AddPayload{
				URN:     cat.URN(nr.URN),
				TypeID:  cat.TypeID(nr.TypeID),
				Stratum: stratum,
				Payload: nr.Payload,
			},
		}
		if err := env.Validate(); err != nil {
			validationErrors = append(validationErrors, fmt.Sprintf("node %s: %v", nr.URN, err))
			continue
		}
		if registry != nil {
			if err := registry.ValidateAdd(env.Add); err != nil {
				validationErrors = append(validationErrors, fmt.Sprintf("node %s: %v", nr.URN, err))
				continue
			}
		}
		envelopes = append(envelopes, env)
	}

	// Phase 2: Generate LINK envelopes for wires
	for _, wr := range req.Wires {
		env := cat.Envelope{
			Type:  cat.LINK,
			Actor: cat.URN(req.Actor),
			Scope: cat.URN(req.Scope),
			Link: &cat.LinkPayload{
				SourceURN:  cat.URN(wr.SourceURN),
				SourcePort: cat.Port(wr.SourcePort),
				TargetURN:  cat.URN(wr.TargetURN),
				TargetPort: cat.Port(wr.TargetPort),
			},
		}
		if err := env.Validate(); err != nil {
			validationErrors = append(validationErrors, fmt.Sprintf("wire %s→%s: %v", wr.SourceURN, wr.TargetURN, err))
			continue
		}
		envelopes = append(envelopes, env)
	}

	program := cat.Program{
		Actor:     cat.URN(req.Actor),
		Scope:     cat.URN(req.Scope),
		Envelopes: envelopes,
	}

	return MaterializeResult{
		Program:   program,
		DryRun:    dryRun,
		NodeCount: len(req.Nodes),
		WireCount: len(req.Wires),
		Errors:    validationErrors,
	}, nil
}

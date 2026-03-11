package cat

import (
	"fmt"
	"time"
)

// Program is a composed morphism — an atomic batch of Envelopes.
// All envelopes execute as a single transaction: either all succeed or none.
// Actor and Scope on the Program propagate to child Envelopes.
type Program struct {
	Actor     URN        `json:"actor,omitempty"`
	Scope     URN        `json:"scope,omitempty"`
	Envelopes []Envelope `json:"envelopes"`
}

// Validate checks program structural correctness.
func (p Program) Validate() error {
	if len(p.Envelopes) == 0 {
		return fmt.Errorf("%w: program must contain at least one envelope", ErrInvalidProgram)
	}
	_, err := p.NormalizedEnvelopes()
	return err
}

// NormalizedEnvelopes returns envelopes with Actor/Scope inherited from the Program.
func (p Program) NormalizedEnvelopes() ([]Envelope, error) {
	out := make([]Envelope, len(p.Envelopes))
	for i, env := range p.Envelopes {
		if p.Actor != "" {
			if env.Actor != "" && env.Actor != p.Actor {
				return nil, fmt.Errorf("%w: envelope %d actor %q does not match program actor %q",
					ErrInvalidProgram, i, env.Actor, p.Actor)
			}
			env.Actor = p.Actor
		}
		if p.Scope != "" {
			if env.Scope != "" && env.Scope != p.Scope {
				return nil, fmt.Errorf("%w: envelope %d scope %q does not match program scope %q",
					ErrInvalidProgram, i, env.Scope, p.Scope)
			}
			env.Scope = p.Scope
		}
		if err := env.Validate(); err != nil {
			return nil, fmt.Errorf("%w: envelope %d: %v", ErrInvalidProgram, i, err)
		}
		out[i] = env
	}
	return out, nil
}

// EvalResult is the output of evaluating a single Envelope against a GraphState.
type EvalResult struct {
	State     GraphState        `json:"state"`
	Node      *Node             `json:"node,omitempty"`
	Wire      *Wire             `json:"wire,omitempty"`
	Persisted PersistedEnvelope `json:"persisted"`
	Summary   string            `json:"summary"`
}

// ProgramResult is the output of evaluating an entire Program atomically.
type ProgramResult struct {
	State     GraphState          `json:"state"`
	Results   []EvalResult        `json:"results"`
	Persisted []PersistedEnvelope `json:"persisted"`
	Summary   string              `json:"summary"`
}

// PersistedEnvelope is a morphism log entry — an element of the free monoid.
// The morphism log IS the single source of truth. State is reconstructible by replay.
type PersistedEnvelope struct {
	Envelope Envelope  `json:"envelope"`
	IssuedAt time.Time `json:"issued_at"`
}

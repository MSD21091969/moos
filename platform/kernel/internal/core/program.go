package core

import (
	"fmt"
	"time"
)

func (program Program) Validate() error {
	if len(program.Envelopes) == 0 {
		return fmt.Errorf("%w: program must contain at least one envelope", ErrInvalidProgram)
	}
	_, err := program.normalizedEnvelopes()
	return err
}

func (program Program) normalizedEnvelopes() ([]Envelope, error) {
	normalized := make([]Envelope, len(program.Envelopes))
	for index, envelope := range program.Envelopes {
		if program.Actor != "" {
			if envelope.Actor != "" && envelope.Actor != program.Actor {
				return nil, fmt.Errorf("%w: envelope %d actor %q does not match program actor %q", ErrInvalidProgram, index, envelope.Actor, program.Actor)
			}
			envelope.Actor = program.Actor
		}
		if program.Scope != "" {
			if envelope.Scope != "" && envelope.Scope != program.Scope {
				return nil, fmt.Errorf("%w: envelope %d scope %q does not match program scope %q", ErrInvalidProgram, index, envelope.Scope, program.Scope)
			}
			envelope.Scope = program.Scope
		}
		if err := envelope.Validate(); err != nil {
			return nil, fmt.Errorf("%w: envelope %d: %v", ErrInvalidProgram, index, err)
		}
		normalized[index] = envelope
	}
	return normalized, nil
}

func EvaluateProgram(state GraphState, program Program, issuedAt time.Time) (ProgramResult, error) {
	return EvaluateProgramWithRegistry(state, program, issuedAt, nil)
}

func EvaluateProgramWithRegistry(state GraphState, program Program, issuedAt time.Time, registry *SemanticRegistry) (ProgramResult, error) {
	normalized, err := program.normalizedEnvelopes()
	if err != nil {
		return ProgramResult{}, err
	}

	workingState := state.Clone()
	results := make([]EvalResult, 0, len(normalized))
	persisted := make([]PersistedEnvelope, 0, len(normalized))
	for index, envelope := range normalized {
		result, err := EvaluateWithRegistry(workingState, envelope, issuedAt.Add(time.Duration(index)*time.Nanosecond), registry)
		if err != nil {
			return ProgramResult{}, err
		}
		workingState = result.State
		results = append(results, result)
		persisted = append(persisted, result.Persisted)
	}

	return ProgramResult{
		State:     workingState,
		Results:   results,
		Persisted: persisted,
		Summary:   fmt.Sprintf("program applied: %d morphisms", len(normalized)),
	}, nil
}

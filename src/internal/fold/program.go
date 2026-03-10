package fold

import (
	"fmt"
	"time"

	"moos/src/internal/cat"
	"moos/src/internal/operad"
)

// EvaluateProgram applies an atomic batch of envelopes. If any envelope fails,
// the entire program is rolled back (the input state is never mutated).
func EvaluateProgram(state cat.GraphState, program cat.Program, issuedAt time.Time) (cat.ProgramResult, error) {
	return EvaluateProgramWithRegistry(state, program, issuedAt, nil)
}

// EvaluateProgramWithRegistry applies an atomic batch with operad constraints.
func EvaluateProgramWithRegistry(state cat.GraphState, program cat.Program, issuedAt time.Time, registry *operad.Registry) (cat.ProgramResult, error) {
	normalized, err := program.NormalizedEnvelopes()
	if err != nil {
		return cat.ProgramResult{}, err
	}

	working := state.Clone()
	results := make([]cat.EvalResult, 0, len(normalized))
	persisted := make([]cat.PersistedEnvelope, 0, len(normalized))

	for i, env := range normalized {
		t := issuedAt.Add(time.Duration(i) * time.Nanosecond)
		result, err := EvaluateWithRegistry(working, env, t, registry)
		if err != nil {
			return cat.ProgramResult{}, err
		}
		working = result.State
		results = append(results, result)
		persisted = append(persisted, result.Persisted)
	}

	return cat.ProgramResult{
		State:     working,
		Results:   results,
		Persisted: persisted,
		Summary:   fmt.Sprintf("program applied: %d morphisms", len(normalized)),
	}, nil
}

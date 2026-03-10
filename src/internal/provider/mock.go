package provider

import "fmt"

// MockProvider echoes input content back. No real LLM calls.
type MockProvider struct {
	Name string
}

func (m MockProvider) Complete(req CompletionRequest) (CompletionResult, error) {
	if len(req.Messages) == 0 {
		return CompletionResult{}, fmt.Errorf("no messages provided")
	}
	last := req.Messages[len(req.Messages)-1]
	return CompletionResult{
		Content:    fmt.Sprintf("[mock:%s] echo: %s", m.Name, last.Content),
		TokensUsed: len(last.Content),
	}, nil
}

// MockBenchmark returns static scores for testing the benchmark functor path.
type MockBenchmark struct{}

// Score returns a static score for a given model + task.
func (m MockBenchmark) Score(model string, task string) map[string]float64 {
	return map[string]float64{
		"accuracy":         0.85,
		"compositionality": 0.90,
		"latency_seconds":  1.2,
		"token_cost":       150,
		"robustness":       0.80,
		"tool_fidelity":    0.75,
	}
}

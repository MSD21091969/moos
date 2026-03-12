package functor

import (
	"testing"

	"moos/platform/kernel/internal/cat"
)

func TestBenchmarkName(t *testing.T) {
	b := Benchmark{}
	if got := b.Name(); got != "FUN05_benchmark" {
		t.Errorf("Name() = %q, want FUN05_benchmark", got)
	}
}

func TestBenchmarkProjectEmpty(t *testing.T) {
	b := Benchmark{}
	result, err := b.Project(cat.NewGraphState())
	if err != nil {
		t.Fatal(err)
	}
	m := result.(map[string]BenchmarkResult)
	if len(m) != 0 {
		t.Errorf("expected empty map, got %d entries", len(m))
	}
}

func buildTestState() cat.GraphState {
	state := cat.NewGraphState()

	// Add a suite node.
	state.Nodes["urn:bench:suite:aa-intelligence-index"] = cat.Node{
		URN:    "urn:bench:suite:aa-intelligence-index",
		TypeID: "benchmark_suite",
		Payload: map[string]any{
			"name": "Artificial Analysis Intelligence Index",
		},
	}

	// Add score nodes.
	scores := []struct {
		urn  cat.URN
		name string
		dims map[string]any
	}{
		{
			urn:  "urn:bench:score:gemini-3.1-pro",
			name: "Gemini 3.1 Pro",
			dims: map[string]any{
				"intelligence_index": float64(57),
				"output_speed_tps":   float64(145),
				"latency_ttft_s":     float64(0.45),
			},
		},
		{
			urn:  "urn:bench:score:gpt-5.4-xhigh",
			name: "GPT-5.4 xhigh",
			dims: map[string]any{
				"intelligence_index": float64(57),
				"output_speed_tps":   float64(72),
				"latency_ttft_s":     float64(0.61),
			},
		},
		{
			urn:  "urn:bench:score:claude-opus-4-6",
			name: "Claude Opus 4.6",
			dims: map[string]any{
				"intelligence_index": float64(53),
				"output_speed_tps":   float64(54),
				"latency_ttft_s":     float64(0.48),
			},
		},
		{
			urn:  "urn:bench:score:mistral-large-2",
			name: "Mistral Large 2",
			dims: map[string]any{
				"intelligence_index": float64(31),
				"output_speed_tps":   float64(70),
				"latency_ttft_s":     float64(0.33),
			},
		},
	}

	for _, s := range scores {
		state.Nodes[s.urn] = cat.Node{
			URN:    s.urn,
			TypeID: "benchmark_score",
			Payload: map[string]any{
				"name":       s.name,
				"dimensions": s.dims,
			},
		}
		// Wire: score --BENCHMARKED_BY--> suite
		wk := cat.WireKey(s.urn, "BENCHMARKED_BY", "urn:bench:suite:aa-intelligence-index", "BENCHMARKED_BY")
		state.Wires[wk] = cat.Wire{
			SourceURN:  s.urn,
			SourcePort: "BENCHMARKED_BY",
			TargetURN:  "urn:bench:suite:aa-intelligence-index",
			TargetPort: "BENCHMARKED_BY",
		}
	}

	return state
}

func TestBenchmarkProjectAllSuites(t *testing.T) {
	b := Benchmark{}
	state := buildTestState()
	result, err := b.Project(state)
	if err != nil {
		t.Fatal(err)
	}

	m := result.(map[string]BenchmarkResult)
	if len(m) != 1 {
		t.Fatalf("expected 1 suite, got %d", len(m))
	}

	br := m["urn:bench:suite:aa-intelligence-index"]
	if br.SuiteName != "Artificial Analysis Intelligence Index" {
		t.Errorf("SuiteName = %q", br.SuiteName)
	}
	if br.ProviderCount != 4 {
		t.Errorf("ProviderCount = %d, want 4", br.ProviderCount)
	}
}

func TestBenchmarkRankings(t *testing.T) {
	b := Benchmark{}
	state := buildTestState()
	result, err := b.Project(state)
	if err != nil {
		t.Fatal(err)
	}

	br := result.(map[string]BenchmarkResult)["urn:bench:suite:aa-intelligence-index"]

	// Rankings by intelligence_index desc, then name asc (case-sensitive).
	// 57 tied: "GPT-5.4 xhigh" < "Gemini 3.1 Pro" (ASCII: 'P' < 'e'), 53 (Claude Opus 4.6), 31 (Mistral Large 2)
	want := []string{"GPT-5.4 xhigh", "Gemini 3.1 Pro", "Claude Opus 4.6", "Mistral Large 2"}
	if len(br.Rankings) != len(want) {
		t.Fatalf("rankings length = %d, want %d", len(br.Rankings), len(want))
	}
	for i, w := range want {
		if br.Rankings[i] != w {
			t.Errorf("rankings[%d] = %q, want %q", i, br.Rankings[i], w)
		}
	}
}

func TestBenchmarkDistributions(t *testing.T) {
	b := Benchmark{}
	state := buildTestState()
	result, err := b.Project(state)
	if err != nil {
		t.Fatal(err)
	}

	br := result.(map[string]BenchmarkResult)["urn:bench:suite:aa-intelligence-index"]

	// Find intelligence_index distribution.
	var idxDist *ScoreDistribution
	for i, d := range br.Distributions {
		if d.Dimension == "intelligence_index" {
			idxDist = &br.Distributions[i]
			break
		}
	}
	if idxDist == nil {
		t.Fatal("intelligence_index distribution not found")
	}

	if idxDist.Min != 31 {
		t.Errorf("Min = %v, want 31", idxDist.Min)
	}
	if idxDist.Max != 57 {
		t.Errorf("Max = %v, want 57", idxDist.Max)
	}
	if idxDist.Count != 4 {
		t.Errorf("Count = %v, want 4", idxDist.Count)
	}
	// Mean: (57+57+53+31)/4 = 49.5
	if idxDist.Mean != 49.5 {
		t.Errorf("Mean = %v, want 49.5", idxDist.Mean)
	}
}

func TestBenchmarkEquivalenceClasses(t *testing.T) {
	b := Benchmark{}
	state := buildTestState()
	result, err := b.Project(state)
	if err != nil {
		t.Fatal(err)
	}

	br := result.(map[string]BenchmarkResult)["urn:bench:suite:aa-intelligence-index"]

	// Expected: frontier [55,101): Gemini 3.1 Pro, GPT-5.4 xhigh
	//           high [45,55): Claude Opus 4.6
	//           mid [30,45): Mistral Large 2
	classes := make(map[string][]string)
	for _, ec := range br.EquivalenceClasses {
		classes[ec.Label] = ec.Providers
	}

	if len(classes["frontier"]) != 2 {
		t.Errorf("frontier class has %d providers, want 2", len(classes["frontier"]))
	}
	if len(classes["high"]) != 1 || classes["high"][0] != "Claude Opus 4.6" {
		t.Errorf("high class = %v, want [Claude Opus 4.6]", classes["high"])
	}
	if len(classes["mid"]) != 1 || classes["mid"][0] != "Mistral Large 2" {
		t.Errorf("mid class = %v, want [Mistral Large 2]", classes["mid"])
	}
	if _, hasLow := classes["low"]; hasLow {
		t.Error("unexpected low class (should be filtered)")
	}
}

func TestBenchmarkProjectSuiteNotFound(t *testing.T) {
	b := Benchmark{}
	_, err := b.ProjectSuite(cat.NewGraphState(), "nonexistent")
	if err == nil {
		t.Error("expected error for nonexistent suite")
	}
}

func TestBenchmarkProjectSuiteSpecific(t *testing.T) {
	b := Benchmark{}
	state := buildTestState()
	br, err := b.ProjectSuite(state, "urn:bench:suite:aa-intelligence-index")
	if err != nil {
		t.Fatal(err)
	}
	if br.ProviderCount != 4 {
		t.Errorf("ProviderCount = %d, want 4", br.ProviderCount)
	}
}

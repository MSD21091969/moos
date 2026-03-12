package functor

import (
	"fmt"
	"math"
	"sort"

	"moos/platform/kernel/internal/cat"
)

// Benchmark implements Projector for FUN05: F_bench: C_Provider → Met.
// It extracts benchmark_score nodes from the graph, groups them by suite,
// and computes score distributions, provider rankings, and equivalence classes.
type Benchmark struct{}

// Name returns the functor identifier.
func (b Benchmark) Name() string { return "FUN05_benchmark" }

// Project computes the full BenchmarkResult for every suite found in the graph.
// The return value is map[string]BenchmarkResult keyed by suite URN.
func (b Benchmark) Project(state cat.GraphState) (any, error) {
	results := make(map[string]*BenchmarkResult)

	// Pass 1: collect suites.
	for _, n := range state.Nodes {
		if n.TypeID == "benchmark_suite" {
			name, _ := n.Payload["name"].(string)
			results[string(n.URN)] = &BenchmarkResult{
				Suite:     string(n.URN),
				SuiteName: name,
			}
		}
	}

	// Pass 2: collect scores and resolve suite via BENCHMARKED_BY wires.
	for _, n := range state.Nodes {
		if n.TypeID != "benchmark_score" {
			continue
		}
		suiteURN := findWireTarget(state, n.URN, "BENCHMARKED_BY")
		if suiteURN == "" {
			continue
		}
		br, ok := results[string(suiteURN)]
		if !ok {
			continue
		}

		name, _ := n.Payload["name"].(string)
		provRef, _ := n.Payload["provider_ref"].(string)
		dims := extractDimensions(n.Payload)

		br.Providers = append(br.Providers, ProviderScore{
			ID:          string(n.URN),
			Name:        name,
			ProviderRef: provRef,
			SuiteRef:    string(suiteURN),
			Dimensions:  dims,
		})
	}

	// Pass 3: compute derived fields per suite.
	out := make(map[string]BenchmarkResult, len(results))
	for k, br := range results {
		br.ProviderCount = len(br.Providers)
		br.Rankings = computeRankings(br.Providers)
		br.Distributions = computeDistributions(br.Providers)
		br.EquivalenceClasses = computeEquivalenceClasses(br.Providers)
		out[k] = *br
	}
	return out, nil
}

// ProjectSuite computes BenchmarkResult for a single suite URN.
func (b Benchmark) ProjectSuite(state cat.GraphState, suiteURN string) (BenchmarkResult, error) {
	all, err := b.Project(state)
	if err != nil {
		return BenchmarkResult{}, err
	}
	m := all.(map[string]BenchmarkResult)
	br, ok := m[suiteURN]
	if !ok {
		return BenchmarkResult{}, fmt.Errorf("suite %q not found in graph", suiteURN)
	}
	return br, nil
}

// findWireTarget returns the target URN of the first wire from src with the given source port.
func findWireTarget(state cat.GraphState, src cat.URN, port cat.Port) cat.URN {
	for _, w := range state.Wires {
		if w.SourceURN == src && w.SourcePort == port {
			return w.TargetURN
		}
	}
	return ""
}

// extractDimensions pulls the "dimensions" sub-map from a node payload.
func extractDimensions(payload map[string]any) map[string]any {
	if d, ok := payload["dimensions"].(map[string]any); ok {
		return d
	}
	return map[string]any{}
}

// computeRankings sorts providers by intelligence_index (desc), falling back to name.
func computeRankings(providers []ProviderScore) []string {
	type ranked struct {
		name  string
		score float64
	}
	var items []ranked
	for _, p := range providers {
		s := toFloat64(p.Dimensions["intelligence_index"])
		items = append(items, ranked{name: p.Name, score: s})
	}
	sort.Slice(items, func(i, j int) bool {
		if items[i].score != items[j].score {
			return items[i].score > items[j].score
		}
		return items[i].name < items[j].name
	})
	out := make([]string, len(items))
	for i, it := range items {
		out[i] = it.name
	}
	return out
}

// computeDistributions calculates min/max/mean for each dimension present.
func computeDistributions(providers []ProviderScore) []ScoreDistribution {
	if len(providers) == 0 {
		return nil
	}

	// Collect all dimension keys.
	keys := map[string]bool{}
	for _, p := range providers {
		for k := range p.Dimensions {
			keys[k] = true
		}
	}

	sorted := make([]string, 0, len(keys))
	for k := range keys {
		sorted = append(sorted, k)
	}
	sort.Strings(sorted)

	var out []ScoreDistribution
	for _, dim := range sorted {
		var vals []float64
		for _, p := range providers {
			if v, ok := p.Dimensions[dim]; ok {
				vals = append(vals, toFloat64(v))
			}
		}
		if len(vals) == 0 {
			continue
		}
		mn, mx := vals[0], vals[0]
		sum := 0.0
		for _, v := range vals {
			sum += v
			if v < mn {
				mn = v
			}
			if v > mx {
				mx = v
			}
		}
		out = append(out, ScoreDistribution{
			Dimension: dim,
			Min:       mn,
			Max:       mx,
			Mean:      math.Round(sum/float64(len(vals))*100) / 100,
			Count:     len(vals),
		})
	}
	return out
}

// computeEquivalenceClasses partitions providers by intelligence_index bands.
// Bands: [0,30) low, [30,45) mid, [45,55) high, [55,100] frontier.
func computeEquivalenceClasses(providers []ProviderScore) []EquivalenceClass {
	bands := []EquivalenceClass{
		{Label: "frontier", Lower: 55, Upper: 101},
		{Label: "high", Lower: 45, Upper: 55},
		{Label: "mid", Lower: 30, Upper: 45},
		{Label: "low", Lower: 0, Upper: 30},
	}

	for i := range bands {
		for _, p := range providers {
			idx := toFloat64(p.Dimensions["intelligence_index"])
			if idx >= bands[i].Lower && idx < bands[i].Upper {
				bands[i].Providers = append(bands[i].Providers, p.Name)
			}
		}
		sort.Strings(bands[i].Providers)
	}

	// Filter out empty bands.
	var out []EquivalenceClass
	for _, b := range bands {
		if len(b.Providers) > 0 {
			out = append(out, b)
		}
	}
	return out
}

// toFloat64 converts json.Number, float64, int, etc. to float64.
func toFloat64(v any) float64 {
	switch n := v.(type) {
	case float64:
		return n
	case int:
		return float64(n)
	case int64:
		return float64(n)
	default:
		return 0
	}
}

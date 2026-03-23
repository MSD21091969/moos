// Package functor defines read-path projections: F: C → D.
//
// Per the categorical specification, functors are structure-preserving
// maps from the graph category C to codomain categories.
// Functor outputs are NEVER ground truth (S4 invariant).
package functor

import "moos/platform/kernel/internal/cat"

// Projector is the common interface for all functors F: C → D.
type Projector interface {
	Name() string
	Project(state cat.GraphState) (any, error)
}

// ProviderScore holds a single provider's benchmark dimensions.
type ProviderScore struct {
	ID          string         `json:"id"`
	Name        string         `json:"name"`
	ProviderRef string         `json:"provider_ref"`
	SuiteRef    string         `json:"suite_ref"`
	Dimensions  map[string]any `json:"dimensions"`
}

// EquivalenceClass groups providers by a score band.
// [P]_F = {providers whose primary dimension falls in [Lower, Upper)}.
type EquivalenceClass struct {
	Label     string   `json:"label"`
	Lower     float64  `json:"lower"`
	Upper     float64  `json:"upper"`
	Providers []string `json:"providers"`
}

// ScoreDistribution summarises a single dimension across all providers.
type ScoreDistribution struct {
	Dimension string  `json:"dimension"`
	Min       float64 `json:"min"`
	Max       float64 `json:"max"`
	Mean      float64 `json:"mean"`
	Count     int     `json:"count"`
}

// BenchmarkResult is the codomain object of FUN05: F_bench → Met.
type BenchmarkResult struct {
	Suite              string              `json:"suite"`
	SuiteName          string              `json:"suite_name"`
	ProviderCount      int                 `json:"provider_count"`
	Providers          []ProviderScore     `json:"providers"`
	Rankings           []string            `json:"rankings"`
	Distributions      []ScoreDistribution `json:"distributions"`
	EquivalenceClasses []EquivalenceClass  `json:"equivalence_classes"`
}

// CalendarEntry is an event-shaped projection object for FUN06.
// It is a read model only (S4 invariant).
type CalendarEntry struct {
	ID          string `json:"id"`
	Summary     string `json:"summary"`
	Description string `json:"description,omitempty"`
	Start       string `json:"start,omitempty"`
	End         string `json:"end,omitempty"`
	Status      string `json:"status"`
	Color       int    `json:"color"`
	Source      string `json:"source"`
	Kind        string `json:"kind"`
}

// CalendarProjection is the codomain object of FUN06: F_cal: C → GCal.
type CalendarProjection struct {
	GeneratedAt string          `json:"generated_at"`
	Entries     []CalendarEntry `json:"entries"`
}

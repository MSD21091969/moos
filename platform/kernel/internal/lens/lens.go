// Package lens provides composable, pure graph filtering predicates.
//
// A lens is a read-path transformation: Apply(state, spec) returns a filtered
// GraphState without mutating the input. This package has no IO.
package lens

import (
	"net/url"
	"strconv"
	"strings"

	"moos/platform/kernel/internal/cat"
)

// Rule is a single conjunctive predicate over graph nodes.
//
// Within one rule, non-empty fields are AND-ed together.
// For list fields (Kind, Stratum, Category), values inside the list are OR-ed.
type Rule struct {
	Kind         []cat.TypeID  `json:"kind,omitempty"`
	Stratum      []cat.Stratum `json:"stratum,omitempty"`
	Category     []string      `json:"category,omitempty"`
	Port         string        `json:"port,omitempty"`
	Neighborhood *Neighborhood `json:"neighborhood,omitempty"`
}

// Neighborhood defines a bidirectional BFS neighborhood rule.
type Neighborhood struct {
	Origin cat.URN `json:"origin"`
	Depth  int     `json:"depth"`
}

// LensSpec composes multiple rules.
//
// Mode "intersect" (default) requires nodes to match all rules.
// Mode "union" keeps nodes matching any rule.
type LensSpec struct {
	Rules []Rule `json:"rules"`
	Mode  string `json:"mode,omitempty"`
}

// Apply filters state by spec and returns a new GraphState.
//
// Result contains only matching nodes and wires where both endpoints are
// included in the matched node set.
func Apply(state cat.GraphState, spec LensSpec) cat.GraphState {
	if len(spec.Rules) == 0 {
		return state.Clone()
	}

	all := allNodeSet(state)
	mode := strings.ToLower(strings.TrimSpace(spec.Mode))
	if mode == "" {
		mode = "intersect"
	}

	var matched map[cat.URN]bool
	if mode == "union" {
		matched = map[cat.URN]bool{}
		for _, r := range spec.Rules {
			ruleSet := applyRule(state, all, r)
			matched = union(matched, ruleSet)
		}
	} else {
		matched = copySet(all)
		for _, r := range spec.Rules {
			ruleSet := applyRule(state, all, r)
			matched = intersect(matched, ruleSet)
		}
	}

	out := cat.NewGraphState()
	for urn := range matched {
		if n, ok := state.Nodes[urn]; ok {
			out.Nodes[urn] = n
		}
	}
	for k, w := range state.Wires {
		if matched[w.SourceURN] && matched[w.TargetURN] {
			out.Wires[k] = w
		}
	}
	return out
}

// ParseQueryParams builds a one-rule LensSpec from URL query params.
//
// Supported params: kind, stratum, category, port, neighborhood, depth, mode.
func ParseQueryParams(v url.Values) LensSpec {
	r := Rule{}

	for _, s := range splitCSV(v["kind"]) {
		r.Kind = append(r.Kind, cat.TypeID(s))
	}
	for _, s := range splitCSV(v["stratum"]) {
		r.Stratum = append(r.Stratum, cat.Stratum(s))
	}
	for _, s := range splitCSV(v["category"]) {
		r.Category = append(r.Category, strings.ToLower(s))
	}
	r.Port = strings.TrimSpace(v.Get("port"))

	if n := strings.TrimSpace(v.Get("neighborhood")); n != "" {
		depth := 1
		if ds := strings.TrimSpace(v.Get("depth")); ds != "" {
			if d, err := strconv.Atoi(ds); err == nil {
				depth = d
			}
		}
		r.Neighborhood = &Neighborhood{Origin: cat.URN(n), Depth: depth}
	}

	hasFilter := len(r.Kind) > 0 || len(r.Stratum) > 0 || len(r.Category) > 0 ||
		r.Port != "" || r.Neighborhood != nil
	if !hasFilter {
		return LensSpec{Mode: strings.ToLower(strings.TrimSpace(v.Get("mode")))}
	}

	return LensSpec{
		Rules: []Rule{r},
		Mode:  strings.ToLower(strings.TrimSpace(v.Get("mode"))),
	}
}

func applyRule(state cat.GraphState, all map[cat.URN]bool, r Rule) map[cat.URN]bool {
	set := copySet(all)

	if len(r.Kind) > 0 {
		allowed := map[cat.TypeID]bool{}
		for _, k := range r.Kind {
			allowed[k] = true
		}
		next := map[cat.URN]bool{}
		for urn := range set {
			n := state.Nodes[urn]
			if allowed[n.TypeID] {
				next[urn] = true
			}
		}
		set = next
	}

	if len(r.Stratum) > 0 {
		allowed := map[cat.Stratum]bool{}
		for _, s := range r.Stratum {
			allowed[s] = true
		}
		next := map[cat.URN]bool{}
		for urn := range set {
			n := state.Nodes[urn]
			if allowed[n.Stratum] {
				next[urn] = true
			}
		}
		set = next
	}

	if len(r.Category) > 0 {
		allowed := map[string]bool{}
		for _, c := range r.Category {
			allowed[strings.ToLower(c)] = true
		}
		next := map[cat.URN]bool{}
		for urn := range set {
			n := state.Nodes[urn]
			if allowed[broadCategory(n.TypeID)] {
				next[urn] = true
			}
		}
		set = next
	}

	if strings.TrimSpace(r.Port) != "" {
		port := strings.ToUpper(strings.TrimSpace(r.Port))
		hasPort := map[cat.URN]bool{}
		for _, w := range state.Wires {
			if strings.ToUpper(string(w.SourcePort)) == port || strings.ToUpper(string(w.TargetPort)) == port {
				hasPort[w.SourceURN] = true
				hasPort[w.TargetURN] = true
			}
		}
		next := map[cat.URN]bool{}
		for urn := range set {
			if hasPort[urn] {
				next[urn] = true
			}
		}
		set = next
	}

	if r.Neighborhood != nil {
		n := neighborhoodSet(state, r.Neighborhood.Origin, r.Neighborhood.Depth)
		set = intersect(set, n)
	}

	return set
}

func neighborhoodSet(state cat.GraphState, origin cat.URN, depth int) map[cat.URN]bool {
	out := map[cat.URN]bool{}
	if _, ok := state.Nodes[origin]; !ok {
		return out
	}
	if depth < 0 {
		depth = 0
	}
	if depth > 10 {
		depth = 10
	}

	type qn struct {
		urn cat.URN
		d   int
	}
	queue := []qn{{urn: origin, d: 0}}
	out[origin] = true

	for len(queue) > 0 {
		cur := queue[0]
		queue = queue[1:]
		if cur.d >= depth {
			continue
		}
		for _, w := range state.Wires {
			if w.SourceURN == cur.urn {
				if !out[w.TargetURN] {
					out[w.TargetURN] = true
					queue = append(queue, qn{urn: w.TargetURN, d: cur.d + 1})
				}
			}
			if w.TargetURN == cur.urn {
				if !out[w.SourceURN] {
					out[w.SourceURN] = true
					queue = append(queue, qn{urn: w.SourceURN, d: cur.d + 1})
				}
			}
		}
	}

	return out
}

func splitCSV(values []string) []string {
	out := make([]string, 0)
	for _, raw := range values {
		for _, p := range strings.Split(raw, ",") {
			s := strings.TrimSpace(p)
			if s != "" {
				out = append(out, s)
			}
		}
	}
	return out
}

func allNodeSet(state cat.GraphState) map[cat.URN]bool {
	m := make(map[cat.URN]bool, len(state.Nodes))
	for urn := range state.Nodes {
		m[urn] = true
	}
	return m
}

func copySet(in map[cat.URN]bool) map[cat.URN]bool {
	out := make(map[cat.URN]bool, len(in))
	for k := range in {
		out[k] = true
	}
	return out
}

func intersect(a, b map[cat.URN]bool) map[cat.URN]bool {
	out := map[cat.URN]bool{}
	for k := range a {
		if b[k] {
			out[k] = true
		}
	}
	return out
}

func union(a, b map[cat.URN]bool) map[cat.URN]bool {
	out := copySet(a)
	for k := range b {
		out[k] = true
	}
	return out
}

// broadCategory maps TypeID to ontology broad_category labels.
func broadCategory(tid cat.TypeID) string {
	switch tid {
	case "user", "collider_admin", "superadmin", "agent_spec", "agent_session":
		return "identity"
	case "app_template", "node_container", "prg_task", "calendar_event", "keep_note", "channel_message", "delegation_task":
		return "structure"
	case "agnostic_model", "system_tool", "compute_resource", "provider":
		return "compute"
	case "ui_lens", "runtime_surface":
		return "surface"
	case "protocol_adapter":
		return "protocol"
	case "infra_service":
		return "infra"
	case "memory_store":
		return "memory"
	case "platform_config", "workstation_config":
		return "platform"
	case "preference":
		return "config"
	case "benchmark_suite", "benchmark_task", "benchmark_score":
		return "evaluation"
	case "industry_entity":
		return "industry"
	case "ontology_term", "ptp_family":
		return "ontology"
	default:
		return "unknown"
	}
}

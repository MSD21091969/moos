package hydration

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"moos/platform/kernel/internal/cat"
)

const ontologyTemplateTypeID = "ontology_term"

type ontology struct {
	Objects    []ontologyObject     `json:"objects"`
	Categories ontologyCategorySets `json:"categories"`
}

type ontologyObject struct {
	ID string `json:"id"`
}

type ontologyCategorySets struct {
	Core              []ontologyCategory `json:"core"`
	StratumChain      []ontologyCategory `json:"stratum_chain"`
	HydrationPipeline []ontologyCategory `json:"hydration_pipeline"`
	FunctorCodomains  []ontologyCategory `json:"functor_codomains"`
	CrossProvider     []ontologyCategory `json:"cross_provider"`
	Glossary          []ontologyGlossary `json:"glossary"`
}

type ontologyCategory struct {
	ID string `json:"id"`
}

type ontologyGlossary struct {
	ID string `json:"id"`
}

// HydrateFromOntology reads ontology.json and synthesizes S1 ontology_term nodes
// for glossary terms, category satellites, and object kind references.
func HydrateFromOntology(ontologyPath string) ([]cat.Node, error) {
	data, err := os.ReadFile(filepath.Clean(ontologyPath))
	if err != nil {
		return nil, fmt.Errorf("read ontology: %w", err)
	}

	var onto ontology
	if err := json.Unmarshal(data, &onto); err != nil {
		return nil, fmt.Errorf("parse ontology: %w", err)
	}

	groupedCategories := [][]ontologyCategory{
		onto.Categories.Core,
		onto.Categories.StratumChain,
		onto.Categories.HydrationPipeline,
		onto.Categories.FunctorCodomains,
		onto.Categories.CrossProvider,
	}

	nodes := make([]cat.Node, 0, len(onto.Objects)+len(onto.Categories.Glossary))
	seen := make(map[cat.URN]struct{})

	for _, g := range onto.Categories.Glossary {
		suffix := glossarySuffix(g.ID)
		if suffix == "" {
			continue
		}
		addOntologyNode(seen, cat.URN("urn:moos:cat:"+suffix), &nodes)
	}

	for _, group := range groupedCategories {
		for _, c := range group {
			if c.ID == "" {
				continue
			}
			addOntologyNode(seen, cat.URN("urn:moos:cat:"+c.ID), &nodes)
		}
	}

	for _, o := range onto.Objects {
		if o.ID == "" {
			continue
		}
		addOntologyNode(seen, cat.URN("urn:moos:obj:"+o.ID), &nodes)
	}

	return nodes, nil
}

func addOntologyNode(seen map[cat.URN]struct{}, urn cat.URN, out *[]cat.Node) {
	if _, ok := seen[urn]; ok {
		return
	}
	seen[urn] = struct{}{}
	*out = append(*out, cat.Node{
		URN:     urn,
		TypeID:  cat.TypeID(ontologyTemplateTypeID),
		Stratum: cat.S1,
	})
}

func glossarySuffix(id string) string {
	trimmed := strings.TrimSpace(id)
	if trimmed == "" {
		return ""
	}
	if idx := strings.LastIndex(trimmed, ":"); idx >= 0 && idx+1 < len(trimmed) {
		return strings.TrimSpace(trimmed[idx+1:])
	}
	return trimmed
}

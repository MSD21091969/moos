package hydration_test

import (
	"os"
	"path/filepath"
	"regexp"
	"testing"

	"moos/platform/kernel/internal/cat"
	"moos/platform/kernel/internal/hydration"
)

func TestHydrateFromOntology_NodeCount(t *testing.T) {
	ontologyPath := writeOntologyFixture(t)

	nodes, err := hydration.HydrateFromOntology(ontologyPath)
	if err != nil {
		t.Fatalf("HydrateFromOntology: %v", err)
	}

	objects := 2
	allCategoryGroups := 5 // core, stratum_chain, hydration_pipeline, functor_codomains, cross_provider
	glossary := 2
	want := objects + allCategoryGroups + glossary

	if got := len(nodes); got != want {
		t.Fatalf("node count = %d, want %d", got, want)
	}
}

func TestHydrateFromOntology_URNPatterns(t *testing.T) {
	ontologyPath := writeOntologyFixture(t)

	nodes, err := hydration.HydrateFromOntology(ontologyPath)
	if err != nil {
		t.Fatalf("HydrateFromOntology: %v", err)
	}

	catPattern := regexp.MustCompile(`^urn:moos:cat:(CAT\d{2}|[a-z\-]+)$`)
	objPattern := regexp.MustCompile(`^urn:moos:obj:OBJ\d{2}$`)

	for _, n := range nodes {
		urn := string(n.URN)
		switch {
		case objPattern.MatchString(urn):
			continue
		case catPattern.MatchString(urn):
			continue
		default:
			t.Fatalf("unexpected URN pattern: %s", urn)
		}
	}
}

func TestHydrateFromOntology_AllS1(t *testing.T) {
	ontologyPath := writeOntologyFixture(t)

	nodes, err := hydration.HydrateFromOntology(ontologyPath)
	if err != nil {
		t.Fatalf("HydrateFromOntology: %v", err)
	}

	for _, n := range nodes {
		if n.Stratum != cat.S1 {
			t.Fatalf("node %s stratum = %s, want %s", n.URN, n.Stratum, cat.S1)
		}
	}
}

func writeOntologyFixture(t *testing.T) string {
	t.Helper()

	dir := t.TempDir()
	path := filepath.Join(dir, "ontology.json")

	const fixture = `{
  "objects": [
    {"id": "OBJ01"},
    {"id": "OBJ02"}
  ],
  "categories": {
    "core": [{"id": "CAT01"}],
    "stratum_chain": [{"id": "CAT06"}],
    "hydration_pipeline": [{"id": "CAT09"}],
    "functor_codomains": [{"id": "CAT13"}],
    "cross_provider": [{"id": "CAT17"}],
    "glossary": [
      {"id": "urn:moos:cat:object"},
      {"id": "urn:moos:cat:natural-transformation"}
    ]
  }
}`

	if err := os.WriteFile(path, []byte(fixture), 0o600); err != nil {
		t.Fatalf("write ontology fixture: %v", err)
	}

	return path
}

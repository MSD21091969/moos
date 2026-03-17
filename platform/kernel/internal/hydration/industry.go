package hydration

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strings"

	"moos/platform/kernel/internal/cat"
	"moos/platform/kernel/internal/shell"
)

type sourceRegistry struct {
	Entries []sourceEntry `json:"entries"`
}

type sourceEntry struct {
	ID     string `json:"id"`
	Domain string `json:"domain"`
}

type industryFile struct {
	Domain     string           `json:"domain"`
	Source     string           `json:"source"`
	Entries    []map[string]any `json:"entries"`
	Categories map[string]any   `json:"categories"`
}

type instanceIndex struct {
	byURN  map[string]struct{}
	byRef  map[string]string
	byName map[string]string
}

func HydrateIndustry(kbRoot string, rt *shell.Runtime) error {
	industryDir := filepath.Join(kbRoot, "industry")
	items, err := os.ReadDir(industryDir)
	if err != nil {
		return fmt.Errorf("read industry dir: %w", err)
	}

	sourceByDomain := loadSourceByDomain(kbRoot)
	idx := buildInstanceIndex(kbRoot)

	for _, item := range items {
		if item.IsDir() || filepath.Ext(item.Name()) != ".json" {
			continue
		}
		path := filepath.Join(industryDir, item.Name())
		if err := hydrateIndustryFile(path, sourceByDomain, idx, rt); err != nil {
			log.Printf("[hydration] industry %s: %v", item.Name(), err)
		}
	}

	return nil
}

func hydrateIndustryFile(path string, sourceByDomain map[string]string, idx instanceIndex, rt *shell.Runtime) error {
	data, err := os.ReadFile(filepath.Clean(path))
	if err != nil {
		return fmt.Errorf("read file: %w", err)
	}

	var file industryFile
	if err := json.Unmarshal(data, &file); err != nil {
		return fmt.Errorf("parse file: %w", err)
	}

	domain := strings.TrimSpace(file.Domain)
	if domain == "" {
		domain = strings.TrimSuffix(filepath.Base(path), filepath.Ext(path))
	}

	sourceURN := strings.TrimSpace(file.Source)
	if sourceURN == "" {
		sourceURN = sourceByDomain[domain]
	}

	entries := collectIndustryEntries(file)
	for _, entry := range entries {
		id := strField(entry, "id")
		if id == "" {
			continue
		}

		indURN := industryURN(domain, id)
		env := cat.Envelope{
			Type:  cat.ADD,
			Actor: cat.URN(demoSeederURN),
			Add: &cat.AddPayload{
				URN:     cat.URN(indURN),
				TypeID:  "industry_entity",
				Stratum: cat.S0,
				Payload: map[string]any{
					"domain": domain,
					"source": sourceURN,
					"entry":  entry,
				},
			},
		}
		if err := rt.SeedIfAbsent(env); err != nil {
			log.Printf("[hydration] industry add %s: %v", indURN, err)
		}

		if sourceURN != "" {
			if err := rt.SeedIfAbsent(cat.Envelope{
				Type:  cat.LINK,
				Actor: cat.URN(demoSeederURN),
				Link: &cat.LinkPayload{
					SourceURN:  cat.URN(sourceURN),
					SourcePort: "owns",
					TargetURN:  cat.URN(indURN),
					TargetPort: "child",
				},
			}); err != nil {
				log.Printf("[hydration] industry source link %s -> %s: %v", sourceURN, indURN, err)
			}
		}

		targetURN := resolveInstanceTarget(entry, idx)
		if targetURN != "" {
			if err := rt.SeedIfAbsent(cat.Envelope{
				Type:  cat.LINK,
				Actor: cat.URN(demoSeederURN),
				Link: &cat.LinkPayload{
					SourceURN:  cat.URN(indURN),
					SourcePort: "classifies",
					TargetURN:  cat.URN(targetURN),
					TargetPort: "source",
				},
			}); err != nil {
				log.Printf("[hydration] industry classify link %s -> %s: %v", indURN, targetURN, err)
			}
		}
	}

	return nil
}

func collectIndustryEntries(file industryFile) []map[string]any {
	entries := make([]map[string]any, 0, len(file.Entries))
	entries = append(entries, file.Entries...)

	for _, raw := range file.Categories {
		arr, ok := raw.([]any)
		if !ok {
			continue
		}
		for _, item := range arr {
			entry, ok := item.(map[string]any)
			if !ok {
				continue
			}
			entries = append(entries, entry)
		}
	}
	return entries
}

func loadSourceByDomain(kbRoot string) map[string]string {
	out := map[string]string{}
	path := filepath.Join(kbRoot, "superset", "sources.json")
	data, err := os.ReadFile(filepath.Clean(path))
	if err != nil {
		return out
	}
	var reg sourceRegistry
	if err := json.Unmarshal(data, &reg); err != nil {
		return out
	}
	for _, e := range reg.Entries {
		d := strings.TrimSpace(e.Domain)
		if d == "" || strings.TrimSpace(e.ID) == "" {
			continue
		}
		if _, exists := out[d]; !exists {
			out[d] = e.ID
		}
	}
	return out
}

func buildInstanceIndex(kbRoot string) instanceIndex {
	idx := instanceIndex{
		byURN:  map[string]struct{}{},
		byRef:  map[string]string{},
		byName: map[string]string{},
	}

	instDir := filepath.Join(kbRoot, "instances")
	items, err := os.ReadDir(instDir)
	if err != nil {
		return idx
	}

	for _, item := range items {
		if item.IsDir() || filepath.Ext(item.Name()) != ".json" {
			continue
		}
		path := filepath.Join(instDir, item.Name())
		data, err := os.ReadFile(filepath.Clean(path))
		if err != nil {
			continue
		}
		var rec instanceRecord
		if err := json.Unmarshal(data, &rec); err != nil {
			continue
		}
		for _, entry := range rec.Entries {
			urn := strField(entry, "id")
			if urn == "" {
				continue
			}
			idx.byURN[urn] = struct{}{}

			if name := strings.ToLower(strings.TrimSpace(strField(entry, "name"))); name != "" {
				if _, exists := idx.byName[name]; !exists {
					idx.byName[name] = urn
				}
			}

			for key, value := range entry {
				s, ok := value.(string)
				if !ok {
					continue
				}
				s = strings.TrimSpace(s)
				if s == "" {
					continue
				}
				if key == "source" || key == "industry_source" || strings.HasSuffix(key, "_ref") {
					idx.byRef[s] = urn
				}
			}
		}
	}

	return idx
}

func resolveInstanceTarget(entry map[string]any, idx instanceIndex) string {
	candidates := []string{}
	if id := strField(entry, "id"); id != "" {
		candidates = append(candidates, id)
		if conv := industryRefToInstanceURN(id); conv != "" {
			candidates = append(candidates, conv)
		}
	}
	for key, value := range entry {
		if !strings.HasSuffix(key, "_ref") {
			continue
		}
		ref, ok := value.(string)
		if !ok {
			continue
		}
		ref = strings.TrimSpace(ref)
		if ref == "" {
			continue
		}
		candidates = append(candidates, ref)
		if conv := industryRefToInstanceURN(ref); conv != "" {
			candidates = append(candidates, conv)
		}
	}

	for _, c := range candidates {
		if _, ok := idx.byURN[c]; ok {
			return c
		}
		if urn, ok := idx.byRef[c]; ok {
			return urn
		}
	}

	if name := strings.ToLower(strings.TrimSpace(strField(entry, "name"))); name != "" {
		if urn, ok := idx.byName[name]; ok {
			return urn
		}
	}

	return ""
}

func industryURN(domain, id string) string {
	cleanDomain := slug(strings.TrimSpace(domain))
	if cleanDomain == "" {
		cleanDomain = "unknown"
	}
	cleanID := slug(strings.TrimSpace(id))
	return "urn:moos:industry:" + cleanDomain + ":" + cleanID
}

func industryRefToInstanceURN(ref string) string {
	trimmed := strings.TrimSpace(ref)
	if !strings.HasPrefix(trimmed, "ind:") {
		return ""
	}
	parts := strings.Split(trimmed, ":")
	if len(parts) < 3 {
		return ""
	}
	prefix := parts[1]
	suffix := strings.Join(parts[2:], ":")
	switch prefix {
	case "provider":
		return "urn:moos:provider:" + suffix
	case "benchmark":
		return "urn:moos:benchmark:" + suffix
	case "protocol":
		return "urn:moos:protocol:" + suffix
	case "compute":
		return "urn:moos:compute:" + suffix
	case "feature":
		return "urn:moos:feature:" + suffix
	case "framework":
		return "urn:moos:framework:" + suffix
	default:
		return ""
	}
}

func slug(s string) string {
	s = strings.ToLower(strings.TrimSpace(s))
	replacer := strings.NewReplacer(" ", "-", "/", "-", "\\", "-", ":", "-", "_", "-", ".", "-")
	s = replacer.Replace(s)
	parts := strings.Split(s, "-")
	filtered := make([]string, 0, len(parts))
	for _, p := range parts {
		p = strings.TrimSpace(p)
		if p != "" {
			filtered = append(filtered, p)
		}
	}
	if len(filtered) == 0 {
		return "unknown"
	}
	return strings.Join(filtered, "-")
}

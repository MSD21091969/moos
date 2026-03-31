package hydration_test

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// validTypeIDs is the canonical set of type_ids from ontology.json objects[].type_id.
var validTypeIDs = map[string]bool{
	"user":               true,
	"collider_admin":     true,
	"superadmin":         true,
	"app_template":       true,
	"node_container":     true,
	"agnostic_model":     true,
	"system_tool":        true,
	"ui_lens":            true,
	"runtime_surface":    true,
	"compute_resource":   true,
	"protocol_adapter":   true,
	"infra_service":      true,
	"memory_store":       true,
	"platform_config":    true,
	"workstation_config": true,
	"kernel_instance":    true,
	"preference":         true,
	"provider":           true,
	"benchmark_suite":    true,
	"benchmark_task":     true,
	"benchmark_score":    true,
	"agent_spec":         true,
	"agent_session":      true,
	"prg_task":           true,
	"calendar_event":     true,
	"keep_note":          true,
	"channel_message":    true,
	"ptp_family":         true,
	"delegation_task":    true,
	"fs_directory":       true,
	"fs_file":            true,
	"os_process":         true,
	"git_repo":           true,
	"git_branch":         true,
	"git_worktree":       true,
	"governance_proposal": true,
	"industry_entity":    true,
	"ontology_term":      true,
}

// allowedStrata maps type_id → set of valid stratum values per ontology.json
// objects[].allowed_strata. Used to cross-validate the optional stratum field.
var allowedStrata = map[string]map[string]bool{
	"user":               {"S2": true, "S3": true},
	"collider_admin":     {"S2": true, "S3": true},
	"superadmin":         {"S2": true, "S3": true},
	"app_template":       {"S1": true, "S2": true},
	"node_container":     {"S2": true, "S3": true},
	"agnostic_model":     {"S2": true, "S3": true},
	"system_tool":        {"S2": true, "S3": true},
	"ui_lens":            {"S4": true},
	"runtime_surface":    {"S2": true, "S3": true},
	"compute_resource":   {"S2": true, "S3": true},
	"protocol_adapter":   {"S2": true, "S3": true},
	"infra_service":      {"S2": true, "S3": true},
	"memory_store":       {"S2": true, "S3": true, "S4": true},
	"platform_config":    {"S2": true, "S3": true},
	"workstation_config": {"S2": true, "S3": true},
	"kernel_instance":    {"S2": true, "S3": true},
	"preference":         {"S2": true, "S3": true},
	"provider":           {"S2": true, "S3": true},
	"benchmark_suite":    {"S2": true},
	"benchmark_task":     {"S2": true},
	"benchmark_score":    {"S3": true},
	"agent_spec":         {"S2": true, "S3": true},
	"agent_session":      {"S2": true, "S3": true},
	"prg_task":           {"S1": true, "S2": true},
	"calendar_event":     {"S0": true, "S1": true, "S2": true},
	"keep_note":          {"S0": true, "S1": true},
	"channel_message":    {"S1": true, "S2": true},
	"ptp_family":         {"S1": true},
	"delegation_task":    {"S2": true},
	"fs_directory":       {"S0": true, "S1": true, "S2": true},
	"fs_file":            {"S0": true, "S1": true, "S2": true},
	"os_process":         {"S0": true, "S2": true, "S3": true},
	"git_repo":           {"S1": true, "S2": true, "S3": true},
	"git_branch":         {"S1": true, "S2": true, "S3": true},
	"git_worktree":       {"S0": true, "S1": true, "S2": true, "S3": true},
	"governance_proposal": {"S0": true, "S1": true, "S2": true},
	"industry_entity":    {"S0": true},
	"ontology_term":      {"S1": true},
}

var validStratumValues = map[string]bool{
	"S0": true, "S1": true, "S2": true, "S3": true, "S4": true,
}

// kbInstanceDirCandidates includes both legacy in-repo and current externalized
// KB layouts.
var kbInstanceDirCandidates = []string{
	"../../../../../ffs0-factory-super/.agent/kb/instances", // current: sibling workspace KB
	"../../../../../../ffs0-factory-super/.agent/kb/instances",
	"../../../../.agent/knowledge_base/instances",    // legacy: repo-local .agent
	"../../../../../.agent/knowledge_base/instances", // current: sibling .agent
}

func resolveKBInstanceDir(t *testing.T) string {
	t.Helper()
	for _, p := range kbInstanceDirCandidates {
		if info, err := os.Stat(p); err == nil && info.IsDir() {
			return p
		}
	}
	t.Skipf("KB instances dir not found (external KB not present in CI); tried: %v", kbInstanceDirCandidates)
	return ""
}

// instanceFile mirrors the top-level structure of instances/*.json.
type instanceFile struct {
	Domain  string                   `json:"domain"`
	Entries []map[string]interface{} `json:"entries"`
}

// TestInstanceFileSchema validates all *.json files in the KB instances directory
// against the rules encoded in superset/schemas/instance.schema.json:
//   - Top-level: domain (required string), entries (required non-empty array)
//   - Each entry: id (required, must match ^urn:moos:), type_id (required, must be one of 23 enum values)
//   - stratum (optional): when present must be S0-S4 and within allowed_strata for the type_id
func TestInstanceFileSchema(t *testing.T) {
	kbInstanceDir := resolveKBInstanceDir(t)
	dirEntries, err := os.ReadDir(kbInstanceDir)
	if err != nil {
		t.Fatalf("cannot read instance dir %q: %v", kbInstanceDir, err)
	}

	var files []string
	for _, e := range dirEntries {
		if !e.IsDir() && strings.HasSuffix(e.Name(), ".json") {
			files = append(files, e.Name())
		}
	}
	if len(files) == 0 {
		t.Fatalf("no JSON files found in %s", kbInstanceDir)
	}

	for _, fname := range files {
		fname := fname
		t.Run(fname, func(t *testing.T) {
			path := filepath.Join(kbInstanceDir, fname)
			data, err := os.ReadFile(path)
			if err != nil {
				t.Fatalf("read file: %v", err)
			}

			var inst instanceFile
			if err := json.Unmarshal(data, &inst); err != nil {
				t.Fatalf("invalid JSON: %v", err)
			}

			// --- top-level requirements ---
			if inst.Domain == "" {
				t.Error("missing required top-level field: domain")
			}
			if len(inst.Entries) == 0 {
				t.Error("entries must be a non-empty array")
				return
			}

			// --- per-entry requirements ---
			for i, entry := range inst.Entries {
				prefix := fmt.Sprintf("entries[%d]", i)
				validateEntry(t, prefix, entry)
			}
		})
	}
}

func validateEntry(t *testing.T, prefix string, entry map[string]interface{}) {
	t.Helper()

	// id: required, string, must match ^urn:moos:
	rawID, hasID := entry["id"]
	if !hasID {
		t.Errorf("%s: missing required field 'id'", prefix)
	} else {
		id, ok := rawID.(string)
		if !ok || id == "" {
			t.Errorf("%s: 'id' must be a non-empty string", prefix)
		} else if !strings.HasPrefix(id, "urn:moos:") {
			t.Errorf("%s: id %q does not match pattern ^urn:moos:", prefix, id)
		}
	}

	// type_id: required, must be one of the 23 ontology type_ids
	rawTypeID, hasTypeID := entry["type_id"]
	var typeID string
	if !hasTypeID {
		t.Errorf("%s: missing required field 'type_id'", prefix)
	} else {
		var ok bool
		typeID, ok = rawTypeID.(string)
		if !ok || typeID == "" {
			t.Errorf("%s: 'type_id' must be a non-empty string", prefix)
		} else if !validTypeIDs[typeID] {
			t.Errorf("%s: type_id %q is not a valid ontology type_id (21 valid values in ontology.json objects[].type_id)", prefix, typeID)
		}
	}

	// stratum: optional; when present must be in S0-S4 and within allowed_strata[type_id]
	if rawStratum, exists := entry["stratum"]; exists {
		stratum, ok := rawStratum.(string)
		if !ok {
			t.Errorf("%s: 'stratum' must be a string", prefix)
		} else if !validStratumValues[stratum] {
			t.Errorf("%s: stratum %q is not valid (must be one of S0 S1 S2 S3 S4)", prefix, stratum)
		} else if typeID != "" && validTypeIDs[typeID] {
			if allowed, known := allowedStrata[typeID]; known {
				if !allowed[stratum] {
					t.Errorf("%s: stratum %q is not in allowed_strata for type_id %q per ontology.json", prefix, stratum, typeID)
				}
			}
		}
	}
}

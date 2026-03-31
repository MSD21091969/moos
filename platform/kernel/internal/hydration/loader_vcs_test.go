package hydration_test

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"

	"moos/platform/kernel/internal/hydration"
)

func TestLoadKBFile_GitBranchesBuildsCheckoutWires(t *testing.T) {
	kbRoot := t.TempDir()
	writeInstance(t, kbRoot, "branches.json", "git_branches", []map[string]any{
		{
			"id":             "urn:moos:branch:main",
			"type_id":        "git_branch",
			"checked_out_at": []string{"urn:moos:worktree:hplaptop-main"},
		},
	})

	req, err := hydration.LoadKBFile(kbRoot, "instances", "branches.json", "urn:moos:kernel:wave-0")
	if err != nil {
		t.Fatalf("LoadKBFile: %v", err)
	}

	if len(req.Nodes) != 1 {
		t.Fatalf("node count = %d, want 1", len(req.Nodes))
	}
	if req.Nodes[0].TypeID != "git_branch" {
		t.Fatalf("type_id = %s, want git_branch", req.Nodes[0].TypeID)
	}
	assertWire(t, req, "urn:moos:kernel:wave-0", "owns", "urn:moos:branch:main", "child")
	assertWire(t, req, "urn:moos:branch:main", "checked_out_at", "urn:moos:worktree:hplaptop-main", "checkout_of")
}

func TestLoadKBFile_GitRepositoriesBuildsBranchTrackingWires(t *testing.T) {
	kbRoot := t.TempDir()
	writeInstance(t, kbRoot, "repos.json", "git_repositories", []map[string]any{
		{
			"id":            "urn:moos:repo:ffs0-factory-super",
			"type_id":       "git_repo",
			"tracks_branch": []string{"urn:moos:branch:main", "urn:moos:branch:agent-vscode-ai"},
		},
	})

	req, err := hydration.LoadKBFile(kbRoot, "instances", "repos.json", "urn:moos:kernel:wave-0")
	if err != nil {
		t.Fatalf("LoadKBFile: %v", err)
	}

	assertWire(t, req, "urn:moos:kernel:wave-0", "owns", "urn:moos:repo:ffs0-factory-super", "child")
	assertWire(t, req, "urn:moos:repo:ffs0-factory-super", "tracks_branch", "urn:moos:branch:main", "branch_of")
	assertWire(t, req, "urn:moos:repo:ffs0-factory-super", "tracks_branch", "urn:moos:branch:agent-vscode-ai", "branch_of")
}

func TestLoadKBFile_KernelsBuildsSpecializationWires(t *testing.T) {
	kbRoot := t.TempDir()
	writeInstance(t, kbRoot, "kernels.json", "kernels", []map[string]any{
		{
			"id":                 "urn:moos:kernel:hplaptop-specialized",
			"type_id":            "kernel_instance",
			"specializes_kernel": "urn:moos:kernel:wave-0",
		},
	})

	req, err := hydration.LoadKBFile(kbRoot, "instances", "kernels.json", "urn:moos:kernel:wave-0")
	if err != nil {
		t.Fatalf("LoadKBFile: %v", err)
	}

	assertWire(t, req, "urn:moos:kernel:wave-0", "owns", "urn:moos:kernel:hplaptop-specialized", "child")
	assertWire(t, req, "urn:moos:kernel:wave-0", "specializes", "urn:moos:kernel:hplaptop-specialized", "specialization_of")
}

func TestLoadKBFile_GovernanceBuildsPromotionWires(t *testing.T) {
	kbRoot := t.TempDir()
	writeInstance(t, kbRoot, "governance.json", "governance", []map[string]any{
		{
			"id":                 "urn:moos:proposal:kernel-split-001",
			"type_id":            "governance_proposal",
			"proposes_promotion": []string{"urn:moos:obj:OBJ23", "urn:moos:kernel:hplaptop-specialized"},
		},
	})

	req, err := hydration.LoadKBFile(kbRoot, "instances", "governance.json", "urn:moos:kernel:wave-0")
	if err != nil {
		t.Fatalf("LoadKBFile: %v", err)
	}

	assertWire(t, req, "urn:moos:kernel:wave-0", "owns", "urn:moos:proposal:kernel-split-001", "child")
	assertWire(t, req, "urn:moos:proposal:kernel-split-001", "proposes_promotion", "urn:moos:obj:OBJ23", "proposed_change")
	assertWire(t, req, "urn:moos:proposal:kernel-split-001", "proposes_promotion", "urn:moos:kernel:hplaptop-specialized", "proposed_change")
}

func TestInstanceOrder_IncludesKernelAndVCSDomains(t *testing.T) {
	requiredOrder := []string{"kernels.json", "worktrees.json", "branches.json", "repos.json", "governance.json"}
	last := -1
	for _, filename := range requiredOrder {
		idx := indexOf(hydration.InstanceOrder, filename)
		if idx == -1 {
			t.Fatalf("InstanceOrder missing %s", filename)
		}
		if idx <= last {
			t.Fatalf("InstanceOrder has %s out of order", filename)
		}
		last = idx
	}
}

func writeInstance(t *testing.T, kbRoot, filename, domain string, entries []map[string]any) {
	t.Helper()
	instDir := filepath.Join(kbRoot, "instances")
	if err := os.MkdirAll(instDir, 0o755); err != nil {
		t.Fatalf("mkdir instances: %v", err)
	}
	payload := map[string]any{
		"domain":  domain,
		"entries": entries,
	}
	data, err := json.Marshal(payload)
	if err != nil {
		t.Fatalf("marshal instance file: %v", err)
	}
	if err := os.WriteFile(filepath.Join(instDir, filename), data, 0o600); err != nil {
		t.Fatalf("write instance file %s: %v", filename, err)
	}
}

func assertWire(t *testing.T, req hydration.MaterializeRequest, srcURN, srcPort, tgtURN, tgtPort string) {
	t.Helper()
	for _, wire := range req.Wires {
		if wire.SourceURN == srcURN && wire.SourcePort == srcPort && wire.TargetURN == tgtURN && wire.TargetPort == tgtPort {
			return
		}
	}
	t.Fatalf("expected wire %s[%s] -> %s[%s]", srcURN, srcPort, tgtURN, tgtPort)
}

func indexOf(items []string, target string) int {
	for i, item := range items {
		if item == target {
			return i
		}
	}
	return -1
}

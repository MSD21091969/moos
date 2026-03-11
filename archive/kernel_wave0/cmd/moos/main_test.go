package main

import (
	"strings"
	"testing"

	"moos/internal/cat"
)

func TestShouldSkipSeedEnvelope(t *testing.T) {
	tests := []struct {
		name     string
		env      cat.Envelope
		skip     bool
		reasonNE string
	}{
		{
			name: "allow valid add",
			env: cat.Envelope{
				Type: cat.ADD,
				Add:  &cat.AddPayload{URN: "urn:moos:workspace:alice", Kind: "NodeContainer", Stratum: cat.S2},
			},
			skip: false,
		},
		{
			name: "block glossary add",
			env: cat.Envelope{
				Type: cat.ADD,
				Add:  &cat.AddPayload{URN: "urn:moos:cat:C", Kind: "NodeContainer", Stratum: cat.S2},
			},
			skip:     true,
			reasonNE: "glossary",
		},
		{
			name: "block legacy kind add",
			env: cat.Envelope{
				Type: cat.ADD,
				Add:  &cat.AddPayload{URN: "urn:moos:workspace:k", Kind: "Kernel", Stratum: cat.S2},
			},
			skip:     true,
			reasonNE: "legacy kind",
		},
		{
			name: "block legacy feature urn add",
			env: cat.Envelope{
				Type: cat.ADD,
				Add:  &cat.AddPayload{URN: "urn:moos:feature:http-api", Kind: "ProtocolAdapter", Stratum: cat.S2},
			},
			skip:     true,
			reasonNE: "legacy system",
		},
		{
			name: "block legacy kernel wave add",
			env: cat.Envelope{
				Type: cat.ADD,
				Add:  &cat.AddPayload{URN: "urn:moos:kernel:wave-0", Kind: "NodeContainer", Stratum: cat.S2},
			},
			skip:     true,
			reasonNE: "legacy system",
		},
		{
			name: "allow add with nil payload",
			env:  cat.Envelope{Type: cat.ADD},
			skip: false,
		},
		{
			name: "block glossary link source",
			env: cat.Envelope{
				Type: cat.LINK,
				Link: &cat.LinkPayload{SourceURN: "urn:moos:cat:C", SourcePort: "out", TargetURN: "urn:ok:t", TargetPort: "in"},
			},
			skip:     true,
			reasonNE: "glossary wire",
		},
		{
			name: "block glossary link target",
			env: cat.Envelope{
				Type: cat.LINK,
				Link: &cat.LinkPayload{SourceURN: "urn:ok:s", SourcePort: "out", TargetURN: "urn:moos:cat:C", TargetPort: "in"},
			},
			skip:     true,
			reasonNE: "glossary wire",
		},
		{
			name: "block legacy link",
			env: cat.Envelope{
				Type: cat.LINK,
				Link: &cat.LinkPayload{SourceURN: "urn:moos:feature:x", SourcePort: "out", TargetURN: "urn:ok:t", TargetPort: "in"},
			},
			skip:     true,
			reasonNE: "legacy system wire",
		},
		{
			name: "allow valid link",
			env: cat.Envelope{
				Type: cat.LINK,
				Link: &cat.LinkPayload{SourceURN: "urn:ok:s", SourcePort: "out", TargetURN: "urn:ok:t", TargetPort: "in"},
			},
			skip: false,
		},
		{
			name: "allow link with nil payload",
			env:  cat.Envelope{Type: cat.LINK},
			skip: false,
		},
		{
			name: "block glossary mutate",
			env: cat.Envelope{
				Type:   cat.MUTATE,
				Mutate: &cat.MutatePayload{URN: "urn:moos:cat:C"},
			},
			skip:     true,
			reasonNE: "glossary mutate",
		},
		{
			name: "block legacy mutate",
			env: cat.Envelope{
				Type:   cat.MUTATE,
				Mutate: &cat.MutatePayload{URN: "urn:moos:feature:semantic-registry"},
			},
			skip:     true,
			reasonNE: "legacy system mutate",
		},
		{
			name: "allow valid mutate",
			env: cat.Envelope{
				Type:   cat.MUTATE,
				Mutate: &cat.MutatePayload{URN: "urn:ok:n"},
			},
			skip: false,
		},
		{
			name: "allow mutate with nil payload",
			env:  cat.Envelope{Type: cat.MUTATE},
			skip: false,
		},
		{
			name: "block glossary unlink",
			env: cat.Envelope{
				Type:   cat.UNLINK,
				Unlink: &cat.UnlinkPayload{SourceURN: "urn:moos:cat:A", SourcePort: "out", TargetURN: "urn:ok:b", TargetPort: "in"},
			},
			skip:     true,
			reasonNE: "glossary unlink",
		},
		{
			name: "block legacy unlink",
			env: cat.Envelope{
				Type:   cat.UNLINK,
				Unlink: &cat.UnlinkPayload{SourceURN: "urn:ok:a", SourcePort: "out", TargetURN: "urn:moos:feature:b", TargetPort: "in"},
			},
			skip:     true,
			reasonNE: "legacy system unlink",
		},
		{
			name: "allow valid unlink",
			env: cat.Envelope{
				Type:   cat.UNLINK,
				Unlink: &cat.UnlinkPayload{SourceURN: "urn:ok:a", SourcePort: "out", TargetURN: "urn:ok:b", TargetPort: "in"},
			},
			skip: false,
		},
		{
			name: "allow unlink with nil payload",
			env:  cat.Envelope{Type: cat.UNLINK},
			skip: false,
		},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			skip, reason := shouldSkipSeedEnvelope(tc.env)
			if skip != tc.skip {
				t.Fatalf("skip=%v want=%v reason=%q", skip, tc.skip, reason)
			}
			if tc.reasonNE != "" && reason == "" {
				t.Fatalf("expected non-empty reason containing %q", tc.reasonNE)
			}
			if tc.reasonNE != "" && !strings.Contains(reason, tc.reasonNE) {
				t.Fatalf("reason=%q does not contain expected token %q", reason, tc.reasonNE)
			}
		})
	}
}

func TestHelperURNFilters(t *testing.T) {
	if !isGlossaryURN("urn:moos:cat:C") {
		t.Fatal("expected glossary URN to be detected")
	}
	if isGlossaryURN("urn:moos:workspace:alice") {
		t.Fatal("did not expect non-glossary URN to match")
	}

	if !isLegacySystemURN("urn:moos:feature:semantic-registry") {
		t.Fatal("expected legacy feature URN to be detected")
	}
	if !isLegacySystemURN("urn:moos:kernel:wave-0") {
		t.Fatal("expected legacy kernel wave URN to be detected")
	}
	if isLegacySystemURN("urn:moos:kernel:self") {
		t.Fatal("did not expect kernel:self to be treated as legacy system URN")
	}
}

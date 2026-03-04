package model

import "testing"

func TestParseMorphismEnvelopesSingle(t *testing.T) {
	input := "```json\n{\"type\":\"ADD\",\"add\":{\"container\":{\"URN\":\"urn:moos:test:1\",\"Kind\":\"data\"}}}\n```"
	envelopes, err := ParseMorphismEnvelopes(input)
	if err != nil {
		t.Fatalf("expected no error, got %v", err)
	}
	if len(envelopes) != 1 {
		t.Fatalf("expected 1 envelope, got %d", len(envelopes))
	}
	if envelopes[0].Type != "ADD" {
		t.Fatalf("expected ADD type")
	}
}

func TestParseMorphismEnvelopesArray(t *testing.T) {
	input := "```morphism\n[{\"type\":\"LINK\",\"link\":{\"wire\":{\"FromContainerURN\":\"urn:a\",\"FromPort\":\"out\",\"ToContainerURN\":\"urn:b\",\"ToPort\":\"in\"}}}]\n```"
	envelopes, err := ParseMorphismEnvelopes(input)
	if err != nil {
		t.Fatalf("expected no error, got %v", err)
	}
	if len(envelopes) != 1 || envelopes[0].Type != "LINK" {
		t.Fatalf("expected LINK envelope")
	}
}

// ---------------------------------------------------------------------------
// Edge cases
// ---------------------------------------------------------------------------

func TestParse_MultipleFencedBlocks(t *testing.T) {
	input := "First block:\n" +
		"```json\n{\"type\":\"ADD\",\"add\":{\"container\":{\"URN\":\"urn:a\",\"Kind\":\"data\"}}}\n```\n" +
		"Some text between.\n" +
		"```json\n{\"type\":\"MUTATE\",\"mutate\":{\"urn\":\"urn:a\",\"expected_version\":1,\"kernel_json\":{}}}\n```\n"
	envelopes, err := ParseMorphismEnvelopes(input)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(envelopes) != 2 {
		t.Fatalf("expected 2 envelopes, got %d", len(envelopes))
	}
	if envelopes[0].Type != "ADD" || envelopes[1].Type != "MUTATE" {
		t.Errorf("expected [ADD, MUTATE], got [%s, %s]", envelopes[0].Type, envelopes[1].Type)
	}
}

func TestParse_EmptyFencedBlock(t *testing.T) {
	input := "```json\n```"
	envelopes, err := ParseMorphismEnvelopes(input)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(envelopes) != 0 {
		t.Errorf("expected 0 envelopes for empty block, got %d", len(envelopes))
	}
}

func TestParse_NonMorphismJSON(t *testing.T) {
	input := "```json\n{\"name\":\"test\",\"value\":42}\n```"
	envelopes, err := ParseMorphismEnvelopes(input)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(envelopes) != 0 {
		t.Errorf("expected 0 envelopes for non-morphism JSON, got %d", len(envelopes))
	}
}

func TestParse_UnfencedJSON(t *testing.T) {
	input := "{\"type\":\"ADD\",\"add\":{\"container\":{\"URN\":\"urn:a\",\"Kind\":\"data\"}}}"
	envelopes, err := ParseMorphismEnvelopes(input)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(envelopes) != 0 {
		t.Errorf("expected 0 envelopes for unfenced JSON, got %d", len(envelopes))
	}
}

func TestParse_PlainTextNoBlocks(t *testing.T) {
	input := "Just a normal response with no code blocks at all."
	envelopes, err := ParseMorphismEnvelopes(input)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if envelopes != nil {
		t.Errorf("expected nil, got %v", envelopes)
	}
}

func TestParse_MalformedJSONInFence(t *testing.T) {
	input := "```json\n{broken!!!\n```"
	envelopes, err := ParseMorphismEnvelopes(input)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(envelopes) != 0 {
		t.Errorf("expected 0 envelopes for malformed JSON, got %d", len(envelopes))
	}
}

func TestParse_ArrayWithMixedValidity(t *testing.T) {
	input := "```json\n" +
		"[{\"type\":\"ADD\",\"add\":{\"container\":{\"URN\":\"urn:ok\",\"Kind\":\"data\"}}},{\"type\":\"\"}]\n" +
		"```"
	envelopes, err := ParseMorphismEnvelopes(input)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(envelopes) != 1 {
		t.Fatalf("expected 1 valid envelope (empty type filtered), got %d", len(envelopes))
	}
	if envelopes[0].Type != "ADD" {
		t.Errorf("expected ADD, got %s", envelopes[0].Type)
	}
}

func TestParse_BareFence(t *testing.T) {
	input := "```\n{\"type\":\"UNLINK\",\"unlink\":{\"wire\":{\"FromContainerURN\":\"urn:a\",\"FromPort\":\"out\",\"ToContainerURN\":\"urn:b\",\"ToPort\":\"in\"}}}\n```"
	envelopes, err := ParseMorphismEnvelopes(input)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(envelopes) != 1 || envelopes[0].Type != "UNLINK" {
		t.Errorf("expected 1 UNLINK envelope from bare fence, got %v", envelopes)
	}
}

func TestParse_WhitespaceAroundJSON(t *testing.T) {
	input := "```json\n   {\"type\":\"MUTATE\",\"mutate\":{\"urn\":\"urn:x\",\"expected_version\":1,\"kernel_json\":{}}}   \n```"
	envelopes, err := ParseMorphismEnvelopes(input)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(envelopes) != 1 || envelopes[0].Type != "MUTATE" {
		t.Errorf("expected 1 MUTATE envelope, got %v", envelopes)
	}
}

func TestParse_AllFourMorphismTypes(t *testing.T) {
	input := "```json\n" +
		"[{\"type\":\"ADD\",\"add\":{\"container\":{\"URN\":\"urn:1\",\"Kind\":\"data\"}}}," +
		"{\"type\":\"LINK\",\"link\":{\"wire\":{\"FromContainerURN\":\"urn:1\",\"FromPort\":\"out\",\"ToContainerURN\":\"urn:2\",\"ToPort\":\"in\"}}}," +
		"{\"type\":\"MUTATE\",\"mutate\":{\"urn\":\"urn:1\",\"expected_version\":1,\"kernel_json\":{}}}," +
		"{\"type\":\"UNLINK\",\"unlink\":{\"wire\":{\"FromContainerURN\":\"urn:1\",\"FromPort\":\"out\",\"ToContainerURN\":\"urn:2\",\"ToPort\":\"in\"}}}]\n" +
		"```"
	envelopes, err := ParseMorphismEnvelopes(input)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(envelopes) != 4 {
		t.Fatalf("expected 4 envelopes, got %d", len(envelopes))
	}
	types := []string{"ADD", "LINK", "MUTATE", "UNLINK"}
	for i, tt := range types {
		if envelopes[i].Type != tt {
			t.Errorf("envelope[%d]: expected %s, got %s", i, tt, envelopes[i].Type)
		}
	}
}

func TestParse_EmptyString(t *testing.T) {
	envelopes, err := ParseMorphismEnvelopes("")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if envelopes != nil {
		t.Errorf("expected nil for empty string, got %v", envelopes)
	}
}

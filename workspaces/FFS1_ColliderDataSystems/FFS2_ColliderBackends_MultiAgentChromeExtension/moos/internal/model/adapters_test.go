package model

import (
	"bytes"
	"context"
	"encoding/json"
	"io"
	"net/http"
	"os"
	"strings"
	"testing"
)

// roundTripFunc is an http.RoundTripper for mocking HTTP responses.
type roundTripFunc func(req *http.Request) *http.Response

func (f roundTripFunc) RoundTrip(req *http.Request) (*http.Response, error) {
	return f(req), nil
}

func mockClient(fn roundTripFunc) *http.Client {
	return &http.Client{Transport: fn}
}

// makeAnthropicJSON builds a valid Anthropic Messages API response body.
func makeAnthropicJSON(text string) string {
	type cBlock struct {
		Type string `json:"type"`
		Text string `json:"text"`
	}
	type aResp struct {
		Content []cBlock `json:"content"`
	}
	b, _ := json.Marshal(aResp{Content: []cBlock{{Type: "text", Text: text}}})
	return string(b)
}

func withAPIKey(t *testing.T) {
	t.Helper()
	t.Setenv("ANTHROPIC_API_KEY", "test-key-abc")
}

// ---------------------------------------------------------------------------
// 1. Anthropic adapter — successful morphism parse
// ---------------------------------------------------------------------------

func TestAnthropicAdapter_ParsesMorphismsFromResponse(t *testing.T) {
	withAPIKey(t)

	llmOutput := "Here is the change:\n" +
		"```json\n" +
		"[{\"type\":\"ADD\",\"add\":{\"container\":{\"URN\":\"urn:moos:test:node1\",\"Kind\":\"data\"}}}]\n" +
		"```\n"

	client := mockClient(func(req *http.Request) *http.Response {
		return &http.Response{
			StatusCode: http.StatusOK,
			Body:       io.NopCloser(bytes.NewBufferString(makeAnthropicJSON(llmOutput))),
			Header:     make(http.Header),
		}
	})

	adapter := AnthropicAdapter{Client: client}
	res, err := adapter.Complete(context.Background(), CompletionRequest{
		SessionID: "s_test",
		Messages:  []Message{{Role: "user", Content: "add a data node"}},
	})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(res.Morphisms) != 1 {
		t.Fatalf("expected 1 morphism, got %d", len(res.Morphisms))
	}
	if res.Morphisms[0].Type != "ADD" {
		t.Errorf("expected ADD morphism, got %s", res.Morphisms[0].Type)
	}
	if !strings.Contains(res.Text, "Here is the change") {
		t.Errorf("expected full text in result, got %q", res.Text)
	}
}

// ---------------------------------------------------------------------------
// 2. Anthropic adapter — multiple morphisms (ADD + LINK)
// ---------------------------------------------------------------------------

func TestAnthropicAdapter_MultipleMorphisms(t *testing.T) {
	withAPIKey(t)

	llmOutput := "```json\n" +
		"[{\"type\":\"ADD\",\"add\":{\"container\":{\"URN\":\"urn:moos:a\",\"Kind\":\"data\"}}}," +
		"{\"type\":\"LINK\",\"link\":{\"wire\":{\"FromContainerURN\":\"urn:moos:a\",\"FromPort\":\"out\",\"ToContainerURN\":\"urn:moos:b\",\"ToPort\":\"in\"}}}]\n" +
		"```\n"

	client := mockClient(func(req *http.Request) *http.Response {
		return &http.Response{
			StatusCode: http.StatusOK,
			Body:       io.NopCloser(bytes.NewBufferString(makeAnthropicJSON(llmOutput))),
			Header:     make(http.Header),
		}
	})

	adapter := AnthropicAdapter{Client: client}
	res, err := adapter.Complete(context.Background(), CompletionRequest{
		SessionID: "s_multi",
		Messages:  []Message{{Role: "user", Content: "add and link"}},
	})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(res.Morphisms) != 2 {
		t.Fatalf("expected 2 morphisms, got %d", len(res.Morphisms))
	}
	if res.Morphisms[0].Type != "ADD" || res.Morphisms[1].Type != "LINK" {
		t.Errorf("expected [ADD, LINK], got [%s, %s]", res.Morphisms[0].Type, res.Morphisms[1].Type)
	}
}

// ---------------------------------------------------------------------------
// 3. Anthropic adapter — plain text (no morphisms)
// ---------------------------------------------------------------------------

func TestAnthropicAdapter_PlainTextNoMorphisms(t *testing.T) {
	withAPIKey(t)

	llmOutput := "I cannot make changes to the graph right now."

	client := mockClient(func(req *http.Request) *http.Response {
		return &http.Response{
			StatusCode: http.StatusOK,
			Body:       io.NopCloser(bytes.NewBufferString(makeAnthropicJSON(llmOutput))),
			Header:     make(http.Header),
		}
	})

	adapter := AnthropicAdapter{Client: client}
	res, err := adapter.Complete(context.Background(), CompletionRequest{
		SessionID: "s_plain",
		Messages:  []Message{{Role: "user", Content: "what is 2+2?"}},
	})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(res.Morphisms) != 0 {
		t.Errorf("expected 0 morphisms, got %d", len(res.Morphisms))
	}
	if res.Text != llmOutput {
		t.Errorf("expected text %q, got %q", llmOutput, res.Text)
	}
}

// ---------------------------------------------------------------------------
// 4. Anthropic adapter — missing API key
// ---------------------------------------------------------------------------

func TestAnthropicAdapter_MissingAPIKey(t *testing.T) {
	t.Setenv("ANTHROPIC_API_KEY", "")

	adapter := AnthropicAdapter{}
	_, err := adapter.Complete(context.Background(), CompletionRequest{
		SessionID: "s_nokey",
		Messages:  []Message{{Role: "user", Content: "hello"}},
	})
	if err == nil {
		t.Fatal("expected error for missing API key")
	}
	if !strings.Contains(err.Error(), "ANTHROPIC_API_KEY") {
		t.Errorf("expected error to mention ANTHROPIC_API_KEY, got %v", err)
	}
}

// ---------------------------------------------------------------------------
// 5. Anthropic adapter — API returns HTTP error
// ---------------------------------------------------------------------------

func TestAnthropicAdapter_HTTPError(t *testing.T) {
	withAPIKey(t)

	client := mockClient(func(req *http.Request) *http.Response {
		return &http.Response{
			StatusCode: http.StatusTooManyRequests,
			Body:       io.NopCloser(bytes.NewBufferString("{\"error\":{\"message\":\"rate limited\"}}")),
			Header:     make(http.Header),
		}
	})

	adapter := AnthropicAdapter{Client: client}
	_, err := adapter.Complete(context.Background(), CompletionRequest{
		SessionID: "s_ratelimit",
		Messages:  []Message{{Role: "user", Content: "hi"}},
	})
	if err == nil {
		t.Fatal("expected error for HTTP 429")
	}
	if !strings.Contains(err.Error(), "429") {
		t.Errorf("expected error to mention 429, got %v", err)
	}
}

// ---------------------------------------------------------------------------
// 6. Anthropic adapter — malformed JSON in response body
// ---------------------------------------------------------------------------

func TestAnthropicAdapter_MalformedResponseBody(t *testing.T) {
	withAPIKey(t)

	client := mockClient(func(req *http.Request) *http.Response {
		return &http.Response{
			StatusCode: http.StatusOK,
			Body:       io.NopCloser(bytes.NewBufferString("{not valid json")),
			Header:     make(http.Header),
		}
	})

	adapter := AnthropicAdapter{Client: client}
	_, err := adapter.Complete(context.Background(), CompletionRequest{
		SessionID: "s_bad_json",
		Messages:  []Message{{Role: "user", Content: "hi"}},
	})
	if err == nil {
		t.Fatal("expected error for malformed JSON")
	}
}

// ---------------------------------------------------------------------------
// 7. Anthropic adapter — verifies request headers
// ---------------------------------------------------------------------------

func TestAnthropicAdapter_RequestHeaders(t *testing.T) {
	withAPIKey(t)

	var capturedReq *http.Request
	client := mockClient(func(req *http.Request) *http.Response {
		capturedReq = req
		return &http.Response{
			StatusCode: http.StatusOK,
			Body:       io.NopCloser(bytes.NewBufferString(makeAnthropicJSON("ok"))),
			Header:     make(http.Header),
		}
	})

	adapter := AnthropicAdapter{Client: client}
	_, _ = adapter.Complete(context.Background(), CompletionRequest{
		SessionID: "s_headers",
		Messages:  []Message{{Role: "user", Content: "hi"}},
	})

	if capturedReq == nil {
		t.Fatal("no request was captured")
	}
	if capturedReq.Header.Get("x-api-key") != "test-key-abc" {
		t.Errorf("expected x-api-key header, got %q", capturedReq.Header.Get("x-api-key"))
	}
	if capturedReq.Header.Get("anthropic-version") != "2023-06-01" {
		t.Errorf("expected anthropic-version header, got %q", capturedReq.Header.Get("anthropic-version"))
	}
	if capturedReq.Header.Get("content-type") != "application/json" {
		t.Errorf("expected content-type, got %q", capturedReq.Header.Get("content-type"))
	}
}

// ---------------------------------------------------------------------------
// 8. Anthropic adapter — request body format
// ---------------------------------------------------------------------------

func TestAnthropicAdapter_RequestBody(t *testing.T) {
	withAPIKey(t)

	var capturedBody []byte
	client := mockClient(func(req *http.Request) *http.Response {
		capturedBody, _ = io.ReadAll(req.Body)
		return &http.Response{
			StatusCode: http.StatusOK,
			Body:       io.NopCloser(bytes.NewBufferString(makeAnthropicJSON("ok"))),
			Header:     make(http.Header),
		}
	})

	adapter := AnthropicAdapter{Client: client}
	_, _ = adapter.Complete(context.Background(), CompletionRequest{
		SessionID: "s_body",
		Messages: []Message{
			{Role: "user", Content: "first message"},
			{Role: "assistant", Content: "response"},
			{Role: "user", Content: "second message"},
		},
	})

	var payload map[string]any
	if err := json.Unmarshal(capturedBody, &payload); err != nil {
		t.Fatalf("failed to parse request body: %v", err)
	}
	if _, ok := payload["model"]; !ok {
		t.Error("request body missing 'model' field")
	}
	if _, ok := payload["system"]; !ok {
		t.Error("request body missing 'system' prompt")
	}
	msgs, ok := payload["messages"].([]any)
	if !ok || len(msgs) != 3 {
		t.Errorf("expected 3 messages in body, got %v", payload["messages"])
	}
}

// ---------------------------------------------------------------------------
// 9. Anthropic adapter — tool call parsing
// ---------------------------------------------------------------------------

func TestAnthropicAdapter_ToolCallParse(t *testing.T) {
	withAPIKey(t)

	llmOutput := "tool: search_papers {\"query\": \"DAG reasoning\"}"

	client := mockClient(func(req *http.Request) *http.Response {
		return &http.Response{
			StatusCode: http.StatusOK,
			Body:       io.NopCloser(bytes.NewBufferString(makeAnthropicJSON(llmOutput))),
			Header:     make(http.Header),
		}
	})

	adapter := AnthropicAdapter{Client: client}
	res, err := adapter.Complete(context.Background(), CompletionRequest{
		SessionID: "s_tool",
		Messages:  []Message{{Role: "user", Content: "search papers"}},
	})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(res.ToolCalls) != 1 {
		t.Fatalf("expected 1 tool call, got %d", len(res.ToolCalls))
	}
	if res.ToolCalls[0].Name != "search_papers" {
		t.Errorf("expected tool name search_papers, got %s", res.ToolCalls[0].Name)
	}
}

// ---------------------------------------------------------------------------
// 10. Anthropic adapter — context cancellation
// ---------------------------------------------------------------------------

func TestAnthropicAdapter_ContextCancellation(t *testing.T) {
	withAPIKey(t)

	ctx, cancel := context.WithCancel(context.Background())
	cancel()

	adapter := AnthropicAdapter{}
	_, err := adapter.Complete(ctx, CompletionRequest{
		SessionID: "s_cancel",
		Messages:  []Message{{Role: "user", Content: "hi"}},
	})
	if err == nil {
		t.Fatal("expected error for cancelled context")
	}
}

// ---------------------------------------------------------------------------
// 11. Gemini adapter — echoes user content
// ---------------------------------------------------------------------------

func TestGeminiAdapter_EchoesUserContent(t *testing.T) {
	adapter := GeminiAdapter{}
	res, err := adapter.Complete(context.Background(), CompletionRequest{
		SessionID: "s_gemini",
		Messages:  []Message{{Role: "user", Content: "hello world"}},
	})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if !strings.Contains(res.Text, "hello world") {
		t.Errorf("expected text to contain user input, got %q", res.Text)
	}
}

// ---------------------------------------------------------------------------
// 12. Gemini adapter — parses inline morphisms
// ---------------------------------------------------------------------------

func TestGeminiAdapter_ParsesMorphismsFromInput(t *testing.T) {
	input := "```json\n" +
		"{\"type\":\"MUTATE\",\"mutate\":{\"urn\":\"urn:moos:test:1\",\"expected_version\":1,\"kernel_json\":{}}}" +
		"\n```"

	adapter := GeminiAdapter{}
	res, err := adapter.Complete(context.Background(), CompletionRequest{
		SessionID: "s_gemini_morph",
		Messages:  []Message{{Role: "user", Content: input}},
	})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(res.Morphisms) != 1 {
		t.Fatalf("expected 1 morphism, got %d", len(res.Morphisms))
	}
	if res.Morphisms[0].Type != "MUTATE" {
		t.Errorf("expected MUTATE, got %s", res.Morphisms[0].Type)
	}
}

// ---------------------------------------------------------------------------
// 13. Gemini adapter — empty messages
// ---------------------------------------------------------------------------

func TestGeminiAdapter_EmptyMessages(t *testing.T) {
	adapter := GeminiAdapter{}
	res, err := adapter.Complete(context.Background(), CompletionRequest{
		SessionID: "s_empty",
		Messages:  []Message{},
	})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(res.Morphisms) != 0 {
		t.Errorf("expected 0 morphisms, got %d", len(res.Morphisms))
	}
}

// ---------------------------------------------------------------------------
// 14. latestUserContent helper
// ---------------------------------------------------------------------------

func TestLatestUserContent(t *testing.T) {
	msgs := []Message{
		{Role: "user", Content: "first"},
		{Role: "assistant", Content: "response"},
		{Role: "user", Content: "second"},
	}
	got := latestUserContent(msgs)
	if got != "second" {
		t.Errorf("expected 'second', got %q", got)
	}
}

func TestLatestUserContent_NoUsers(t *testing.T) {
	msgs := []Message{{Role: "assistant", Content: "hello"}}
	got := latestUserContent(msgs)
	if got != "" {
		t.Errorf("expected empty string, got %q", got)
	}
}

// ---------------------------------------------------------------------------
// 15. parseToolCalls edge cases
// ---------------------------------------------------------------------------

func TestParseToolCalls_NoPrefix(t *testing.T) {
	if parseToolCalls("just plain text") != nil {
		t.Error("expected nil for non-tool text")
	}
}

func TestParseToolCalls_EmptyBody(t *testing.T) {
	if parseToolCalls("tool:") != nil {
		t.Error("expected nil for empty tool body")
	}
}

func TestParseToolCalls_NameOnly(t *testing.T) {
	result := parseToolCalls("tool: my_tool")
	if len(result) != 1 || result[0].Name != "my_tool" {
		t.Errorf("expected tool call my_tool, got %v", result)
	}
}

func TestParseToolCalls_WithJSONArgs(t *testing.T) {
	result := parseToolCalls("tool: search {\"q\": \"hello\", \"limit\": 10}")
	if len(result) != 1 || result[0].Name != "search" {
		t.Fatalf("unexpected: %v", result)
	}
	if result[0].Arguments["q"] != "hello" {
		t.Errorf("expected q=hello, got %v", result[0].Arguments["q"])
	}
}

func TestParseToolCalls_MalformedArgs(t *testing.T) {
	result := parseToolCalls("tool: my_tool not-json")
	if len(result) != 1 || result[0].Name != "my_tool" {
		t.Fatalf("unexpected: %v", result)
	}
	if len(result[0].Arguments) != 0 {
		t.Errorf("expected empty arguments for malformed JSON, got %v", result[0].Arguments)
	}
}

// ---------------------------------------------------------------------------
// 16. Anthropic adapter — malformed morphism JSON in fence
// ---------------------------------------------------------------------------

func TestAnthropicAdapter_MalformedMorphismJSON(t *testing.T) {
	withAPIKey(t)

	llmOutput := "```json\n{broken json!!!\n```"

	client := mockClient(func(req *http.Request) *http.Response {
		return &http.Response{
			StatusCode: http.StatusOK,
			Body:       io.NopCloser(bytes.NewBufferString(makeAnthropicJSON(llmOutput))),
			Header:     make(http.Header),
		}
	})

	adapter := AnthropicAdapter{Client: client}
	res, err := adapter.Complete(context.Background(), CompletionRequest{
		SessionID: "s_badmorph",
		Messages:  []Message{{Role: "user", Content: "hi"}},
	})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(res.Morphisms) != 0 {
		t.Errorf("expected 0 morphisms for malformed JSON, got %d", len(res.Morphisms))
	}
	if res.Text == "" {
		t.Error("expected non-empty text even with malformed morphisms")
	}
}

// ---------------------------------------------------------------------------
// 17. Anthropic adapter — empty content blocks
// ---------------------------------------------------------------------------

func TestAnthropicAdapter_EmptyContentBlocks(t *testing.T) {
	withAPIKey(t)

	client := mockClient(func(req *http.Request) *http.Response {
		return &http.Response{
			StatusCode: http.StatusOK,
			Body:       io.NopCloser(bytes.NewBufferString("{\"content\":[]}")),
			Header:     make(http.Header),
		}
	})

	adapter := AnthropicAdapter{Client: client}
	res, err := adapter.Complete(context.Background(), CompletionRequest{
		SessionID: "s_empty_content",
		Messages:  []Message{{Role: "user", Content: "hi"}},
	})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if res.Text != "" {
		t.Errorf("expected empty text, got %q", res.Text)
	}
	if len(res.Morphisms) != 0 {
		t.Errorf("expected 0 morphisms, got %d", len(res.Morphisms))
	}
}

// ---------------------------------------------------------------------------
// 18. Gemini adapter — role case insensitivity
// ---------------------------------------------------------------------------

func TestGeminiAdapter_RoleCaseInsensitivity(t *testing.T) {
	adapter := GeminiAdapter{}
	res, err := adapter.Complete(context.Background(), CompletionRequest{
		SessionID: "s_case",
		Messages:  []Message{{Role: "USER", Content: "uppercase role"}},
	})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if !strings.Contains(res.Text, "uppercase role") {
		t.Errorf("expected user content, got %q", res.Text)
	}
}

// ---------------------------------------------------------------------------
// 19. Anthropic adapter — nil Client defaults
// ---------------------------------------------------------------------------

func TestAnthropicAdapter_NilClientDefault(t *testing.T) {
	t.Setenv("ANTHROPIC_API_KEY", "")

	adapter := AnthropicAdapter{Client: nil}
	_, err := adapter.Complete(context.Background(), CompletionRequest{
		SessionID: "s_nil_client",
		Messages:  []Message{{Role: "user", Content: "hi"}},
	})
	if err == nil {
		t.Fatal("expected error for missing API key")
	}
}

// ---------------------------------------------------------------------------
// 20. Gemini adapter — UNLINK morphism
// ---------------------------------------------------------------------------

func TestGeminiAdapter_UnlinkMorphism(t *testing.T) {
	input := "```json\n" +
		"{\"type\":\"UNLINK\",\"unlink\":{\"wire\":{\"FromContainerURN\":\"urn:a\",\"FromPort\":\"out\",\"ToContainerURN\":\"urn:b\",\"ToPort\":\"in\"}}}" +
		"\n```"

	adapter := GeminiAdapter{}
	res, err := adapter.Complete(context.Background(), CompletionRequest{
		SessionID: "s_unlink",
		Messages:  []Message{{Role: "user", Content: input}},
	})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(res.Morphisms) != 1 || res.Morphisms[0].Type != "UNLINK" {
		t.Errorf("expected 1 UNLINK morphism, got %v", res.Morphisms)
	}
}

// ---------------------------------------------------------------------------
// 21. API key safety — key not in response text
// ---------------------------------------------------------------------------

func TestAnthropicAdapter_KeyNotInResponseText(t *testing.T) {
	withAPIKey(t)

	client := mockClient(func(req *http.Request) *http.Response {
		return &http.Response{
			StatusCode: http.StatusOK,
			Body:       io.NopCloser(bytes.NewBufferString(makeAnthropicJSON("safe text"))),
			Header:     make(http.Header),
		}
	})

	adapter := AnthropicAdapter{Client: client}
	res, _ := adapter.Complete(context.Background(), CompletionRequest{
		SessionID: "s_safe",
		Messages:  []Message{{Role: "user", Content: "hi"}},
	})

	apiKey := os.Getenv("ANTHROPIC_API_KEY")
	if strings.Contains(res.Text, apiKey) {
		t.Error("API key must not appear in response text")
	}
}

// ---------------------------------------------------------------------------
// Phase 4: Streaming adapter tests
// ---------------------------------------------------------------------------

// makeAnthropicSSE builds a fake Anthropic text/event-stream body.
func makeAnthropicSSE(tokens ...string) string {
	var sb strings.Builder
	for _, tok := range tokens {
		delta := map[string]any{
			"type":  "content_block_delta",
			"index": 0,
			"delta": map[string]string{"type": "text_delta", "text": tok},
		}
		b, _ := json.Marshal(delta)
		sb.WriteString("event: content_block_delta\ndata: ")
		sb.WriteString(string(b))
		sb.WriteString("\n\n")
	}
	sb.WriteString("event: message_stop\ndata: {\"type\":\"message_stop\"}\n\n")
	return sb.String()
}

func TestAnthropicAdapter_Stream_YieldsChunks(t *testing.T) {
	withAPIKey(t)

	want := []string{"Hello", ", ", "world!"}
	client := mockClient(func(req *http.Request) *http.Response {
		h := make(http.Header)
		h.Set("Content-Type", "text/event-stream")
		return &http.Response{
			StatusCode: http.StatusOK,
			Body:       io.NopCloser(strings.NewReader(makeAnthropicSSE(want...))),
			Header:     h,
		}
	})

	adapter := AnthropicAdapter{Client: client}
	ch, err := adapter.Stream(context.Background(), CompletionRequest{
		SessionID: "s_stream",
		Messages:  []Message{{Role: "user", Content: "hi"}},
	})
	if err != nil {
		t.Fatalf("Stream() error: %v", err)
	}

	var gotText strings.Builder
	gotDone := false
	for chunk := range ch {
		if chunk.Error != nil {
			t.Fatalf("unexpected error chunk: %v", chunk.Error)
		}
		if chunk.Text != "" {
			gotText.WriteString(chunk.Text)
		}
		if chunk.Done {
			gotDone = true
		}
	}

	if gotText.String() != strings.Join(want, "") {
		t.Fatalf("expected %q, got %q", strings.Join(want, ""), gotText.String())
	}
	if !gotDone {
		t.Fatal("expected Done=true chunk")
	}
}

func TestAnthropicAdapter_Stream_MorphismsEmittedAfterText(t *testing.T) {
	withAPIKey(t)

	morphismToken := "\n```json\n[{\"Type\":\"ADD\",\"URN\":\"urn:moos:test:stream1\",\"Kind\":\"DATA\",\"Kernel\":{}}]\n```\n"
	client := mockClient(func(req *http.Request) *http.Response {
		h := make(http.Header)
		h.Set("Content-Type", "text/event-stream")
		return &http.Response{
			StatusCode: http.StatusOK,
			Body:       io.NopCloser(strings.NewReader(makeAnthropicSSE("Adding node:", morphismToken))),
			Header:     h,
		}
	})

	adapter := AnthropicAdapter{Client: client}
	ch, err := adapter.Stream(context.Background(), CompletionRequest{
		SessionID: "s_morph_stream",
		Messages:  []Message{{Role: "user", Content: "add node"}},
	})
	if err != nil {
		t.Fatalf("Stream() error: %v", err)
	}

	var gotMorphisms int
	for chunk := range ch {
		if len(chunk.Morphisms) > 0 {
			gotMorphisms += len(chunk.Morphisms)
		}
	}
	if gotMorphisms == 0 {
		t.Fatal("expected morphisms in stream chunks")
	}
}

func TestAnthropicAdapter_Stream_NoKey_ReturnsError(t *testing.T) {
	t.Setenv("ANTHROPIC_API_KEY", "")
	adapter := AnthropicAdapter{}
	_, err := adapter.Stream(context.Background(), CompletionRequest{
		Messages: []Message{{Role: "user", Content: "hi"}},
	})
	if err == nil {
		t.Fatal("expected error when ANTHROPIC_API_KEY is empty")
	}
}

func TestAnthropicAdapter_Stream_APIError_ReturnsError(t *testing.T) {
	withAPIKey(t)
	client := mockClient(func(req *http.Request) *http.Response {
		return &http.Response{
			StatusCode: http.StatusUnauthorized,
			Body:       io.NopCloser(strings.NewReader(`{"error":"invalid api key"}`)),
			Header:     make(http.Header),
		}
	})
	adapter := AnthropicAdapter{Client: client}
	_, err := adapter.Stream(context.Background(), CompletionRequest{
		Messages: []Message{{Role: "user", Content: "hi"}},
	})
	if err == nil {
		t.Fatal("expected error on HTTP 401")
	}
	if !strings.Contains(err.Error(), "401") {
		t.Fatalf("expected 401 in error, got: %v", err)
	}
}

func TestGeminiAdapter_Stream_NoKey_FallsBackToCompletionStub(t *testing.T) {
	t.Setenv("GEMINI_API_KEY", "")
	adapter := GeminiAdapter{}
	ch, err := adapter.Stream(context.Background(), CompletionRequest{
		Messages: []Message{{Role: "user", Content: "hello gemini"}},
	})
	if err != nil {
		t.Fatalf("expected stub fallback, got error: %v", err)
	}
	var gotText bool
	for chunk := range ch {
		if chunk.Text != "" {
			gotText = true
		}
	}
	if !gotText {
		t.Fatal("expected at least one text chunk from Gemini stub fallback")
	}
}

func TestParsedToolCalls_Exported(t *testing.T) {
	calls := ParseToolCalls(`tool:search {"query":"DAG reasoning"}`)
	if len(calls) != 1 {
		t.Fatalf("expected 1 tool call, got %d", len(calls))
	}
	if calls[0].Name != "search" {
		t.Fatalf("expected name 'search', got %q", calls[0].Name)
	}
	if calls[0].Arguments["query"] != "DAG reasoning" {
		t.Fatalf("expected query arg, got %v", calls[0].Arguments)
	}
}

func TestParsedToolCalls_EmptyText_ReturnsNil(t *testing.T) {
	calls := ParseToolCalls("just regular text, no tool calls here")
	if len(calls) != 0 {
		t.Fatalf("expected no tool calls, got %d", len(calls))
	}
}

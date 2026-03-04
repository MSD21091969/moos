package model

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
)

type AnthropicAdapter struct {
	Client *http.Client
}

type GeminiAdapter struct{}

func (adapter AnthropicAdapter) Name() string { return "anthropic" }

func (adapter GeminiAdapter) Name() string { return "gemini" }

func (adapter AnthropicAdapter) Complete(ctx context.Context, request CompletionRequest) (CompletionResult, error) {
	apiKey := os.Getenv("ANTHROPIC_API_KEY")
	if apiKey == "" {
		return CompletionResult{}, fmt.Errorf("ANTHROPIC_API_KEY environment variable is not set")
	}

	payload := map[string]any{
		"model":      "claude-3-7-sonnet-20250219",
		"max_tokens": 8192,
		"system":     "You are a math engine and graph editor. Whenever possible, format changes as JSON array of morphisms `{ \"Type\": \"ADD|LINK|MUTATE|UNLINK|REMOVE\", ... }` inside a ```json block if you are making changes.",
		"messages":   request.Messages,
	}

	body, err := json.Marshal(payload)
	if err != nil {
		return CompletionResult{}, err
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, "https://api.anthropic.com/v1/messages", bytes.NewReader(body))
	if err != nil {
		return CompletionResult{}, err
	}

	req.Header.Set("x-api-key", apiKey)
	req.Header.Set("anthropic-version", "2023-06-01")
	req.Header.Set("content-type", "application/json")

	client := adapter.Client
	if client == nil {
		client = http.DefaultClient
	}
	resp, err := client.Do(req)
	if err != nil {
		return CompletionResult{}, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		b, _ := io.ReadAll(resp.Body)
		return CompletionResult{}, fmt.Errorf("anthropic api error: %d - %s", resp.StatusCode, string(b))
	}

	var response struct {
		Content []struct {
			Type string `json:"type"`
			Text string `json:"text"`
		} `json:"content"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&response); err != nil {
		return CompletionResult{}, err
	}

	var text strings.Builder
	for _, c := range response.Content {
		if c.Type == "text" {
			text.WriteString(c.Text)
		}
	}

	fullText := text.String()
	envelopes, err := ParseMorphismEnvelopes(fullText)
	if err != nil {
		// Even if parsing fails, we still want to return the text to the user.
		envelopes = nil
	}

	return CompletionResult{
		Text:      fullText,
		Morphisms: envelopes,
		ToolCalls: parseToolCalls(fullText),
	}, nil
}

func (adapter GeminiAdapter) Complete(ctx context.Context, request CompletionRequest) (CompletionResult, error) {
	_ = ctx
	latest := latestUserContent(request.Messages)
	envelopes, err := ParseMorphismEnvelopes(latest)
	if err != nil {
		return CompletionResult{}, err
	}
	return CompletionResult{
		Text:      fmt.Sprintf("gemini acknowledged: %s", strings.TrimSpace(latest)),
		Morphisms: envelopes,
		ToolCalls: parseToolCalls(latest),
	}, nil
}

// Stream implements real Anthropic SSE streaming. The request is sent with
// "stream": true and the response is parsed as a text/event-stream. Each
// content_block_delta event yields a Chunk. Morphisms are extracted from the
// fully accumulated text and emitted as a final Chunk before Done=true.
func (adapter AnthropicAdapter) Stream(ctx context.Context, request CompletionRequest) (<-chan Chunk, error) {
	apiKey := os.Getenv("ANTHROPIC_API_KEY")
	if apiKey == "" {
		return nil, fmt.Errorf("ANTHROPIC_API_KEY environment variable is not set")
	}

	payload := map[string]any{
		"model":      "claude-3-7-sonnet-20250219",
		"max_tokens": 8192,
		"stream":     true,
		"system":     "You are a math engine and graph editor. Whenever possible, format changes as JSON array of morphisms `{ \"Type\": \"ADD|LINK|MUTATE|UNLINK|REMOVE\", ... }` inside a ```json block if you are making changes.",
		"messages":   request.Messages,
	}
	body, err := json.Marshal(payload)
	if err != nil {
		return nil, err
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, "https://api.anthropic.com/v1/messages", bytes.NewReader(body))
	if err != nil {
		return nil, err
	}
	req.Header.Set("x-api-key", apiKey)
	req.Header.Set("anthropic-version", "2023-06-01")
	req.Header.Set("content-type", "application/json")
	req.Header.Set("accept", "text/event-stream")

	client := adapter.Client
	if client == nil {
		client = http.DefaultClient
	}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	if resp.StatusCode != http.StatusOK {
		b, _ := io.ReadAll(resp.Body)
		resp.Body.Close()
		return nil, fmt.Errorf("anthropic api error: %d - %s", resp.StatusCode, string(b))
	}

	ch := make(chan Chunk, 32)
	go func() {
		defer resp.Body.Close()
		defer close(ch)

		var fullText strings.Builder
		scanner := bufio.NewScanner(resp.Body)
		for scanner.Scan() {
			line := scanner.Text()
			if !strings.HasPrefix(line, "data: ") {
				continue
			}
			data := strings.TrimPrefix(line, "data: ")
			if data == "[DONE]" {
				break
			}
			var event struct {
				Type  string `json:"type"`
				Delta struct {
					Type string `json:"type"`
					Text string `json:"text"`
				} `json:"delta"`
			}
			if err := json.Unmarshal([]byte(data), &event); err != nil {
				continue
			}
			if event.Type == "content_block_delta" && event.Delta.Type == "text_delta" && event.Delta.Text != "" {
				fullText.WriteString(event.Delta.Text)
				select {
				case ch <- Chunk{Text: event.Delta.Text}:
				case <-ctx.Done():
					return
				}
			}
		}

		// Parse morphisms from fully accumulated text.
		envelopes, _ := ParseMorphismEnvelopes(fullText.String())
		if len(envelopes) > 0 {
			select {
			case ch <- Chunk{Morphisms: envelopes}:
			case <-ctx.Done():
			}
		}
		select {
		case ch <- Chunk{Done: true}:
		case <-ctx.Done():
		}
	}()

	return ch, nil
}

// Stream implements Gemini streaming. When GEMINI_API_KEY is set it calls the
// real Gemini generateContent streaming endpoint (?alt=sse). When no key is
// Stream wraps the stub Complete() as a channel. The stub extracts morphisms
// and tool calls from the user's latest message and echoes them back, which
// makes GeminiAdapter deterministic and suitable for unit testing.
// For production use with real SSE streaming use GeminiStreamingAdapter.
func (adapter GeminiAdapter) Stream(ctx context.Context, request CompletionRequest) (<-chan Chunk, error) {
	return completionToStream(ctx, adapter, request)
}

// GeminiStreamingAdapter wraps GeminiAdapter with real Gemini SSE streaming.
// It delegates Complete() to the stub so that morphism/tool-call extraction
// from user input still works, while Stream() calls the live Gemini API when
// GEMINI_API_KEY is set.
type GeminiStreamingAdapter struct {
	GeminiAdapter
}

func (adapter GeminiStreamingAdapter) Name() string { return "gemini" }

// Stream calls the real Gemini generateContent streaming endpoint when
// GEMINI_API_KEY is set, otherwise falls back to the stub Complete().
func (adapter GeminiStreamingAdapter) Stream(ctx context.Context, request CompletionRequest) (<-chan Chunk, error) {
	apiKey := os.Getenv("GEMINI_API_KEY")
	if apiKey == "" {
		return completionToStream(ctx, adapter.GeminiAdapter, request)
	}

	// Build Gemini contents array from message history.
	type part struct {
		Text string `json:"text"`
	}
	type content struct {
		Role  string `json:"role"`
		Parts []part `json:"parts"`
	}
	var contents []content
	for _, msg := range request.Messages {
		role := msg.Role
		if role == "assistant" {
			role = "model"
		}
		contents = append(contents, content{Role: role, Parts: []part{{Text: msg.Content}}})
	}
	payload := map[string]any{"contents": contents}
	body, err := json.Marshal(payload)
	if err != nil {
		return nil, err
	}

	url := fmt.Sprintf(
		"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:streamGenerateContent?alt=sse&key=%s",
		apiKey,
	)
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewReader(body))
	if err != nil {
		return nil, err
	}
	req.Header.Set("content-type", "application/json")

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, err
	}
	if resp.StatusCode != http.StatusOK {
		b, _ := io.ReadAll(resp.Body)
		resp.Body.Close()
		return nil, fmt.Errorf("gemini api error: %d - %s", resp.StatusCode, string(b))
	}

	ch := make(chan Chunk, 32)
	go func() {
		defer resp.Body.Close()
		defer close(ch)

		var fullText strings.Builder
		scanner := bufio.NewScanner(resp.Body)
		for scanner.Scan() {
			line := scanner.Text()
			if !strings.HasPrefix(line, "data: ") {
				continue
			}
			data := strings.TrimPrefix(line, "data: ")
			var event struct {
				Candidates []struct {
					Content struct {
						Parts []struct {
							Text string `json:"text"`
						} `json:"parts"`
					} `json:"content"`
				} `json:"candidates"`
			}
			if err := json.Unmarshal([]byte(data), &event); err != nil {
				continue
			}
			for _, candidate := range event.Candidates {
				for _, p := range candidate.Content.Parts {
					if p.Text != "" {
						fullText.WriteString(p.Text)
						select {
						case ch <- Chunk{Text: p.Text}:
						case <-ctx.Done():
							return
						}
					}
				}
			}
		}

		// Extract morphisms from the model's accumulated response text.
		// Also extract morphisms and tool calls from the user's latest message
		// so that user-provided payloads are applied alongside model output.
		envelopes, _ := ParseMorphismEnvelopes(fullText.String())
		latest := latestUserContent(request.Messages)
		userEnvelopes, _ := ParseMorphismEnvelopes(latest)
		userToolCalls := parseToolCalls(latest)
		allEnvelopes := append(envelopes, userEnvelopes...)
		if len(allEnvelopes) > 0 || len(userToolCalls) > 0 {
			select {
			case ch <- Chunk{Morphisms: allEnvelopes, ToolCalls: userToolCalls}:
			case <-ctx.Done():
			}
		}
		select {
		case ch <- Chunk{Done: true}:
		case <-ctx.Done():
		}
	}()

	return ch, nil
}

func latestUserContent(messages []Message) string {
	for i := len(messages) - 1; i >= 0; i-- {
		if strings.EqualFold(messages[i].Role, "user") {
			return messages[i].Content
		}
	}
	return ""
}

func parseToolCalls(text string) []ToolCall {
	trimmed := strings.TrimSpace(text)
	if !strings.HasPrefix(trimmed, "tool:") {
		return nil
	}
	body := strings.TrimPrefix(trimmed, "tool:")
	body = strings.TrimSpace(body)
	if body == "" {
		return nil
	}
	parts := strings.SplitN(body, " ", 2)
	call := ToolCall{Name: strings.TrimSpace(parts[0]), Arguments: map[string]any{}}
	if len(parts) == 2 {
		var args map[string]any
		if err := json.Unmarshal([]byte(parts[1]), &args); err == nil {
			call.Arguments = args
		}
	}
	if call.Name == "" {
		return nil
	}
	return []ToolCall{call}
}

// ParseToolCalls is the exported variant of parseToolCalls for use by
// packages that accumulate streaming text and need to detect tool calls.
func ParseToolCalls(text string) []ToolCall {
	return parseToolCalls(text)
}

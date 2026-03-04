package model

import (
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

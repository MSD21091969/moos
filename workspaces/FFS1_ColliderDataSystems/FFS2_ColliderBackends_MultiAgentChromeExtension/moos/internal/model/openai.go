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

// OpenAIAdapter implements the Adapter interface against any OpenAI-compatible
// chat completions endpoint. It targets api.openai.com by default but can be
// redirected to GCP Vertex AI (or any other OpenAI-compatible proxy) by setting
// OPENAI_BASE_URL. Authentication uses a plain Bearer token, so both an OpenAI
// API key and a GCP access token (`gcloud auth print-access-token`) work.
//
// Required env:
//   - OPENAI_API_KEY — API key or GCP access token used as Bearer auth.
//
// Optional env:
//   - OPENAI_BASE_URL — Base URL without trailing slash. Defaults to
//     "https://api.openai.com/v1". For GCP Vertex AI set to:
//     "https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT}/locations/{LOCATION}/endpoints/openapi"
//   - OPENAI_MODEL — Chat model name. Defaults to "gpt-4o". For GCP Vertex AI
//     use the model garden identifier e.g. "meta/llama-3.1-405b-instruct".
type OpenAIAdapter struct {
	Client *http.Client
}

func (adapter OpenAIAdapter) Name() string { return "openai" }

func (adapter OpenAIAdapter) baseURL() string {
	if u := os.Getenv("OPENAI_BASE_URL"); u != "" {
		return strings.TrimRight(u, "/")
	}
	return "https://api.openai.com/v1"
}

func (adapter OpenAIAdapter) model() string {
	if m := os.Getenv("OPENAI_MODEL"); m != "" {
		return m
	}
	return "gpt-4o"
}

func (adapter OpenAIAdapter) client() *http.Client {
	if adapter.Client != nil {
		return adapter.Client
	}
	return http.DefaultClient
}

func (adapter OpenAIAdapter) apiKey() (string, error) {
	key := os.Getenv("OPENAI_API_KEY")
	if key == "" {
		return "", fmt.Errorf("OPENAI_API_KEY environment variable is not set")
	}
	return key, nil
}

// buildMessages converts internal messages to the OpenAI messages format.
func buildMessages(messages []Message) []map[string]string {
	result := make([]map[string]string, 0, len(messages)+1)
	result = append(result, map[string]string{
		"role":    "system",
		"content": "You are a math engine and graph editor. Whenever possible, format changes as JSON array of morphisms `{ \"Type\": \"ADD|LINK|MUTATE|UNLINK|REMOVE\", ... }` inside a ```json block if you are making changes.",
	})
	for _, msg := range messages {
		result = append(result, map[string]string{
			"role":    msg.Role,
			"content": msg.Content,
		})
	}
	return result
}

func (adapter OpenAIAdapter) Complete(ctx context.Context, request CompletionRequest) (CompletionResult, error) {
	apiKey, err := adapter.apiKey()
	if err != nil {
		return CompletionResult{}, err
	}

	payload := map[string]any{
		"model":    adapter.model(),
		"messages": buildMessages(request.Messages),
	}
	body, err := json.Marshal(payload)
	if err != nil {
		return CompletionResult{}, err
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, adapter.baseURL()+"/chat/completions", bytes.NewReader(body))
	if err != nil {
		return CompletionResult{}, err
	}
	req.Header.Set("Authorization", "Bearer "+apiKey)
	req.Header.Set("Content-Type", "application/json")

	resp, err := adapter.client().Do(req)
	if err != nil {
		return CompletionResult{}, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		b, _ := io.ReadAll(resp.Body)
		return CompletionResult{}, fmt.Errorf("openai api error: %d - %s", resp.StatusCode, string(b))
	}

	var response struct {
		Choices []struct {
			Message struct {
				Content string `json:"content"`
			} `json:"message"`
		} `json:"choices"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&response); err != nil {
		return CompletionResult{}, err
	}

	var text strings.Builder
	for _, choice := range response.Choices {
		text.WriteString(choice.Message.Content)
	}
	accumulated := text.String()
	envelopes, _ := ParseMorphismEnvelopes(accumulated)
	latest := latestUserContent(request.Messages)
	userEnvelopes, _ := ParseMorphismEnvelopes(latest)
	userToolCalls := parseToolCalls(latest)

	return CompletionResult{
		Text:      accumulated,
		Morphisms: append(envelopes, userEnvelopes...),
		ToolCalls: userToolCalls,
	}, nil
}

// Stream calls the OpenAI (or GCP Vertex AI) chat completions endpoint with
// stream=true and yields Chunk values as SSE events arrive. The format is
// identical between OpenAI and GCP Vertex AI's OpenAI-compatible surface.
func (adapter OpenAIAdapter) Stream(ctx context.Context, request CompletionRequest) (<-chan Chunk, error) {
	apiKey, err := adapter.apiKey()
	if err != nil {
		return nil, err
	}

	payload := map[string]any{
		"model":    adapter.model(),
		"messages": buildMessages(request.Messages),
		"stream":   true,
	}
	body, err := json.Marshal(payload)
	if err != nil {
		return nil, err
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, adapter.baseURL()+"/chat/completions", bytes.NewReader(body))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Authorization", "Bearer "+apiKey)
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "text/event-stream")

	resp, err := adapter.client().Do(req)
	if err != nil {
		return nil, err
	}
	if resp.StatusCode != http.StatusOK {
		b, _ := io.ReadAll(resp.Body)
		resp.Body.Close()
		return nil, fmt.Errorf("openai api error: %d - %s", resp.StatusCode, string(b))
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
				Choices []struct {
					Delta struct {
						Content string `json:"content"`
					} `json:"delta"`
					FinishReason *string `json:"finish_reason"`
				} `json:"choices"`
			}
			if err := json.Unmarshal([]byte(data), &event); err != nil {
				continue
			}
			for _, choice := range event.Choices {
				if choice.Delta.Content != "" {
					fullText.WriteString(choice.Delta.Content)
					select {
					case ch <- Chunk{Text: choice.Delta.Content}:
					case <-ctx.Done():
						return
					}
				}
			}
		}

		// Extract morphisms from accumulated model output, then overlay any
		// user-provided morphisms/tool calls from the latest user message.
		envelopes, _ := ParseMorphismEnvelopes(fullText.String())
		latest := latestUserContent(request.Messages)
		userEnvelopes, _ := ParseMorphismEnvelopes(latest)
		userToolCalls := parseToolCalls(latest)
		allEnvelopes := append(envelopes, userEnvelopes...)
		if len(allEnvelopes) > 0 || len(userToolCalls) > 0 {
			select {
			case ch <- Chunk{Morphisms: allEnvelopes, ToolCalls: userToolCalls}:
			case <-ctx.Done():
				return
			}
		}
		select {
		case ch <- Chunk{Done: true}:
		case <-ctx.Done():
		}
	}()

	return ch, nil
}

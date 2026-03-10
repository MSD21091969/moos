// Package provider defines the LLM/AI adapter interface.
// In the MVP, only mock implementations are provided — no real model calls.
package provider

// Provider is the adapter interface for LLM/AI model calls.
type Provider interface {
	Complete(req CompletionRequest) (CompletionResult, error)
}

// CompletionRequest is a model invocation request.
type CompletionRequest struct {
	Model     string    `json:"model"`
	Messages  []Message `json:"messages"`
	MaxTokens int       `json:"max_tokens,omitempty"`
}

// Message is a single chat message.
type Message struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

// CompletionResult is the response from a model invocation.
type CompletionResult struct {
	Content    string `json:"content"`
	TokensUsed int    `json:"tokens_used"`
}

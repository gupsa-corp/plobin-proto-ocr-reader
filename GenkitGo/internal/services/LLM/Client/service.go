package Client

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// LLMModel represents available LLM models
type LLMModel string

const (
	ModelBoto          LLMModel = "boto"            // Qwen3-Omni-30B-A3B-Instruct
	ModelGPT4          LLMModel = "gpt-4"
	ModelGPT35Turbo    LLMModel = "gpt-3.5-turbo"
	ModelClaude3Sonnet LLMModel = "claude-3-sonnet"
	ModelClaude3Haiku  LLMModel = "claude-3-haiku"
)

// Message represents a chat message
type Message struct {
	Role    string `json:"role"`    // "system", "user", or "assistant"
	Content string `json:"content"`
}

// LLMRequest represents the request to LLM API
type LLMRequest struct {
	Model       string    `json:"model"`
	Messages    []Message `json:"messages"`
	Temperature float64   `json:"temperature"`
	MaxTokens   int       `json:"max_tokens,omitempty"`
	Stream      bool      `json:"stream"`
}

// LLMResponse represents the response from LLM API
type LLMResponse struct {
	ID      string `json:"id"`
	Object  string `json:"object"`
	Created int64  `json:"created"`
	Model   string `json:"model"`
	Choices []struct {
		Index   int `json:"index"`
		Message struct {
			Role    string `json:"role"`
			Content string `json:"content"`
		} `json:"message"`
		FinishReason string `json:"finish_reason"`
	} `json:"choices"`
	Usage struct {
		PromptTokens     int `json:"prompt_tokens"`
		CompletionTokens int `json:"completion_tokens"`
		TotalTokens      int `json:"total_tokens"`
	} `json:"usage"`
}

// LLMClient is a client for ai.gupsa.net/v1 LLM API
type LLMClient struct {
	baseURL string
	apiKey  string
	model   string
	client  *http.Client
}

// NewLLMClient creates a new LLM client
func NewLLMClient(baseURL, apiKey, model string) *LLMClient {
	if model == "" {
		model = string(ModelBoto)
	}

	return &LLMClient{
		baseURL: baseURL,
		apiKey:  apiKey,
		model:   model,
		client: &http.Client{
			Timeout: 60 * time.Second,
		},
	}
}

// ChatCompletion sends a chat completion request
func (c *LLMClient) ChatCompletion(ctx context.Context, messages []Message, temperature float64) (*LLMResponse, error) {
	url := fmt.Sprintf("%s/chat/completions", c.baseURL)

	reqBody := LLMRequest{
		Model:       c.model,
		Messages:    messages,
		Temperature: temperature,
		Stream:      false,
	}

	jsonData, err := json.Marshal(reqBody)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")
	if c.apiKey != "" {
		req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", c.apiKey))
	}

	resp, err := c.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API returned status %d: %s", resp.StatusCode, string(body))
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	var llmResp LLMResponse
	if err := json.Unmarshal(body, &llmResp); err != nil {
		return nil, fmt.Errorf("failed to unmarshal response: %w", err)
	}

	return &llmResp, nil
}

// AnalyzeText is a convenience method for text analysis
func (c *LLMClient) AnalyzeText(ctx context.Context, text, prompt string, temperature float64) (string, error) {
	messages := []Message{
		{Role: "system", Content: prompt},
		{Role: "user", Content: text},
	}

	resp, err := c.ChatCompletion(ctx, messages, temperature)
	if err != nil {
		return "", err
	}

	if len(resp.Choices) == 0 {
		return "", fmt.Errorf("no response from LLM")
	}

	return resp.Choices[0].Message.Content, nil
}

// Close closes the client (placeholder for future cleanup)
func (c *LLMClient) Close() error {
	// HTTP client doesn't need explicit closing
	return nil
}

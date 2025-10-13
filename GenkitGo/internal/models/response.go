package models

// APIResponse represents a standard API response
type APIResponse struct {
	Success bool        `json:"success"`
	Message string      `json:"message"`
	Data    interface{} `json:"data,omitempty"`
}

// ErrorResponse represents an error response
type ErrorResponse struct {
	Success bool   `json:"success"`
	Message string `json:"message"`
	Error   string `json:"error,omitempty"`
}

// ProcessImageResponse represents process-image endpoint response
type ProcessImageResponse struct {
	Success    bool        `json:"success"`
	Message    string      `json:"message"`
	Data       *OCRResult  `json:"data,omitempty"`
}

// AnalyzeResponse represents analyze endpoint response
type AnalyzeResponse struct {
	Success  bool   `json:"success"`
	Message  string `json:"message"`
	Analysis string `json:"analysis,omitempty"`
}

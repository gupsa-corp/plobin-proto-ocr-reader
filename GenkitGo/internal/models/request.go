package models

import "time"

// RequestType represents the type of processing request
type RequestType string

const (
	RequestTypeImage RequestType = "image"
	RequestTypePDF   RequestType = "pdf"
)

// RequestStatus represents the status of a request
type RequestStatus string

const (
	RequestStatusPending    RequestStatus = "pending"
	RequestStatusProcessing RequestStatus = "processing"
	RequestStatusCompleted  RequestStatus = "completed"
	RequestStatusFailed     RequestStatus = "failed"
)

// RequestMetadata represents metadata for a processing request
type RequestMetadata struct {
	RequestID    string        `json:"request_id"`
	OriginalFile string        `json:"original_file"`
	FileType     RequestType   `json:"file_type"`
	FileSize     int64         `json:"file_size"`
	TotalPages   int           `json:"total_pages"`
	Status       RequestStatus `json:"status"`
	CreatedAt    time.Time     `json:"created_at"`
	UpdatedAt    time.Time     `json:"updated_at"`
	ErrorMessage string        `json:"error_message,omitempty"`
}

// RequestSummary represents a summary of processing results
type RequestSummary struct {
	RequestID       string              `json:"request_id"`
	TotalPages      int                 `json:"total_pages"`
	TotalBlocks     int                 `json:"total_blocks"`
	AverageConf     float64             `json:"average_confidence"`
	ProcessingTime  float64             `json:"processing_time_seconds"`
	Pages           []PageSummary       `json:"pages"`
	OCRMetadata     map[string]interface{} `json:"ocr_metadata,omitempty"`
}

// PageSummary represents a summary of a single page
type PageSummary struct {
	PageNumber int     `json:"page_number"`
	BlockCount int     `json:"block_count"`
	AvgConf    float64 `json:"average_confidence"`
}

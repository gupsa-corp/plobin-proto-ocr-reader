package Storage

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"time"

	"github.com/google/uuid"
	"github.com/plobin/genkitgo/internal/models"
)

// Service handles file storage and retrieval
type Service struct {
	baseDir string
}

// NewService creates a new storage service
func NewService(baseDir string) *Service {
	if baseDir == "" {
		baseDir = "output"
	}

	// Create base directory if it doesn't exist
	os.MkdirAll(baseDir, 0755)

	return &Service{
		baseDir: baseDir,
	}
}

// CreateRequest creates a new request structure
func (s *Service) CreateRequest(filename string, fileType models.RequestType, fileSize int64, totalPages int) (string, error) {
	requestID := uuid.New().String()
	requestDir := filepath.Join(s.baseDir, requestID)

	// Create directories
	dirs := []string{
		requestDir,
		filepath.Join(requestDir, "pages"),
	}

	for _, dir := range dirs {
		if err := os.MkdirAll(dir, 0755); err != nil {
			return "", fmt.Errorf("failed to create directory %s: %w", dir, err)
		}
	}

	// Create metadata
	metadata := models.RequestMetadata{
		RequestID:    requestID,
		OriginalFile: filename,
		FileType:     fileType,
		FileSize:     fileSize,
		TotalPages:   totalPages,
		Status:       models.RequestStatusPending,
		CreatedAt:    time.Now(),
		UpdatedAt:    time.Now(),
	}

	// Save metadata
	if err := s.SaveMetadata(requestID, &metadata); err != nil {
		return "", fmt.Errorf("failed to save metadata: %w", err)
	}

	return requestID, nil
}

// SaveMetadata saves request metadata
func (s *Service) SaveMetadata(requestID string, metadata *models.RequestMetadata) error {
	metadataPath := filepath.Join(s.baseDir, requestID, "metadata.json")
	
	data, err := json.MarshalIndent(metadata, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal metadata: %w", err)
	}

	return os.WriteFile(metadataPath, data, 0644)
}

// GetMetadata retrieves request metadata
func (s *Service) GetMetadata(requestID string) (*models.RequestMetadata, error) {
	metadataPath := filepath.Join(s.baseDir, requestID, "metadata.json")

	data, err := os.ReadFile(metadataPath)
	if err != nil {
		return nil, fmt.Errorf("failed to read metadata: %w", err)
	}

	var metadata models.RequestMetadata
	if err := json.Unmarshal(data, &metadata); err != nil {
		return nil, fmt.Errorf("failed to unmarshal metadata: %w", err)
	}

	return &metadata, nil
}

// SaveSummary saves request summary
func (s *Service) SaveSummary(requestID string, summary *models.RequestSummary) error {
	summaryPath := filepath.Join(s.baseDir, requestID, "summary.json")

	data, err := json.MarshalIndent(summary, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal summary: %w", err)
	}

	return os.WriteFile(summaryPath, data, 0644)
}

// GetSummary retrieves request summary
func (s *Service) GetSummary(requestID string) (*models.RequestSummary, error) {
	summaryPath := filepath.Join(s.baseDir, requestID, "summary.json")

	data, err := os.ReadFile(summaryPath)
	if err != nil {
		return nil, fmt.Errorf("failed to read summary: %w", err)
	}

	var summary models.RequestSummary
	if err := json.Unmarshal(data, &summary); err != nil {
		return nil, fmt.Errorf("failed to unmarshal summary: %w", err)
	}

	return &summary, nil
}

// SavePageResult saves page OCR result
func (s *Service) SavePageResult(requestID string, pageNum int, result *models.PageResult) error {
	pageDir := filepath.Join(s.baseDir, requestID, "pages", fmt.Sprintf("%03d", pageNum))
	os.MkdirAll(pageDir, 0755)

	resultPath := filepath.Join(pageDir, "result.json")

	data, err := json.MarshalIndent(result, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal page result: %w", err)
	}

	return os.WriteFile(resultPath, data, 0644)
}

// ListRequests lists all request IDs
func (s *Service) ListRequests() ([]string, error) {
	entries, err := os.ReadDir(s.baseDir)
	if err != nil {
		return nil, fmt.Errorf("failed to read base directory: %w", err)
	}

	var requests []string
	for _, entry := range entries {
		if entry.IsDir() {
			requests = append(requests, entry.Name())
		}
	}

	return requests, nil
}

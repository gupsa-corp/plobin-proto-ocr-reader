package ListPages

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/plobin/genkitgo/internal/models"
)

type Service struct {
	baseDir string
}

type PageSummary struct {
	PageNumber int `json:"page_number"`
	BlockCount int `json:"block_count"`
}

type PagesListResult struct {
	RequestID  string        `json:"request_id"`
	TotalPages int           `json:"total_pages"`
	Pages      []PageSummary `json:"pages"`
}

func NewService(baseDir string) *Service {
	return &Service{
		baseDir: baseDir,
	}
}

// Execute lists all pages for a request
func (s *Service) Execute(ctx context.Context, requestID string) (*PagesListResult, error) {
	// Load request metadata
	metadataPath := filepath.Join(s.baseDir, requestID, "metadata.json")
	data, err := os.ReadFile(metadataPath)
	if err != nil {
		return nil, fmt.Errorf("request not found: %w", err)
	}

	var metadata models.RequestMetadata
	if err := json.Unmarshal(data, &metadata); err != nil {
		return nil, fmt.Errorf("failed to parse metadata: %w", err)
	}

	result := &PagesListResult{
		RequestID:  requestID,
		TotalPages: metadata.TotalPages,
		Pages:      make([]PageSummary, 0, metadata.TotalPages),
	}

	// Iterate through all pages
	for i := 1; i <= metadata.TotalPages; i++ {
		pagePath := filepath.Join(s.baseDir, requestID, fmt.Sprintf("page_%d.json", i))
		pageData, err := os.ReadFile(pagePath)
		if err != nil {
			// Page file might not exist yet
			result.Pages = append(result.Pages, PageSummary{
				PageNumber: i,
				BlockCount: 0,
			})
			continue
		}

		var pageResult models.OCRResult
		if err := json.Unmarshal(pageData, &pageResult); err != nil {
			result.Pages = append(result.Pages, PageSummary{
				PageNumber: i,
				BlockCount: 0,
			})
			continue
		}

		result.Pages = append(result.Pages, PageSummary{
			PageNumber: i,
			BlockCount: len(pageResult.Blocks),
		})
	}

	return result, nil
}

package GetBlock

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

func NewService(baseDir string) *Service {
	return &Service{
		baseDir: baseDir,
	}
}

// Execute retrieves a specific block by ID from request storage
func (s *Service) Execute(ctx context.Context, requestID string, blockID int) (*models.BlockInfo, error) {
	// Load request metadata to get page information
	metadataPath := filepath.Join(s.baseDir, requestID, "metadata.json")
	data, err := os.ReadFile(metadataPath)
	if err != nil {
		return nil, fmt.Errorf("request not found: %w", err)
	}

	var metadata models.RequestMetadata
	if err := json.Unmarshal(data, &metadata); err != nil {
		return nil, fmt.Errorf("failed to parse metadata: %w", err)
	}

	// Search through all pages for the block
	for i := 1; i <= metadata.TotalPages; i++ {
		pagePath := filepath.Join(s.baseDir, requestID, fmt.Sprintf("page_%d.json", i))
		pageData, err := os.ReadFile(pagePath)
		if err != nil {
			continue // Skip missing pages
		}

		var pageResult models.OCRResult
		if err := json.Unmarshal(pageData, &pageResult); err != nil {
			continue
		}

		// Find block by ID
		for _, block := range pageResult.Blocks {
			if block.ID == blockID {
				return &block, nil
			}
		}
	}

	return nil, fmt.Errorf("block %d not found in request %s", blockID, requestID)
}

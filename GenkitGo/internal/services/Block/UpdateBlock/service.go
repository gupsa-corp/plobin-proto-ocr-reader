package UpdateBlock

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

// Execute updates a specific block's text
func (s *Service) Execute(ctx context.Context, requestID string, blockID int, newText string) (*models.BlockInfo, error) {
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

	// Search through all pages for the block
	for i := 1; i <= metadata.TotalPages; i++ {
		pagePath := filepath.Join(s.baseDir, requestID, fmt.Sprintf("page_%d.json", i))
		pageData, err := os.ReadFile(pagePath)
		if err != nil {
			continue
		}

		var pageResult models.OCRResult
		if err := json.Unmarshal(pageData, &pageResult); err != nil {
			continue
		}

		// Find and update block
		found := false
		var updatedBlock *models.BlockInfo
		for j := range pageResult.Blocks {
			if pageResult.Blocks[j].ID == blockID {
				pageResult.Blocks[j].Text = newText
				updatedBlock = &pageResult.Blocks[j]
				found = true
				break
			}
		}

		if found {
			// Save updated page
			updatedData, err := json.MarshalIndent(pageResult, "", "  ")
			if err != nil {
				return nil, fmt.Errorf("failed to marshal updated page: %w", err)
			}

			if err := os.WriteFile(pagePath, updatedData, 0644); err != nil {
				return nil, fmt.Errorf("failed to save updated page: %w", err)
			}

			return updatedBlock, nil
		}
	}

	return nil, fmt.Errorf("block %d not found in request %s", blockID, requestID)
}

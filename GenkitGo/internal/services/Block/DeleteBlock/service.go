package DeleteBlock

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

// Execute deletes a specific block by removing it from the page
func (s *Service) Execute(ctx context.Context, requestID string, blockID int) error {
	// Load request metadata
	metadataPath := filepath.Join(s.baseDir, requestID, "metadata.json")
	data, err := os.ReadFile(metadataPath)
	if err != nil {
		return fmt.Errorf("request not found: %w", err)
	}

	var metadata models.RequestMetadata
	if err := json.Unmarshal(data, &metadata); err != nil {
		return fmt.Errorf("failed to parse metadata: %w", err)
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

		// Find and delete block
		found := false
		newBlocks := make([]models.BlockInfo, 0, len(pageResult.Blocks))
		for _, block := range pageResult.Blocks {
			if block.ID == blockID {
				found = true
				continue // Skip this block (delete it)
			}
			newBlocks = append(newBlocks, block)
		}

		if found {
			pageResult.Blocks = newBlocks

			// Save updated page
			updatedData, err := json.MarshalIndent(pageResult, "", "  ")
			if err != nil {
				return fmt.Errorf("failed to marshal updated page: %w", err)
			}

			if err := os.WriteFile(pagePath, updatedData, 0644); err != nil {
				return fmt.Errorf("failed to save updated page: %w", err)
			}

			return nil
		}
	}

	return fmt.Errorf("block %d not found in request %s", blockID, requestID)
}

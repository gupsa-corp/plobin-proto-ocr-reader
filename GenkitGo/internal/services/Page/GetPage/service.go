package GetPage

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

// Execute retrieves blocks for a specific page
func (s *Service) Execute(ctx context.Context, requestID string, pageNumber int) (*models.OCRResult, error) {
	// Validate page number
	if pageNumber < 1 {
		return nil, fmt.Errorf("invalid page number: %d", pageNumber)
	}

	// Load page data
	pagePath := filepath.Join(s.baseDir, requestID, fmt.Sprintf("page_%d.json", pageNumber))
	data, err := os.ReadFile(pagePath)
	if err != nil {
		if os.IsNotExist(err) {
			return nil, fmt.Errorf("page %d not found in request %s", pageNumber, requestID)
		}
		return nil, fmt.Errorf("failed to read page: %w", err)
	}

	var pageResult models.OCRResult
	if err := json.Unmarshal(data, &pageResult); err != nil {
		return nil, fmt.Errorf("failed to parse page data: %w", err)
	}

	return &pageResult, nil
}

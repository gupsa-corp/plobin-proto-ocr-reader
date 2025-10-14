package ExtractBlocks

import (
	"context"
	"fmt"

	"github.com/plobin/genkitgo/internal/models"
	"github.com/plobin/genkitgo/internal/services/OCR/SuryaClient"
)

type Service struct {
	language    string
	suryaClient *SuryaClient.Service
}

func NewService(language string) *Service {
	if language == "" {
		language = "kor+eng"
	}
	return &Service{
		language:    language,
		suryaClient: SuryaClient.NewService("http://localhost:6004"),
	}
}

// Execute performs OCR on an image using Surya (ML-based layout detection + OCR)
func (s *Service) Execute(ctx context.Context, imagePath string, options models.OCROptions) (*models.OCRResult, error) {
	// Call Surya OCR service
	// Use ExecuteLayout for fast layout detection with structure
	result, err := s.suryaClient.ExecuteLayout(ctx, imagePath)
	if err != nil {
		return nil, fmt.Errorf("surya OCR failed: %w", err)
	}

	return result, nil
}

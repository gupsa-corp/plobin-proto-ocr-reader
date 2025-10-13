package ExtractBlocks

import (
	"context"
	"fmt"

	"github.com/otiai10/gosseract/v2"
	"github.com/plobin/genkitgo/internal/models"
)

type Service struct {
	language string
}

func NewService(language string) *Service {
	if language == "" {
		language = "kor+eng"
	}
	return &Service{
		language: language,
	}
}

// Execute performs OCR on an image and extracts text blocks
func (s *Service) Execute(ctx context.Context, imagePath string, options models.OCROptions) (*models.OCRResult, error) {
	// Initialize Tesseract client
	client := gosseract.NewClient()
	defer client.Close()

	// Set language
	lang := s.language
	if options.Language != "" {
		lang = options.Language
	}
	client.SetLanguage(lang)

	// Set image
	if err := client.SetImage(imagePath); err != nil {
		return nil, fmt.Errorf("failed to set image: %w", err)
	}

	// Get bounding boxes
	boxes, err := client.GetBoundingBoxes(gosseract.RIL_WORD)
	if err != nil {
		return nil, fmt.Errorf("failed to get bounding boxes: %w", err)
	}

	// Convert to BlockInfo
	blocks := make([]models.BlockInfo, 0, len(boxes))
	for i, box := range boxes {
		if box.Word == "" {
			continue
		}

		block := models.BlockInfo{
			ID:   i,
			Text: box.Word,
			Confidence: float64(box.Confidence) / 100.0, // Convert 0-100 to 0-1
			BBox: models.BBox{
				X:      box.Box.Min.X,
				Y:      box.Box.Min.Y,
				Width:  box.Box.Max.X - box.Box.Min.X,
				Height: box.Box.Max.Y - box.Box.Min.Y,
			},
			BBoxPoints: []models.Point{
				{X: box.Box.Min.X, Y: box.Box.Min.Y},
				{X: box.Box.Max.X, Y: box.Box.Min.Y},
				{X: box.Box.Max.X, Y: box.Box.Max.Y},
				{X: box.Box.Min.X, Y: box.Box.Max.Y},
			},
			BlockType: models.BlockTypeText,
		}
		blocks = append(blocks, block)
	}

	// Calculate average confidence
	avgConfidence := 0.0
	if len(blocks) > 0 {
		for _, block := range blocks {
			avgConfidence += block.Confidence
		}
		avgConfidence /= float64(len(blocks))
	}

	result := &models.OCRResult{
		RequestID:   "",
		TotalBlocks: len(blocks),
		AverageConf: avgConfidence,
		Blocks:      blocks,
	}

	return result, nil
}

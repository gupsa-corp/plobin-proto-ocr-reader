package GetImage

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
)

type Service struct {
	baseDir string
}

type ImageResult struct {
	FilePath    string `json:"file_path"`
	ContentType string `json:"content_type"`
	Data        []byte `json:"-"` // Binary data not included in JSON
}

func NewService(baseDir string) *Service {
	return &Service{
		baseDir: baseDir,
	}
}

// Execute retrieves the original image file for a specific page
func (s *Service) Execute(ctx context.Context, requestID string, pageNumber int) (*ImageResult, error) {
	if pageNumber < 1 {
		return nil, fmt.Errorf("invalid page number: %d", pageNumber)
	}

	// Try different image extensions
	extensions := []string{".png", ".jpg", ".jpeg"}
	for _, ext := range extensions {
		imagePath := filepath.Join(s.baseDir, requestID, fmt.Sprintf("page_%d%s", pageNumber, ext))

		if _, err := os.Stat(imagePath); err == nil {
			// File exists, read it
			data, err := os.ReadFile(imagePath)
			if err != nil {
				return nil, fmt.Errorf("failed to read image: %w", err)
			}

			contentType := "image/png"
			if ext == ".jpg" || ext == ".jpeg" {
				contentType = "image/jpeg"
			}

			return &ImageResult{
				FilePath:    imagePath,
				ContentType: contentType,
				Data:        data,
			}, nil
		}
	}

	return nil, fmt.Errorf("image for page %d not found in request %s", pageNumber, requestID)
}

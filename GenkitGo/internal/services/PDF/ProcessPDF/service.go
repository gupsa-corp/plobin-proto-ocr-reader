package ProcessPDF

import (
	"context"
	"fmt"
	"image/png"
	"os"
	"path/filepath"

	"github.com/gen2brain/go-fitz"
	"github.com/plobin/genkitgo/internal/models"
	"github.com/plobin/genkitgo/internal/services/OCR/ExtractBlocks"
)

type Service struct {
	ocrService *ExtractBlocks.Service
	dpi        float64
}

type PDFResult struct {
	RequestID   string             `json:"request_id"`
	TotalPages  int                `json:"total_pages"`
	TotalBlocks int                `json:"total_blocks"`
	AverageConf float64            `json:"average_confidence"`
	Pages       []models.OCRResult `json:"pages"`
}

func NewService(language string, dpi float64) *Service {
	if dpi == 0 {
		dpi = 150.0  // Default DPI
	}
	return &Service{
		ocrService: ExtractBlocks.NewService(language),
		dpi:        dpi,
	}
}

// Execute processes a PDF file: converts to images and performs OCR on each page
func (s *Service) Execute(ctx context.Context, pdfPath string, options models.OCROptions) (*PDFResult, error) {
	// Open PDF document
	doc, err := fitz.New(pdfPath)
	if err != nil {
		return nil, fmt.Errorf("failed to open PDF: %w", err)
	}
	defer doc.Close()

	pageCount := doc.NumPage()
	if pageCount == 0 {
		return nil, fmt.Errorf("PDF has no pages")
	}

	// Create temporary directory for images
	tempDir, err := os.MkdirTemp("", "pdf-*")
	if err != nil {
		return nil, fmt.Errorf("failed to create temp directory: %w", err)
	}
	defer os.RemoveAll(tempDir)

	// Process each page
	pages := make([]models.OCRResult, 0, pageCount)
	totalBlocks := 0
	totalConfidence := 0.0

	for pageNum := 0; pageNum < pageCount; pageNum++ {
		// Render page to image
		img, err := doc.Image(pageNum)
		if err != nil {
			return nil, fmt.Errorf("failed to render page %d: %w", pageNum+1, err)
		}

		// Save image to temporary file
		imagePath := filepath.Join(tempDir, fmt.Sprintf("page_%d.png", pageNum+1))
		file, err := os.Create(imagePath)
		if err != nil {
			return nil, fmt.Errorf("failed to create image file: %w", err)
		}

		if err := png.Encode(file, img); err != nil {
			file.Close()
			return nil, fmt.Errorf("failed to encode image: %w", err)
		}
		file.Close()

		// Perform OCR on the image
		result, err := s.ocrService.Execute(ctx, imagePath, options)
		if err != nil {
			return nil, fmt.Errorf("failed to OCR page %d: %w", pageNum+1, err)
		}

		// Update block IDs to be globally unique
		for i := range result.Blocks {
			result.Blocks[i].ID = totalBlocks + i
		}

		totalBlocks += result.TotalBlocks
		totalConfidence += result.AverageConf

		pages = append(pages, *result)
	}

	// Calculate overall average confidence
	avgConfidence := 0.0
	if pageCount > 0 {
		avgConfidence = totalConfidence / float64(pageCount)
	}

	return &PDFResult{
		RequestID:   "",
		TotalPages:  pageCount,
		TotalBlocks: totalBlocks,
		AverageConf: avgConfidence,
		Pages:       pages,
	}, nil
}

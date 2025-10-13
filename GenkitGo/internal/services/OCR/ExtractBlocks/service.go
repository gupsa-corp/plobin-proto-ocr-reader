package ExtractBlocks

import (
	"context"
	"encoding/json"
	"fmt"
	"os/exec"
	"time"

	"github.com/plobin/genkitgo/internal/models"
)

// Service handles OCR block extraction using Python Surya OCR
type Service struct {
	pythonPath string
	scriptPath string
}

// NewService creates a new OCR extraction service
func NewService(pythonPath, scriptPath string) *Service {
	if pythonPath == "" {
		pythonPath = "python3"
	}
	if scriptPath == "" {
		scriptPath = "../FastApi/services/ocr_wrapper.py"
	}

	return &Service{
		pythonPath: pythonPath,
		scriptPath: scriptPath,
	}
}

// Execute extracts text blocks from an image using Surya OCR
func (s *Service) Execute(ctx context.Context, imagePath string, options models.OCROptions) (*models.OCRResult, error) {
	startTime := time.Now()

	// Prepare JSON options
	optsJSON, err := json.Marshal(options)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal options: %w", err)
	}

	// Call Python script
	cmd := exec.CommandContext(ctx, s.pythonPath, s.scriptPath, imagePath, string(optsJSON))
	
	output, err := cmd.CombinedOutput()
	if err != nil {
		return nil, fmt.Errorf("OCR processing failed: %w, output: %s", err, string(output))
	}

	// Parse result
	var result models.OCRResult
	if err := json.Unmarshal(output, &result); err != nil {
		return nil, fmt.Errorf("failed to parse OCR result: %w", err)
	}

	result.ProcessingTime = time.Since(startTime).Seconds()

	return &result, nil
}

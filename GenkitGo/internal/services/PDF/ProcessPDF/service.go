package ProcessPDF

import (
	"context"
	"encoding/json"
	"fmt"
	"os/exec"
	"time"

	"github.com/plobin/genkitgo/internal/models"
)

// Service handles PDF processing using Python
type Service struct {
	pythonPath string
	scriptPath string
}

// PDFResult represents the result of PDF processing
type PDFResult struct {
	RequestID        string               `json:"request_id"`
	TotalPages       int                  `json:"total_pages"`
	TotalBlocks      int                  `json:"total_blocks"`
	AverageConf      float64              `json:"average_confidence"`
	Pages            []models.PageResult  `json:"pages"`
	ProcessingTime   float64              `json:"processing_time"`
}

// NewService creates a new PDF processing service
func NewService(pythonPath, scriptPath string) *Service {
	if pythonPath == "" {
		pythonPath = "python3"
	}
	if scriptPath == "" {
		scriptPath = "./FastApi/services/pdf_wrapper.py"
	}

	return &Service{
		pythonPath: pythonPath,
		scriptPath: scriptPath,
	}
}

// Execute processes a PDF file and extracts text blocks from all pages
func (s *Service) Execute(ctx context.Context, pdfPath string, options models.OCROptions) (*PDFResult, error) {
	startTime := time.Now()

	// Prepare JSON options
	optsJSON, err := json.Marshal(map[string]interface{}{
		"merge_blocks":         options.MergeBlocks,
		"merge_threshold":      options.MergeThreshold,
		"create_sections":      options.CreateSections,
		"build_hierarchy_tree": options.BuildHierarchyTree,
		"language":             options.Language,
		"use_gpu":              false, // Can be made configurable
		"dpi":                  150,   // Can be made configurable
	})
	if err != nil {
		return nil, fmt.Errorf("failed to marshal options: %w", err)
	}

	// Call Python script
	cmd := exec.CommandContext(ctx, s.pythonPath, s.scriptPath, pdfPath, string(optsJSON))
	
	output, err := cmd.CombinedOutput()
	if err != nil {
		return nil, fmt.Errorf("PDF processing failed: %w, output: %s", err, string(output))
	}

	// Parse result
	var result PDFResult
	if err := json.Unmarshal(output, &result); err != nil {
		return nil, fmt.Errorf("failed to parse PDF result: %w, output: %s", err, string(output))
	}

	result.ProcessingTime = time.Since(startTime).Seconds()

	return &result, nil
}

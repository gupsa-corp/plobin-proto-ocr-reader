package SuryaClient

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"os"
	"path/filepath"
	"time"

	"github.com/plobin/genkitgo/internal/models"
)

type Service struct {
	baseURL string
	client  *http.Client
}

type SuryaResponse struct {
	Success bool   `json:"success"`
	Message string `json:"message"`
	Data    struct {
		TotalBlocks      int                  `json:"total_blocks"`
		AverageConfidence float64             `json:"average_confidence,omitempty"`
		Blocks           []models.BlockInfo   `json:"blocks"`
		ProcessingTime   float64              `json:"processing_time"`
	} `json:"data"`
}

func NewService(baseURL string) *Service {
	if baseURL == "" {
		baseURL = "http://localhost:6004"
	}

	return &Service{
		baseURL: baseURL,
		client: &http.Client{
			Timeout: 5 * time.Minute, // Surya can be slow
		},
	}
}

// ExecuteLayout performs layout detection using Surya
func (s *Service) ExecuteLayout(ctx context.Context, imagePath string) (*models.OCRResult, error) {
	return s.callSuryaAPI(ctx, imagePath, "/api/surya/layout", "")
}

// ExecuteOCR performs full OCR with layout detection using Surya
func (s *Service) ExecuteOCR(ctx context.Context, imagePath string, languages string) (*models.OCRResult, error) {
	if languages == "" {
		languages = "en"
	}
	return s.callSuryaAPI(ctx, imagePath, "/api/surya/ocr", languages)
}

// ExecuteDetection performs text line detection using Surya
func (s *Service) ExecuteDetection(ctx context.Context, imagePath string) (*models.OCRResult, error) {
	return s.callSuryaAPI(ctx, imagePath, "/api/surya/detect", "")
}

// CheckHealth checks if Surya service is available
func (s *Service) CheckHealth(ctx context.Context) error {
	req, err := http.NewRequestWithContext(ctx, "GET", s.baseURL+"/health", nil)
	if err != nil {
		return fmt.Errorf("failed to create health check request: %w", err)
	}

	resp, err := s.client.Do(req)
	if err != nil {
		return fmt.Errorf("surya service unavailable: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("surya service unhealthy: status %d", resp.StatusCode)
	}

	return nil
}

func (s *Service) callSuryaAPI(ctx context.Context, imagePath string, endpoint string, languages string) (*models.OCRResult, error) {
	// Open image file
	file, err := os.Open(imagePath)
	if err != nil {
		return nil, fmt.Errorf("failed to open image: %w", err)
	}
	defer file.Close()

	// Create multipart form
	body := &bytes.Buffer{}
	writer := multipart.NewWriter(body)

	// Add file
	part, err := writer.CreateFormFile("file", filepath.Base(imagePath))
	if err != nil {
		return nil, fmt.Errorf("failed to create form file: %w", err)
	}

	if _, err := io.Copy(part, file); err != nil {
		return nil, fmt.Errorf("failed to copy file: %w", err)
	}

	// Add languages if provided
	if languages != "" {
		if err := writer.WriteField("languages", languages); err != nil {
			return nil, fmt.Errorf("failed to add languages field: %w", err)
		}
	}

	if err := writer.Close(); err != nil {
		return nil, fmt.Errorf("failed to close writer: %w", err)
	}

	// Create HTTP request
	url := s.baseURL + endpoint
	req, err := http.NewRequestWithContext(ctx, "POST", url, body)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", writer.FormDataContentType())

	// Send request
	startTime := time.Now()
	resp, err := s.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to call surya API: %w", err)
	}
	defer resp.Body.Close()

	// Read response
	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("surya API error: status %d, body: %s", resp.StatusCode, string(respBody))
	}

	// Parse response
	var suryaResp SuryaResponse
	if err := json.Unmarshal(respBody, &suryaResp); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}

	if !suryaResp.Success {
		return nil, fmt.Errorf("surya API returned error: %s", suryaResp.Message)
	}

	// Convert to OCRResult
	result := &models.OCRResult{
		RequestID:   "",
		TotalBlocks: suryaResp.Data.TotalBlocks,
		AverageConf: suryaResp.Data.AverageConfidence,
		Blocks:      suryaResp.Data.Blocks,
	}

	// Log processing time
	totalTime := time.Since(startTime)
	fmt.Printf("Surya %s: %d blocks, %.2fs (API: %.2fs)\n",
		endpoint, result.TotalBlocks, totalTime.Seconds(), suryaResp.Data.ProcessingTime)

	return result, nil
}

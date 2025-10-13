package GetTemplate

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
	templatesDir := filepath.Join(baseDir, "templates")
	os.MkdirAll(templatesDir, 0755)
	return &Service{
		baseDir: templatesDir,
	}
}

// Execute retrieves a specific template by ID
func (s *Service) Execute(ctx context.Context, templateID string) (*models.Template, error) {
	templatePath := filepath.Join(s.baseDir, templateID+".json")
	data, err := os.ReadFile(templatePath)
	if err != nil {
		if os.IsNotExist(err) {
			return nil, fmt.Errorf("template not found: %s", templateID)
		}
		return nil, fmt.Errorf("failed to read template: %w", err)
	}

	var template models.Template
	if err := json.Unmarshal(data, &template); err != nil {
		return nil, fmt.Errorf("failed to parse template: %w", err)
	}

	return &template, nil
}

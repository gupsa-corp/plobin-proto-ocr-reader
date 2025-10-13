package CreateTemplate

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"time"

	"github.com/google/uuid"
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

// Execute creates a new template
func (s *Service) Execute(ctx context.Context, req models.TemplateCreateRequest) (*models.Template, error) {
	if req.Name == "" {
		return nil, fmt.Errorf("template name is required")
	}

	if len(req.Fields) == 0 {
		return nil, fmt.Errorf("template must have at least one field")
	}

	template := models.Template{
		ID:          uuid.New().String(),
		Name:        req.Name,
		Description: req.Description,
		Fields:      req.Fields,
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
	}

	// Save template to file
	templatePath := filepath.Join(s.baseDir, template.ID+".json")
	data, err := json.MarshalIndent(template, "", "  ")
	if err != nil {
		return nil, fmt.Errorf("failed to marshal template: %w", err)
	}

	if err := os.WriteFile(templatePath, data, 0644); err != nil {
		return nil, fmt.Errorf("failed to save template: %w", err)
	}

	return &template, nil
}

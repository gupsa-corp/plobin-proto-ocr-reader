package ListTemplates

import (
	"context"
	"encoding/json"
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

// Execute lists all available templates
func (s *Service) Execute(ctx context.Context) ([]models.Template, error) {
	entries, err := os.ReadDir(s.baseDir)
	if err != nil {
		return []models.Template{}, nil // Return empty list if directory doesn't exist
	}

	templates := make([]models.Template, 0)
	for _, entry := range entries {
		if entry.IsDir() || filepath.Ext(entry.Name()) != ".json" {
			continue
		}

		templatePath := filepath.Join(s.baseDir, entry.Name())
		data, err := os.ReadFile(templatePath)
		if err != nil {
			continue
		}

		var template models.Template
		if err := json.Unmarshal(data, &template); err != nil {
			continue
		}

		templates = append(templates, template)
	}

	return templates, nil
}

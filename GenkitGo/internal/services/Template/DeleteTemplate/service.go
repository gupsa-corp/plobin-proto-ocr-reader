package DeleteTemplate

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
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

// Execute deletes a template by ID
func (s *Service) Execute(ctx context.Context, templateID string) error {
	templatePath := filepath.Join(s.baseDir, templateID+".json")

	if _, err := os.Stat(templatePath); err != nil {
		if os.IsNotExist(err) {
			return fmt.Errorf("template not found: %s", templateID)
		}
		return fmt.Errorf("failed to check template: %w", err)
	}

	if err := os.Remove(templatePath); err != nil {
		return fmt.Errorf("failed to delete template: %w", err)
	}

	return nil
}

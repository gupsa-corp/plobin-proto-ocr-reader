package models

import "time"

type TemplateField struct {
	Name        string   `json:"name"`
	Type        string   `json:"type"` // text, number, date, etc.
	Required    bool     `json:"required"`
	Description string   `json:"description,omitempty"`
	BlockIDs    []int    `json:"block_ids,omitempty"` // Associated block IDs
	Validation  string   `json:"validation,omitempty"` // Validation rules
}

type Template struct {
	ID          string          `json:"id"`
	Name        string          `json:"name"`
	Description string          `json:"description,omitempty"`
	Fields      []TemplateField `json:"fields"`
	CreatedAt   time.Time       `json:"created_at"`
	UpdatedAt   time.Time       `json:"updated_at"`
}

type TemplateCreateRequest struct {
	Name        string          `json:"name"`
	Description string          `json:"description,omitempty"`
	Fields      []TemplateField `json:"fields"`
}

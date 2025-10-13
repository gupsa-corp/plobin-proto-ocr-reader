package models

// OCROptions represents OCR processing options
type OCROptions struct {
	MergeBlocks        bool    `json:"merge_blocks"`
	MergeThreshold     int     `json:"merge_threshold"`
	ConfidenceThreshold float64 `json:"confidence_threshold"`
	CreateSections     bool    `json:"create_sections"`
	BuildHierarchyTree bool    `json:"build_hierarchy_tree"`
	Language           string  `json:"language"`
}

// OCRResult represents the result of OCR processing
type OCRResult struct {
	RequestID      string                 `json:"request_id"`
	Blocks         []BlockInfo            `json:"blocks"`
	TotalBlocks    int                    `json:"total_blocks"`
	AverageConf    float64                `json:"average_confidence"`
	ProcessingTime float64                `json:"processing_time"`
	Sections       []Section              `json:"sections,omitempty"`
	HierarchyTree  map[string]interface{} `json:"hierarchy_tree,omitempty"`
}

// PageResult represents OCR result for a single page
type PageResult struct {
	PageNumber      int                    `json:"page_number"`
	Blocks          []BlockInfo            `json:"blocks"`
	TotalBlocks     int                    `json:"total_blocks"`
	AverageConf     float64                `json:"average_confidence"`
	OriginalImage   string                 `json:"original_image"`
	Visualization   string                 `json:"visualization,omitempty"`
	Sections        []Section              `json:"sections,omitempty"`
	HierarchyTree   map[string]interface{} `json:"hierarchy_tree,omitempty"`
}

package models

// BlockType represents the type of a text block
type BlockType string

const (
	BlockTypeText      BlockType = "text"
	BlockTypeTitle     BlockType = "title"
	BlockTypeTable     BlockType = "table"
	BlockTypeImage     BlockType = "image"
	BlockTypeEquation  BlockType = "equation"
	BlockTypeFootnote  BlockType = "footnote"
	BlockTypeHeader    BlockType = "header"
	BlockTypeFooter    BlockType = "footer"
	BlockTypeListItem  BlockType = "list_item"
	BlockTypeUnknown   BlockType = "unknown"
)

// BBox represents a bounding box
type BBox struct {
	X      int `json:"x"`
	Y      int `json:"y"`
	Width  int `json:"width"`
	Height int `json:"height"`
}

// Point represents a coordinate point
type Point struct {
	X int `json:"x"`
	Y int `json:"y"`
}

// BlockInfo represents OCR block information
type BlockInfo struct {
	ID          int       `json:"id"`
	Text        string    `json:"text"`
	Confidence  float64   `json:"confidence"`
	BBox        BBox      `json:"bbox"`
	BBoxPoints  []Point   `json:"bbox_points"`
	BlockType   BlockType `json:"block_type"`
	Language    string    `json:"language,omitempty"`
	LayoutLabel string    `json:"layout_label,omitempty"` // Surya layout label (Title, Text, Table, etc.)
}

// BlockResult represents blocks with metadata
type BlockResult struct {
	Blocks        []BlockInfo            `json:"blocks"`
	TotalBlocks   int                    `json:"total_blocks"`
	AverageConf   float64                `json:"average_confidence"`
	Sections      []Section              `json:"sections,omitempty"`
	HierarchyTree map[string]interface{} `json:"hierarchy_tree,omitempty"`
}

// Section represents a logical section of blocks
type Section struct {
	ID     string      `json:"id"`
	Type   string      `json:"type"` // "header", "body", "footer", etc.
	Blocks []BlockInfo `json:"blocks"`
}

package models

// Block - OCR 텍스트 블록 정보
type Block struct {
	Text       string  `json:"text"`
	Confidence float64 `json:"confidence"`
	BBox       []int   `json:"bbox"`        // [x1, y1, x2, y2]
	BlockType  string  `json:"block_type"`  // text, title, table, image
}

// BlockResult - OCR 처리 결과
type BlockResult struct {
	ImagePath      string  `json:"image_path"`
	Blocks         []Block `json:"blocks"`
	ProcessingTime float64 `json:"processing_time"`
	TotalBlocks    int     `json:"total_blocks"`
}

// PDFPage - PDF 페이지 정보
type PDFPage struct {
	PageNumber int          `json:"page_number"`
	ImagePath  string       `json:"image_path"`
	Result     *BlockResult `json:"result"`
}

// PDFResult - PDF 전체 처리 결과
type PDFResult struct {
	PDFPath        string    `json:"pdf_path"`
	Pages          []PDFPage `json:"pages"`
	TotalPages     int       `json:"total_pages"`
	ProcessingTime float64   `json:"processing_time"`
}

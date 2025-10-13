package processpdf

import (
	"encoding/json"
	"errors"
	"net/http"
)

// ProcessPDFRequest - PDF OCR 요청 구조체
type ProcessPDFRequest struct {
	PDFPath             string  `json:"pdf_path" validate:"required"`
	ConfidenceThreshold float64 `json:"confidence_threshold"`
	MergeBlocks         bool    `json:"merge_blocks"`
}

// ValidateRequest - 입력 검증 (1파일 1메서드 원칙)
func ValidateRequest(r *http.Request) (*ProcessPDFRequest, error) {
	var req ProcessPDFRequest

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		return nil, errors.New("잘못된 요청 형식입니다")
	}

	if req.PDFPath == "" {
		return nil, errors.New("pdf_path는 필수입니다")
	}

	if req.ConfidenceThreshold == 0 {
		req.ConfidenceThreshold = 0.5
	}

	return &req, nil
}

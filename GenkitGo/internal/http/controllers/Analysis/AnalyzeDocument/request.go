package analyzedocument

import (
	"encoding/json"
	"errors"
	"net/http"
)

// AnalyzeDocumentRequest - 문서 분석 요청 구조체
type AnalyzeDocumentRequest struct {
	ImagePath string `json:"image_path" validate:"required"`
	Language  string `json:"language"`
}

// ValidateRequest - 입력 검증 (1파일 1메서드 원칙)
func ValidateRequest(r *http.Request) (*AnalyzeDocumentRequest, error) {
	var req AnalyzeDocumentRequest

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		return nil, errors.New("잘못된 요청 형식입니다")
	}

	if req.ImagePath == "" {
		return nil, errors.New("image_path는 필수입니다")
	}

	if req.Language == "" {
		req.Language = "ko"
	}

	return &req, nil
}

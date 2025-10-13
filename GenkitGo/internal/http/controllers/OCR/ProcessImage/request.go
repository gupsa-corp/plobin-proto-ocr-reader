package processimage

import (
	"encoding/json"
	"errors"
	"net/http"
)

// ProcessImageRequest - 이미지 OCR 요청 구조체
type ProcessImageRequest struct {
	ImagePath           string  `json:"image_path" validate:"required"`
	ConfidenceThreshold float64 `json:"confidence_threshold"`
	MergeBlocks         bool    `json:"merge_blocks"`
	MergeThreshold      int     `json:"merge_threshold"`
}

// ValidateRequest - 입력 검증 (1파일 1메서드 원칙)
// 역할: HTTP Request Body → 구조체 변환 + 유효성 검증
func ValidateRequest(r *http.Request) (*ProcessImageRequest, error) {
	var req ProcessImageRequest

	// JSON 디코딩
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		return nil, errors.New("잘못된 요청 형식입니다")
	}

	// 필수 필드 검증
	if req.ImagePath == "" {
		return nil, errors.New("image_path는 필수입니다")
	}

	// 기본값 설정
	if req.ConfidenceThreshold == 0 {
		req.ConfidenceThreshold = 0.5
	}

	if req.MergeThreshold == 0 {
		req.MergeThreshold = 30
	}

	return &req, nil
}

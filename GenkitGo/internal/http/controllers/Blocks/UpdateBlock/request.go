package updateblock

import (
	"encoding/json"
	"errors"
	"net/http"
)

// UpdateBlockRequest - 블록 수정 요청 구조체
type UpdateBlockRequest struct {
	BlockID   string `json:"block_id" validate:"required"`
	Text      string `json:"text"`
	BlockType string `json:"block_type"`
}

// ValidateRequest - 입력 검증 (1파일 1메서드 원칙)
func ValidateRequest(r *http.Request) (*UpdateBlockRequest, error) {
	var req UpdateBlockRequest

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		return nil, errors.New("잘못된 요청 형식입니다")
	}

	if req.BlockID == "" {
		return nil, errors.New("block_id는 필수입니다")
	}

	return &req, nil
}

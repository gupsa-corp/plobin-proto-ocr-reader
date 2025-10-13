package getblock

import (
	"errors"
	"net/http"
)

// GetBlockRequest - 블록 조회 요청 구조체
type GetBlockRequest struct {
	BlockID string `json:"block_id" validate:"required"`
}

// ValidateRequest - 입력 검증 (1파일 1메서드 원칙)
func ValidateRequest(r *http.Request) (*GetBlockRequest, error) {
	blockID := r.URL.Query().Get("block_id")

	if blockID == "" {
		return nil, errors.New("block_id는 필수입니다")
	}

	return &GetBlockRequest{
		BlockID: blockID,
	}, nil
}

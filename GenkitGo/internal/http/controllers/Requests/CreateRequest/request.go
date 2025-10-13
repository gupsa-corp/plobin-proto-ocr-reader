package createrequest

import (
	"encoding/json"
	"errors"
	"net/http"
)

// CreateRequestRequest - 요청 생성 구조체
type CreateRequestRequest struct {
	FilePath string `json:"file_path" validate:"required"`
	FileType string `json:"file_type"`
}

// ValidateRequest - 입력 검증 (1파일 1메서드 원칙)
func ValidateRequest(r *http.Request) (*CreateRequestRequest, error) {
	var req CreateRequestRequest

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		return nil, errors.New("잘못된 요청 형식입니다")
	}

	if req.FilePath == "" {
		return nil, errors.New("file_path는 필수입니다")
	}

	return &req, nil
}

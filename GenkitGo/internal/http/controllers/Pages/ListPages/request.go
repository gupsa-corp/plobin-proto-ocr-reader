package listpages

import (
	"errors"
	"net/http"
)

// ListPagesRequest - 페이지 목록 조회 요청 구조체
type ListPagesRequest struct {
	RequestID string `json:"request_id" validate:"required"`
}

// ValidateRequest - 입력 검증 (1파일 1메서드 원칙)
func ValidateRequest(r *http.Request) (*ListPagesRequest, error) {
	requestID := r.URL.Query().Get("request_id")

	if requestID == "" {
		return nil, errors.New("request_id는 필수입니다")
	}

	return &ListPagesRequest{
		RequestID: requestID,
	}, nil
}

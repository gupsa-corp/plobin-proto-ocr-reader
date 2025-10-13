package getimage

import (
	"errors"
	"net/http"
	"strconv"
)

// GetImageRequest - 이미지 조회 요청 구조체
type GetImageRequest struct {
	RequestID  string `json:"request_id" validate:"required"`
	PageNumber int    `json:"page_number" validate:"required"`
}

// ValidateRequest - 입력 검증 (1파일 1메서드 원칙)
func ValidateRequest(r *http.Request) (*GetImageRequest, error) {
	requestID := r.URL.Query().Get("request_id")
	pageNumStr := r.URL.Query().Get("page_number")

	if requestID == "" {
		return nil, errors.New("request_id는 필수입니다")
	}

	if pageNumStr == "" {
		return nil, errors.New("page_number는 필수입니다")
	}

	pageNumber, err := strconv.Atoi(pageNumStr)
	if err != nil {
		return nil, errors.New("page_number는 숫자여야 합니다")
	}

	return &GetImageRequest{
		RequestID:  requestID,
		PageNumber: pageNumber,
	}, nil
}

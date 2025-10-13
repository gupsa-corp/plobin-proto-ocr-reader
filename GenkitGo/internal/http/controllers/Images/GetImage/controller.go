package getimage

import (
	"net/http"

	errorresponse "github.com/plobin/genkitgo/internal/http/common/ErrorResponse"
	successresponse "github.com/plobin/genkitgo/internal/http/common/SuccessResponse"
)

// Handle - 이미지 조회 핸들러 (1파일 1메서드 원칙)
// Route: GET /api/images
// 역할: Request 수신 → Service 호출 → Response 반환
func Handle(w http.ResponseWriter, r *http.Request) {
	// TODO: 이미지 조회 로직 구현
	// FastAPI의 api/endpoints/images.py 포팅 필요

	req, err := ValidateRequest(r)
	if err != nil {
		errorresponse.Write(w, http.StatusBadRequest, err.Error())
		return
	}

	successresponse.Write(w, map[string]interface{}{
		"message":     "이미지 조회 엔드포인트 (구현 예정)",
		"request_id":  req.RequestID,
		"page_number": req.PageNumber,
	})
}

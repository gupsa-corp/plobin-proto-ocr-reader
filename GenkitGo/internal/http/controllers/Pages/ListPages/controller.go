package listpages

import (
	"net/http"

	errorresponse "github.com/plobin/genkitgo/internal/http/common/ErrorResponse"
	successresponse "github.com/plobin/genkitgo/internal/http/common/SuccessResponse"
)

// Handle - 페이지 목록 조회 핸들러 (1파일 1메서드 원칙)
// Route: GET /api/pages
// 역할: Request 수신 → Service 호출 → Response 반환
func Handle(w http.ResponseWriter, r *http.Request) {
	// TODO: 페이지 목록 조회 로직 구현
	// FastAPI의 api/endpoints/pages.py 포팅 필요

	requestID := r.URL.Query().Get("request_id")
	if requestID == "" {
		errorresponse.Write(w, http.StatusBadRequest, "request_id는 필수입니다")
		return
	}

	successresponse.Write(w, map[string]interface{}{
		"message":    "페이지 목록 조회 엔드포인트 (구현 예정)",
		"request_id": requestID,
		"pages":      []string{},
	})
}

package listrequests

import (
	"net/http"

	successresponse "github.com/plobin/genkitgo/internal/http/common/SuccessResponse"
)

// Handle - 요청 목록 조회 핸들러 (1파일 1메서드 원칙)
// Route: GET /api/requests
// 역할: Request 수신 → Service 호출 → Response 반환
func Handle(w http.ResponseWriter, r *http.Request) {
	// TODO: 요청 목록 조회 로직 구현
	// FastAPI의 api/endpoints/requests/request_queries.py 포팅 필요

	successresponse.Write(w, map[string]interface{}{
		"message":  "요청 목록 조회 엔드포인트 (구현 예정)",
		"requests": []string{},
	})
}

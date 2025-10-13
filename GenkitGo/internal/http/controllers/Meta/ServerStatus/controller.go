package serverstatus

import (
	"net/http"
	"time"

	successresponse "github.com/plobin/genkitgo/internal/http/common/SuccessResponse"
)

var serverStartTime = time.Now()

// Handle - 서버 상태 조회 핸들러 (1파일 1메서드 원칙)
// Route: GET /
// 역할: 서버 상태 정보 반환
func Handle(w http.ResponseWriter, r *http.Request) {
	uptime := time.Since(serverStartTime)

	successresponse.Write(w, map[string]interface{}{
		"status":  "ok",
		"message": "GenkitGo OCR API Server",
		"uptime":  uptime.String(),
		"version": "1.0.0",
	})
}

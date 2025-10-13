package analyzedocument

import (
	"net/http"

	successresponse "github.com/plobin/genkitgo/internal/http/common/SuccessResponse"
)

// Handle - 문서 분석 핸들러 (1파일 1메서드 원칙)
// Route: POST /api/analysis/analyze-document
// 역할: Request 수신 → Genkit Flow 호출 → Response 반환
func Handle(w http.ResponseWriter, r *http.Request) {
	// TODO: LLM 문서 분석 로직 구현
	// Genkit Flow 통합 필요
	// FastAPI의 api/endpoints/analysis/ 포팅 필요

	successresponse.Write(w, map[string]string{
		"message": "문서 분석 엔드포인트 (구현 예정)",
		"note":    "Genkit Flow 통합 예정",
	})
}

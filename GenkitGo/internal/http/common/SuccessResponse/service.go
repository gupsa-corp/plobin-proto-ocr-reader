package successresponse

import (
	"encoding/json"
	"net/http"
)

// APIResponse - 표준 API 응답 구조체 (CLAUDE.md 준수)
type APIResponse struct {
	Success bool        `json:"success"`
	Message string      `json:"message"`
	Data    interface{} `json:"data"`
}

// Write - 성공 응답 작성 (1파일 1메서드 원칙)
// 역할: 비즈니스 로직 결과 → 표준 JSON 성공 응답 변환
func Write(w http.ResponseWriter, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)

	response := APIResponse{
		Success: true,
		Message: "요청이 성공적으로 처리되었습니다",
		Data:    data,
	}

	json.NewEncoder(w).Encode(response)
}

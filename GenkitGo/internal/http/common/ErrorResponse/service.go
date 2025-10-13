package errorresponse

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

// Write - 에러 응답 작성 (1파일 1메서드 원칙)
// 역할: 에러 정보 → 표준 JSON 에러 응답 변환
func Write(w http.ResponseWriter, statusCode int, message string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(statusCode)

	response := APIResponse{
		Success: false,
		Message: message,
		Data:    nil,
	}

	json.NewEncoder(w).Encode(response)
}

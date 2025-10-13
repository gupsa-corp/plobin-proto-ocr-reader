package createrequest

import (
	"net/http"

	errorresponse "github.com/plobin/genkitgo/internal/http/common/ErrorResponse"
	successresponse "github.com/plobin/genkitgo/internal/http/common/SuccessResponse"
)

// Handle - 요청 생성 핸들러 (1파일 1메서드 원칙)
// Route: POST /api/requests
// 역할: Request 수신 → Service 호출 → Response 반환
func Handle(w http.ResponseWriter, r *http.Request) {
	// TODO: 요청 생성 로직 구현
	// FastAPI의 api/endpoints/requests/request_processing.py 포팅 필요

	req, err := ValidateRequest(r)
	if err != nil {
		errorresponse.Write(w, http.StatusBadRequest, err.Error())
		return
	}

	successresponse.Write(w, map[string]interface{}{
		"message":    "요청 생성 엔드포인트 (구현 예정)",
		"file_path":  req.FilePath,
		"request_id": "temp_request_id",
	})
}

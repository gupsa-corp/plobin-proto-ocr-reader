package deleteblock

import (
	"net/http"

	errorresponse "github.com/plobin/genkitgo/internal/http/common/ErrorResponse"
	successresponse "github.com/plobin/genkitgo/internal/http/common/SuccessResponse"
)

// Handle - 블록 삭제 핸들러 (1파일 1메서드 원칙)
// Route: DELETE /api/blocks/{block_id}
// 역할: Request 수신 → Service 호출 → Response 반환
func Handle(w http.ResponseWriter, r *http.Request) {
	// TODO: 블록 삭제 로직 구현
	// FastAPI의 api/endpoints/blocks.py 포팅 필요

	blockID := r.URL.Query().Get("block_id")
	if blockID == "" {
		errorresponse.Write(w, http.StatusBadRequest, "block_id는 필수입니다")
		return
	}

	successresponse.Write(w, map[string]string{
		"message":  "블록 삭제 엔드포인트 (구현 예정)",
		"block_id": blockID,
	})
}

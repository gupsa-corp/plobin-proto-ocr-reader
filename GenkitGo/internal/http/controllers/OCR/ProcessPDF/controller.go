package processpdf

import (
	"net/http"

	successresponse "github.com/plobin/genkitgo/internal/http/common/SuccessResponse"
)

// Handle - PDF OCR 처리 핸들러 (1파일 1메서드 원칙)
// Route: POST /api/ocr/process-pdf
// 역할: Request 수신 → Service 호출 → Response 반환
func Handle(w http.ResponseWriter, r *http.Request) {
	// TODO: PDF 처리 로직 구현
	// FastAPI의 api/endpoints/process_pdf.py 포팅 필요

	successresponse.Write(w, map[string]string{
		"message": "PDF 처리 엔드포인트 (구현 예정)",
	})
}

package processimage

import (
	"net/http"

	extractblocks "github.com/plobin/genkitgo/internal/services/OCR/ExtractBlocks"
	errorresponse "github.com/plobin/genkitgo/internal/http/common/ErrorResponse"
	successresponse "github.com/plobin/genkitgo/internal/http/common/SuccessResponse"
)

// Handle - 이미지 OCR 처리 핸들러 (1파일 1메서드 원칙)
// Route: POST /api/ocr/process-image
// 역할: Request 수신 → Service 호출 → Response 반환
func Handle(w http.ResponseWriter, r *http.Request) {
	// 1. Request 검증
	req, err := ValidateRequest(r)
	if err != nil {
		errorresponse.Write(w, http.StatusBadRequest, err.Error())
		return
	}

	// 2. Service 호출 (비즈니스 로직 위임)
	service := extractblocks.New()
	result, err := service.Execute(req.ImagePath, req.ConfidenceThreshold, req.MergeBlocks)
	if err != nil {
		errorresponse.Write(w, http.StatusInternalServerError, err.Error())
		return
	}

	// 3. Response 반환
	successresponse.Write(w, result)
}

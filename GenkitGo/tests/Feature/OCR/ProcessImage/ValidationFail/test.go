package validationfail_test

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	processimage "github.com/plobin/genkitgo/internal/http/controllers/OCR/ProcessImage"
)

// Test_필수_필드_누락_시_검증이_실패한다 - 검증 실패 테스트 (1파일 1메서드 원칙)
func Test_필수_필드_누락_시_검증이_실패한다(t *testing.T) {
	// Arrange - image_path 누락
	requestBody := map[string]interface{}{
		"confidence_threshold": 0.5,
	}
	body, _ := json.Marshal(requestBody)

	req := httptest.NewRequest(http.MethodPost, "/api/ocr/process-image", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	// Act
	processimage.Handle(w, req)

	// Assert
	if w.Code != http.StatusBadRequest {
		t.Errorf("예상: 400, 실제: %d", w.Code)
	}

	var response map[string]interface{}
	json.NewDecoder(w.Body).Decode(&response)

	if response["success"] != false {
		t.Errorf("success 필드가 false여야 합니다")
	}

	if response["message"] == "" {
		t.Errorf("에러 메시지가 있어야 합니다")
	}
}

package success_test

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	processimage "github.com/plobin/genkitgo/internal/http/controllers/OCR/ProcessImage"
)

// Test_이미지_OCR_처리가_성공한다 - 성공 케이스 테스트 (1파일 1메서드 원칙)
func Test_이미지_OCR_처리가_성공한다(t *testing.T) {
	// Arrange
	requestBody := map[string]interface{}{
		"image_path":           "test_image.jpg",
		"confidence_threshold": 0.5,
		"merge_blocks":         true,
	}
	body, _ := json.Marshal(requestBody)

	req := httptest.NewRequest(http.MethodPost, "/api/ocr/process-image", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	// Act
	processimage.Handle(w, req)

	// Assert
	if w.Code != http.StatusOK {
		t.Errorf("예상: 200, 실제: %d", w.Code)
	}

	var response map[string]interface{}
	json.NewDecoder(w.Body).Decode(&response)

	if response["success"] != true {
		t.Errorf("success 필드가 true여야 합니다")
	}

	if response["message"] == "" {
		t.Errorf("message 필드가 비어있으면 안 됩니다")
	}
}

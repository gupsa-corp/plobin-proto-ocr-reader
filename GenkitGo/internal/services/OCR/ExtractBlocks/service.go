package extractblocks

import (
	"github.com/plobin/genkitgo/internal/models"
	initializeocr "github.com/plobin/genkitgo/internal/services/OCR/InitializeOCR"
)

// Service - OCR 블록 추출 서비스
type Service struct {
	extractor *initializeocr.DocumentBlockExtractor
}

// New - Service 생성자
func New() *Service {
	return &Service{
		extractor: initializeocr.New(true, "ko"),
	}
}

// Execute - OCR 블록 추출 비즈니스 로직 (1파일 1메서드 원칙)
// 역할: 이미지 → OCR 처리 → 블록 정보 반환
// 금지: HTTP 요청/응답 처리 (Controller 책임)
func (s *Service) Execute(imagePath string, confidenceThreshold float64, mergeBlocks bool) (*models.BlockResult, error) {
	// TODO: 실제 OCR 처리 구현
	// FastAPI의 services/ocr/extraction.py 로직 포팅 필요

	// 임시 구현 (구조 확인용)
	result := &models.BlockResult{
		ImagePath: imagePath,
		Blocks: []models.Block{
			{
				Text:       "샘플 텍스트",
				Confidence: 0.95,
				BBox:       []int{10, 20, 100, 50},
				BlockType:  "text",
			},
		},
		ProcessingTime: 0.5,
	}

	return result, nil
}

package initializeocr

import (
	"fmt"
)

// DocumentBlockExtractor - OCR 엔진 래퍼 (Surya OCR)
type DocumentBlockExtractor struct {
	UseGPU bool
	Lang   string
}

// New - OCR 엔진 초기화 (1파일 1메서드 원칙)
func New(useGPU bool, lang string) *DocumentBlockExtractor {
	fmt.Printf("Surya OCR 초기화 중 (언어: %s, GPU: %v)...\n", lang, useGPU)

	return &DocumentBlockExtractor{
		UseGPU: useGPU,
		Lang:   lang,
	}
}

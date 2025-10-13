#!/usr/bin/env python3
"""
Test simple OCR extraction
"""

from paddleocr import PaddleOCR
from services.ocr.simple_extraction import extract_text_simple, visualize_with_pil

# PaddleOCR 초기화 (간단하게!)
print("PaddleOCR 초기화 중...")
ocr = PaddleOCR(use_angle_cls=True, lang='korean')

# 테스트 이미지
image_path = 'test_korean_receipt.png'

# 간단한 OCR 추출
print("\n=== 간단한 OCR 추출 ===")
result = extract_text_simple(ocr, image_path, confidence_threshold=0.3)

# 결과 출력
print(f"\n총 {len(result['blocks'])}개 블록:")
for block in result['blocks']:
    print(f"  [{block['id']}] {block['text']} (신뢰도: {block['confidence']:.3f})")

# PIL 시각화
print("\n=== PIL 시각화 생성 ===")
output_path = 'test_simple_visualization.png'
visualize_with_pil(image_path, result, save_path=output_path)

print(f"\n✅ 완료! 결과: {output_path}")

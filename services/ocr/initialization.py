#!/usr/bin/env python3
"""
OCR initialization service
"""

from paddleocr import PaddleOCR


def initialize_ocr(use_gpu: bool = True, lang: str = 'korean'):
    """
    PaddleOCR 초기화

    Args:
        use_gpu: GPU 사용 여부 (RTX 3090 활용)
        lang: 인식 언어 ('korean', 'en', 'ch' 등)

    Returns:
        초기화된 PaddleOCR 인스턴스
    """
    try:
        # 먼저 기본 설정으로 시도
        ocr = PaddleOCR(lang=lang)
        print(f"PaddleOCR 초기화 완료 - 언어: {lang}")

        # GPU 사용 여부는 PaddlePaddle 환경에 따라 자동 결정됨
        if use_gpu:
            print("GPU 가속 활성화 시도 (PaddlePaddle 환경에 따라 자동 결정)")
        else:
            print("CPU 모드로 실행")

        return ocr

    except Exception as e:
        print(f"PaddleOCR 초기화 실패: {e}")
        # 영어로 폴백 시도
        try:
            print("영어 모드로 재시도...")
            ocr = PaddleOCR(lang='en')
            print("영어 모드로 PaddleOCR 초기화 완료")
            return ocr
        except Exception as e2:
            print(f"영어 모드 초기화도 실패: {e2}")
            raise e


__all__ = ['initialize_ocr']
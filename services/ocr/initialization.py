#!/usr/bin/env python3
"""
OCR initialization service
"""

from paddleocr import PaddleOCR


def initialize_ocr(use_gpu: bool = True, lang: str = 'korean', enable_layout_analysis: bool = True):
    """
    PaddleOCR 초기화 (표 인식 및 레이아웃 분석 기능 포함)

    Args:
        use_gpu: GPU 사용 여부 (RTX 3090 활용)
        lang: 인식 언어 ('korean', 'en', 'ch' 등)
        enable_layout_analysis: 레이아웃 분석 및 표 인식 활성화

    Returns:
        초기화된 PaddleOCR 인스턴스
    """
    try:
        # 고급 설정으로 초기화 (표 인식 및 레이아웃 분석 포함)
        if enable_layout_analysis:
            ocr = PaddleOCR(
                lang=lang,
                use_angle_cls=True,    # 텍스트 방향 분류 활성화
                show_log=False         # 로그 출력 최소화
            )
            print(f"PaddleOCR 초기화 완료 - 언어: {lang}, 레이아웃 분석: 활성화")
        else:
            # 기본 설정
            ocr = PaddleOCR(lang=lang, show_log=False)
            print(f"PaddleOCR 초기화 완료 - 언어: {lang}, 기본 모드")

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
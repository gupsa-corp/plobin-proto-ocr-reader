#!/usr/bin/env python3
"""
OCR initialization service - Surya OCR
"""

from typing import Tuple, Optional
import os


def initialize_ocr(use_gpu: bool = True, lang: str = 'ko', enable_layout_analysis: bool = True,
                   use_korean_optimized: bool = False, **kwargs):
    """
    Surya OCR 초기화

    Args:
        use_gpu: GPU 사용 여부 (자동 감지, CUDA 사용 가능 시 GPU 자동 사용)
        lang: 인식 언어 ('ko', 'en', 'ja' 등 - Surya는 90+ 언어 지원)
        enable_layout_analysis: 레이아웃 분석 활성화 (Surya 내장 기능)
        use_korean_optimized: 한글 최적화 (Surya는 기본적으로 다국어 최적화됨)
        **kwargs: 추가 설정 (호환성 유지)

    Returns:
        (detection_predictor, recognition_predictor) 튜플
    """
    try:
        from surya.detection import DetectionPredictor
        from surya.recognition import RecognitionPredictor

        print(f"Surya OCR 초기화 중... (언어: {lang})")

        # GPU 설정
        if use_gpu:
            # Surya는 torch를 사용하므로 CUDA 자동 감지
            import torch
            if torch.cuda.is_available():
                print("✅ GPU(CUDA) 감지됨 - GPU 가속 활성화")
                os.environ.setdefault('TORCH_DEVICE', 'cuda')
            else:
                print("⚠️ CUDA 사용 불가 - CPU 모드로 실행")
                os.environ.setdefault('TORCH_DEVICE', 'cpu')
        else:
            print("CPU 모드로 실행")
            os.environ['TORCH_DEVICE'] = 'cpu'

        # Detection Predictor 초기화
        print("텍스트 감지 모델 로드 중...")
        det_predictor = DetectionPredictor()

        # Foundation Predictor 초기화 (Recognition에 필요)
        print("Foundation 모델 로드 중...")
        from surya.recognition import FoundationPredictor
        foundation_predictor = FoundationPredictor()

        # Recognition Predictor 초기화
        print("텍스트 인식 모델 로드 중...")
        rec_predictor = RecognitionPredictor(foundation_predictor)

        print(f"✅ Surya OCR 초기화 완료 (언어: {lang})")

        return det_predictor, rec_predictor

    except ImportError as e:
        print(f"❌ Surya OCR 패키지를 찾을 수 없습니다: {e}")
        print("다음 명령어로 설치하세요: pip install surya-ocr")
        raise

    except Exception as e:
        print(f"❌ Surya OCR 초기화 실패: {e}")
        raise


def get_supported_languages():
    """
    Surya OCR이 지원하는 언어 목록 반환

    Returns:
        지원 언어 리스트
    """
    try:
        from surya.languages import CODE_TO_LANGUAGE
        return list(CODE_TO_LANGUAGE.keys())
    except ImportError:
        # Fallback: 주요 언어만 반환
        return ['ko', 'en', 'ja', 'zh', 'es', 'fr', 'de', 'ru', 'ar', 'hi']


__all__ = ['initialize_ocr', 'get_supported_languages']

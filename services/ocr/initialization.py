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
        # 최적화된 설정으로 초기화 (RTX 3090 최적화)
        if enable_layout_analysis:
            ocr = PaddleOCR(
                lang=lang,
                use_angle_cls=True,         # 텍스트 방향 분류 활성화
                show_log=False,             # 로그 출력 최소화
                # 성능 최적화 설정
                det_limit_side_len=1600,    # 감지 이미지 크기 최적화 (기본 960 → 1600)
                rec_batch_num=8,            # 배치 크기 증가 (기본 6 → 8)
                max_batch_size=12,          # 최대 배치 크기 증가 (기본 10 → 12)
                # 정확도 향상 설정
                det_db_thresh=0.2,          # 텍스트 감지 임계값 낮춤 (기본 0.3 → 0.2)
                det_db_box_thresh=0.5,      # 박스 신뢰도 임계값 낮춤 (기본 0.6 → 0.5)
                rec_image_shape='3, 48, 320', # 인식 이미지 크기 최적화
                # GPU 메모리 효율성
                ir_optim=True,              # 추론 최적화 활성화
                use_tensorrt=False,         # TensorRT 비활성화 (호환성)
                gpu_mem=8000,              # GPU 메모리 제한 (8GB, RTX 3090 고려)
                cpu_threads=8              # CPU 스레드 수 최적화
            )
            print(f"PaddleOCR 최적화 초기화 완료 - 언어: {lang}, GPU 메모리: 8GB 제한")
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
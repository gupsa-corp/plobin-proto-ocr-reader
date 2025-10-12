#!/usr/bin/env python3
"""
OCR initialization service
"""

from paddleocr import PaddleOCR


def initialize_ocr(use_gpu: bool = True, lang: str = 'en', enable_layout_analysis: bool = True,
                   use_korean_optimized: bool = False, use_ppocrv5: bool = False, use_tensorrt: bool = False):
    """
    PaddleOCR 초기화 (한글 정확도 최적화 포함)

    Args:
        use_gpu: GPU 사용 여부 (RTX 3090 활용)
        lang: 인식 언어 ('korean', 'en', 'ch' 등)
        enable_layout_analysis: 레이아웃 분석 및 표 인식 활성화
        use_korean_optimized: 한글 최적화 설정 사용 여부
        use_ppocrv5: PP-OCRv5 모델 사용 여부 (최신 버전)
        use_tensorrt: TensorRT 가속화 사용 여부 (최고 성능)

    Returns:
        초기화된 PaddleOCR 인스턴스
    """
    try:
        # TensorRT 가속화 우선 시도
        if use_tensorrt and use_gpu:
            try:
                from .tensorrt_acceleration import initialize_with_tensorrt
                result = initialize_with_tensorrt(lang, enable_layout_analysis)
                if result:
                    return result
                else:
                    print("⚠️ TensorRT 초기화 실패. 일반 모드로 폴백...")
            except ImportError:
                print("⚠️ TensorRT 모듈을 찾을 수 없습니다. 일반 모드로 폴백...")
            except Exception as e:
                print(f"⚠️ TensorRT 초기화 실패: {e}. 일반 모드로 폴백...")

        # PP-OCRv5 사용 시 새로운 초기화 시스템 사용
        if use_ppocrv5 and lang == 'korean':
            try:
                from .ppocrv5_initialization import initialize_ppocrv5_korean
                return initialize_ppocrv5_korean(use_gpu, enable_layout_analysis)
            except ImportError:
                print("⚠️ PP-OCRv5 모듈을 찾을 수 없습니다. PP-OCRv3으로 폴백...")
            except Exception as e:
                print(f"⚠️ PP-OCRv5 초기화 실패: {e}. PP-OCRv3으로 폴백...")

        # 한글 최적화 설정 (PP-OCRv3)
        if lang == 'korean' and use_korean_optimized:
            print("한글 최적화 모드로 PaddleOCR 초기화 중...")

            # 한글 전용 모델 설정 시도 (고품질 설정)
            try:
                ocr = PaddleOCR(
                    # 한글 전용 모델 사용 (PP-OCRv3)
                    lang='korean',             # 명시적으로 korean 지정
                    use_angle_cls=True,        # 텍스트 방향 분류 활성화
                    use_gpu=use_gpu,           # GPU 명시적 지정

                    # 한글 고품질 감지 설정 (매우 낮은 임계값으로 모든 텍스트 감지)
                    det_limit_side_len=4096,   # 고해상도 이미지 지원 (최대)
                    det_db_thresh=0.1,         # 텍스트 감지 임계값 (매우 낮춤 - 더 많이 감지)
                    det_db_box_thresh=0.3,     # 박스 신뢰도 임계값 (낮춤)
                    det_db_unclip_ratio=2.0,   # 박스 확장 증가

                    # 인식 품질 설정
                    rec_batch_num=6,           # 배치 크기
                    drop_score=0.3,            # 낮은 신뢰도 결과 제거 (낮춰서 더 많이 감지)

                    # 고품질 처리
                    use_dilation=True,         # 텍스트 영역 확장
                    det_db_score_mode='fast'   # 빠른 스코어 모드
                )
                print("✅ 한글 최적화 PaddleOCR 초기화 완료")
                return ocr

            except Exception as e:
                print(f"⚠️ 한글 최적화 모델 로드 실패: {e}")
                print("기본 한글 모델로 폴백...")

        # 기본 설정으로 초기화
        if enable_layout_analysis:
            ocr = PaddleOCR(
                lang=lang,
                use_angle_cls=True,        # 텍스트 방향 분류 활성화
                det_limit_side_len=1600,   # 고해상도 이미지 지원
                rec_batch_num=8,           # 배치 크기
                det_db_thresh=0.2,         # 텍스트 감지 임계값
                det_db_box_thresh=0.5      # 박스 신뢰도 임계값
            )
            print(f"PaddleOCR 최적화 초기화 완료 - 언어: {lang}")
        else:
            # 기본 설정
            ocr = PaddleOCR(lang=lang)
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
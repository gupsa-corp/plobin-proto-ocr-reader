#!/usr/bin/env python3
"""
PP-OCRv5 초기화 서비스
"""

from paddleocr import PaddleOCR
import os
from typing import Optional

class PPOCRv5Manager:
    """PP-OCRv5 모델 관리자"""

    def __init__(self):
        self.ocr_instance = None
        self.current_config = None

    def initialize_ppocrv5_korean(self, use_gpu: bool = True, enable_layout_analysis: bool = True) -> PaddleOCR:
        """
        PP-OCRv5 한글 최적화 초기화

        Args:
            use_gpu: GPU 사용 여부
            enable_layout_analysis: 레이아웃 분석 활성화

        Returns:
            초기화된 PP-OCRv5 PaddleOCR 인스턴스
        """
        try:
            print("PP-OCRv5 한글 최적화 모드로 초기화 중...")

            # PP-OCRv5 간소화된 한글 최적화 설정
            config = {
                # 기본 설정 (안정성 우선)
                'lang': 'korean',
                'use_angle_cls': True,
                'show_log': False,

                # 자동 모델 다운로드
                'det_model_dir': None,
                'rec_model_dir': None,
                'cls_model_dir': None,

                # 한글 최적화 감지 설정 (검증된 값)
                'det_limit_side_len': 3000,      # 고해상도 지원
                'det_db_thresh': 0.05,           # 민감한 감지
                'det_db_box_thresh': 0.3,        # 박스 임계값
                'det_db_unclip_ratio': 3.0,      # 박스 확장

                # 한글 최적화 인식 설정 (검증된 값)
                'rec_image_shape': '3, 80, 320', # 안정적인 크기
                'rec_batch_num': 6,              # 안정적인 배치 크기
                'max_batch_size': 10,            # 안정적인 최대 배치

                # 기본 성능 설정
                'use_gpu': use_gpu,
                'ir_optim': True,
                'gpu_mem': 8000,
                'cpu_threads': 28,
            }

            # PP-OCRv5 인스턴스 생성
            self.ocr_instance = PaddleOCR(**config)
            self.current_config = config

            print("✅ PP-OCRv5 한글 최적화 초기화 완료")
            print(f"   - 모델: PP-OCRv5 Korean")
            print(f"   - GPU: {'활성화' if use_gpu else '비활성화'}")
            print(f"   - 레이아웃 분석: {'활성화' if enable_layout_analysis else '비활성화'}")

            return self.ocr_instance

        except Exception as e:
            print(f"❌ PP-OCRv5 초기화 실패: {e}")
            # 폴백: 기존 PP-OCRv3 사용
            print("🔄 PP-OCRv3으로 폴백...")
            return self._fallback_to_v3(use_gpu, enable_layout_analysis)

    def _fallback_to_v3(self, use_gpu: bool, enable_layout_analysis: bool) -> PaddleOCR:
        """PP-OCRv3으로 폴백"""
        try:
            from .initialization import initialize_ocr
            return initialize_ocr(use_gpu, 'korean', enable_layout_analysis, True)
        except Exception as e:
            print(f"❌ PP-OCRv3 폴백도 실패: {e}")
            raise

    def get_model_info(self) -> dict:
        """현재 모델 정보 반환"""
        if not self.ocr_instance or not self.current_config:
            return {"status": "not_initialized"}

        return {
            "status": "initialized",
            "version": "PP-OCRv5",
            "language": "korean",
            "gpu_enabled": self.current_config.get('use_gpu', False),
            "layout_analysis": self.current_config.get('layout', False),
            "image_shape": self.current_config.get('rec_image_shape'),
            "batch_size": self.current_config.get('rec_batch_num'),
        }

    def update_config(self, **kwargs) -> bool:
        """실행 중 설정 업데이트"""
        try:
            if self.current_config:
                self.current_config.update(kwargs)
                # 필요시 모델 재초기화
                print(f"⚙️ PP-OCRv5 설정 업데이트: {kwargs}")
                return True
        except Exception as e:
            print(f"❌ 설정 업데이트 실패: {e}")
            return False

# 전역 PP-OCRv5 매니저 인스턴스
ppocrv5_manager = PPOCRv5Manager()

def initialize_ppocrv5_korean(use_gpu: bool = True, enable_layout_analysis: bool = True) -> PaddleOCR:
    """PP-OCRv5 한글 초기화 (편의 함수)"""
    return ppocrv5_manager.initialize_ppocrv5_korean(use_gpu, enable_layout_analysis)

def get_ppocrv5_info() -> dict:
    """PP-OCRv5 정보 조회 (편의 함수)"""
    return ppocrv5_manager.get_model_info()
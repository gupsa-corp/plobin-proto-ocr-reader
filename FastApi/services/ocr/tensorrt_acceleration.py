#!/usr/bin/env python3
"""
TensorRT 가속화 서비스
"""

import os
import subprocess
from paddleocr import PaddleOCR
from typing import Optional, Dict

class TensorRTManager:
    """TensorRT 가속화 관리자"""

    def __init__(self):
        self.tensorrt_available = self._check_tensorrt_availability()
        self.ocr_instance = None
        self.current_config = None

    def _check_tensorrt_availability(self) -> bool:
        """TensorRT 사용 가능 여부 확인"""
        try:
            # NVIDIA GPU 확인
            result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
            if result.returncode != 0:
                print("❌ NVIDIA GPU를 찾을 수 없습니다")
                return False

            # TensorRT 라이브러리 확인
            try:
                import tensorrt
                print(f"✅ TensorRT {tensorrt.__version__} 감지됨")
                return True
            except ImportError:
                print("⚠️ TensorRT 라이브러리가 설치되지 않았습니다")
                return False

        except Exception as e:
            print(f"⚠️ TensorRT 확인 중 오류: {e}")
            return False

    def initialize_with_tensorrt(self, lang: str = 'korean',
                                enable_layout_analysis: bool = True) -> Optional[PaddleOCR]:
        """
        TensorRT 가속화가 활성화된 PaddleOCR 초기화

        Args:
            lang: 인식 언어
            enable_layout_analysis: 레이아웃 분석 활성화

        Returns:
            TensorRT 가속 PaddleOCR 인스턴스 또는 None
        """
        if not self.tensorrt_available:
            print("❌ TensorRT를 사용할 수 없습니다")
            return None

        try:
            print("🚀 TensorRT 가속화 PaddleOCR 초기화 중...")

            # TensorRT 최적화 설정
            config = {
                # 기본 설정
                'lang': lang,
                'use_angle_cls': True,
                'show_log': False,

                # TensorRT 가속화 설정
                'use_gpu': True,                 # GPU 필수
                'use_tensorrt': True,            # TensorRT 활성화 (핵심!)
                'precision': 'fp16',             # FP16 정밀도 (속도 향상)
                'gpu_mem': 8000,                 # GPU 메모리 할당

                # 고성능 설정
                'det_limit_side_len': 3000,      # 고해상도 지원
                'det_db_thresh': 0.05,           # 민감한 감지
                'det_db_box_thresh': 0.3,        # 박스 임계값
                'det_db_unclip_ratio': 3.0,      # 박스 확장

                # 인식 최적화
                'rec_image_shape': '3, 80, 320', # 최적화된 크기
                'rec_batch_num': 16,             # TensorRT에서 대량 배치 처리
                'max_batch_size': 32,            # 최대 배치 크기 증가

                # TensorRT 특화 최적화
                'ir_optim': True,                # 추론 최적화
                'enable_mkldnn': False,          # GPU 모드에서는 비활성화
                'cpu_threads': 1,                # GPU 모드에서는 최소화

                # 캐싱 및 워밍업
                'warmup': True,                  # 모델 워밍업
                'benchmark': True,               # 벤치마크 모드
            }

            # 레이아웃 분석 추가 설정
            if enable_layout_analysis:
                config.update({
                    'layout': True,
                    'table': True,
                    'ocr': True,
                })

            # TensorRT PaddleOCR 인스턴스 생성
            self.ocr_instance = PaddleOCR(**config)
            self.current_config = config

            print("✅ TensorRT 가속화 PaddleOCR 초기화 완료")
            print(f"   - 언어: {lang}")
            print(f"   - 정밀도: FP16")
            print(f"   - 배치 크기: {config['rec_batch_num']}")
            print(f"   - GPU 메모리: {config['gpu_mem']}MB")

            return self.ocr_instance

        except Exception as e:
            print(f"❌ TensorRT 초기화 실패: {e}")
            print("🔄 일반 GPU 모드로 폴백...")
            return self._fallback_to_gpu_mode(lang, enable_layout_analysis)

    def _fallback_to_gpu_mode(self, lang: str, enable_layout_analysis: bool) -> Optional[PaddleOCR]:
        """TensorRT 실패 시 일반 GPU 모드로 폴백"""
        try:
            from .initialization import initialize_ocr
            return initialize_ocr(use_gpu=True, lang=lang,
                                enable_layout_analysis=enable_layout_analysis,
                                use_korean_optimized=True)
        except Exception as e:
            print(f"❌ GPU 폴백도 실패: {e}")
            return None

    def get_acceleration_info(self) -> Dict:
        """TensorRT 가속화 정보 반환"""
        return {
            "tensorrt_available": self.tensorrt_available,
            "status": "initialized" if self.ocr_instance else "not_initialized",
            "config": self.current_config,
            "performance_mode": "tensorrt" if self.tensorrt_available and self.ocr_instance else "standard"
        }

    def benchmark_performance(self, test_image_path: str, iterations: int = 5) -> Dict:
        """성능 벤치마크 실행"""
        if not self.ocr_instance:
            return {"error": "OCR 인스턴스가 초기화되지 않았습니다"}

        import time

        print(f"🏃‍♂️ TensorRT 성능 벤치마크 시작 ({iterations}회)")

        times = []
        for i in range(iterations):
            start_time = time.time()
            result = self.ocr_instance.ocr(test_image_path)
            end_time = time.time()

            processing_time = end_time - start_time
            times.append(processing_time)
            print(f"   반복 {i+1}: {processing_time:.3f}초")

        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)

        print(f"📊 벤치마크 결과:")
        print(f"   - 평균: {avg_time:.3f}초")
        print(f"   - 최고: {min_time:.3f}초")
        print(f"   - 최저: {max_time:.3f}초")

        return {
            "iterations": iterations,
            "times": times,
            "average_time": avg_time,
            "min_time": min_time,
            "max_time": max_time,
            "acceleration_enabled": self.tensorrt_available
        }

    def enable_tensorrt_optimization(self) -> bool:
        """TensorRT 최적화 활성화"""
        if not self.tensorrt_available:
            print("❌ TensorRT를 사용할 수 없습니다")
            return False

        try:
            # 환경 변수 설정
            os.environ['CUDA_VISIBLE_DEVICES'] = '0'  # 첫 번째 GPU 사용
            os.environ['TRT_LOGGER_LEVEL'] = 'WARNING'  # TensorRT 로그 레벨

            print("✅ TensorRT 환경 최적화 완료")
            return True

        except Exception as e:
            print(f"❌ TensorRT 최적화 실패: {e}")
            return False

# 전역 TensorRT 매니저 인스턴스
tensorrt_manager = TensorRTManager()

def initialize_with_tensorrt(lang: str = 'korean', enable_layout_analysis: bool = True) -> Optional[PaddleOCR]:
    """TensorRT 가속화 초기화 (편의 함수)"""
    return tensorrt_manager.initialize_with_tensorrt(lang, enable_layout_analysis)

def get_tensorrt_info() -> Dict:
    """TensorRT 정보 조회 (편의 함수)"""
    return tensorrt_manager.get_acceleration_info()

def benchmark_tensorrt(test_image_path: str, iterations: int = 5) -> Dict:
    """TensorRT 벤치마크 (편의 함수)"""
    return tensorrt_manager.benchmark_performance(test_image_path, iterations)
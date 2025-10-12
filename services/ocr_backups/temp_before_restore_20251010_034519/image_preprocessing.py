#!/usr/bin/env python3
"""
한글 OCR 정확도 향상을 위한 이미지 전처리 모듈
"""

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import tempfile
import os


class KoreanImagePreprocessor:
    """한글 텍스트 인식을 위한 이미지 전처리기"""

    def __init__(self):
        self.temp_files = []

    def preprocess_for_korean_ocr(self, image_path: str, enhancement_level: str = 'medium') -> str:
        """
        한글 OCR을 위한 종합적인 이미지 전처리

        Args:
            image_path: 원본 이미지 경로
            enhancement_level: 강화 수준 ('light', 'medium', 'strong')

        Returns:
            전처리된 이미지의 임시 파일 경로
        """
        try:
            # 이미지 로드
            if isinstance(image_path, str):
                image = cv2.imread(image_path)
            else:
                image = image_path

            if image is None:
                raise ValueError(f"이미지를 로드할 수 없습니다: {image_path}")

            # 전처리 파이프라인 실행
            processed_image = self._apply_preprocessing_pipeline(image, enhancement_level)

            # 임시 파일로 저장
            temp_path = self._save_temp_image(processed_image)
            return temp_path

        except Exception as e:
            print(f"이미지 전처리 실패: {e}")
            return image_path  # 원본 반환

    def _apply_preprocessing_pipeline(self, image: np.ndarray, level: str) -> np.ndarray:
        """전처리 파이프라인 적용"""

        # 1. 해상도 향상 (업스케일링)
        image = self._upscale_image(image, level)

        # 2. 노이즈 제거
        image = self._denoise_image(image, level)

        # 3. 선명도 향상
        image = self._enhance_sharpness(image, level)

        # 4. 대비 개선
        image = self._enhance_contrast(image, level)

        # 5. 이진화 (한글 텍스트에 최적화)
        image = self._adaptive_binarization(image, level)

        # 6. 모폴로지 연산 (한글 특성 고려)
        image = self._morphological_operations(image, level)

        return image

    def _upscale_image(self, image: np.ndarray, level: str) -> np.ndarray:
        """해상도 향상"""
        scale_factors = {
            'light': 1.2,
            'medium': 1.5,
            'strong': 2.0
        }

        scale = scale_factors.get(level, 1.5)
        height, width = image.shape[:2]
        new_width = int(width * scale)
        new_height = int(height * scale)

        # 고품질 보간법 사용
        return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)

    def _denoise_image(self, image: np.ndarray, level: str) -> np.ndarray:
        """노이즈 제거"""
        denoise_strengths = {
            'light': 3,
            'medium': 5,
            'strong': 7
        }

        strength = denoise_strengths.get(level, 5)

        # Non-local means denoising (컬러 이미지용)
        if len(image.shape) == 3:
            return cv2.fastNlMeansDenoisingColored(image, None, strength, strength, 7, 21)
        else:
            return cv2.fastNlMeansDenoising(image, None, strength, 7, 21)

    def _enhance_sharpness(self, image: np.ndarray, level: str) -> np.ndarray:
        """선명도 향상"""
        # OpenCV를 PIL로 변환
        if len(image.shape) == 3:
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        else:
            pil_image = Image.fromarray(image)

        # 선명도 향상
        sharpness_factors = {
            'light': 1.2,
            'medium': 1.5,
            'strong': 2.0
        }

        factor = sharpness_factors.get(level, 1.5)
        enhancer = ImageEnhance.Sharpness(pil_image)
        enhanced = enhancer.enhance(factor)

        # 추가적인 언샤프 마스킹
        enhanced = enhanced.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))

        # 다시 OpenCV 형식으로 변환
        if len(image.shape) == 3:
            return cv2.cvtColor(np.array(enhanced), cv2.COLOR_RGB2BGR)
        else:
            return np.array(enhanced)

    def _enhance_contrast(self, image: np.ndarray, level: str) -> np.ndarray:
        """대비 개선"""
        # CLAHE (Contrast Limited Adaptive Histogram Equalization) 적용
        contrast_factors = {
            'light': 2.0,
            'medium': 3.0,
            'strong': 4.0
        }

        clip_limit = contrast_factors.get(level, 3.0)

        if len(image.shape) == 3:
            # 컬러 이미지의 경우 LAB 색공간에서 L 채널에만 적용
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
            lab[:, :, 0] = clahe.apply(lab[:, :, 0])
            return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        else:
            # 그레이스케일 이미지
            clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
            return clahe.apply(image)

    def _adaptive_binarization(self, image: np.ndarray, level: str) -> np.ndarray:
        """적응적 이진화 (한글 텍스트 최적화)"""
        # 그레이스케일 변환
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # 적응적 임계값 설정
        block_sizes = {
            'light': 11,
            'medium': 15,
            'strong': 19
        }

        block_size = block_sizes.get(level, 15)

        # 적응적 이진화 (한글 텍스트에 최적화)
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, block_size, 2
        )

        # Otsu 이진화도 시도해보고 더 좋은 결과 선택
        _, otsu_binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # 두 결과의 품질 비교 (텍스트 영역 비율 기준)
        adaptive_text_ratio = np.sum(binary == 0) / binary.size
        otsu_text_ratio = np.sum(otsu_binary == 0) / otsu_binary.size

        # 적정 텍스트 비율 범위 내의 결과 선택
        if 0.1 <= adaptive_text_ratio <= 0.7:
            return binary
        elif 0.1 <= otsu_text_ratio <= 0.7:
            return otsu_binary
        else:
            return binary  # 기본값

    def _morphological_operations(self, image: np.ndarray, level: str) -> np.ndarray:
        """모폴로지 연산 (한글 문자 특성 고려)"""
        if len(image.shape) == 3:
            # 이미 컬러라면 그대로 반환
            return image

        # 한글 문자 연결 및 노이즈 제거를 위한 커널
        kernel_sizes = {
            'light': (2, 2),
            'medium': (3, 3),
            'strong': (4, 4)
        }

        kernel_size = kernel_sizes.get(level, (3, 3))
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, kernel_size)

        # 노이즈 제거를 위한 열림 연산
        opened = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel, iterations=1)

        # 문자 연결을 위한 닫힘 연산
        closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel, iterations=1)

        return closed

    def _save_temp_image(self, image: np.ndarray) -> str:
        """전처리된 이미지를 임시 파일로 저장"""
        temp_fd, temp_path = tempfile.mkstemp(suffix='.png')
        try:
            cv2.imwrite(temp_path, image)
            self.temp_files.append(temp_path)
            return temp_path
        finally:
            os.close(temp_fd)

    def cleanup_temp_files(self):
        """임시 파일들 정리"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception:
                pass
        self.temp_files.clear()

    def __del__(self):
        """소멸자에서 임시 파일 정리"""
        self.cleanup_temp_files()


def preprocess_image_for_korean_ocr(image_path: str, enhancement_level: str = 'medium') -> str:
    """
    한글 OCR을 위한 이미지 전처리 (편의 함수)

    Args:
        image_path: 원본 이미지 경로
        enhancement_level: 강화 수준 ('light', 'medium', 'strong')

    Returns:
        전처리된 이미지의 임시 파일 경로
    """
    preprocessor = KoreanImagePreprocessor()
    return preprocessor.preprocess_for_korean_ocr(image_path, enhancement_level)


__all__ = ['KoreanImagePreprocessor', 'preprocess_image_for_korean_ocr']
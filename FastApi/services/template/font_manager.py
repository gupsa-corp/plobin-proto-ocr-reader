"""
Font management for Korean text rendering in templates.
"""

import os
import logging
from pathlib import Path
from PIL import ImageFont
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class FontManager:
    """한글 폰트 관리 클래스"""

    def __init__(self):
        self.korean_fonts = [
            # Noto CJK 폰트들 (가장 좋은 한글 지원)
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
            "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc",

            # 대안 한글 폰트들
            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
            "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
            "/usr/share/fonts/truetype/nanum/NanumMyeongjo.ttf",
            "/usr/share/fonts/truetype/nanum/NanumMyeongjoBold.ttf",

            # 시스템 기본 폰트들
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]

        self.fallback_fonts = [
            "/System/Library/Fonts/Arial.ttf",  # macOS
            "/Windows/Fonts/arial.ttf",        # Windows
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
        ]

        # 사용 가능한 폰트 캐시
        self._font_cache = {}

    def get_korean_font(self, size: int = 12, bold: bool = False) -> ImageFont.FreeTypeFont:
        """
        한글 지원 폰트 가져오기

        Args:
            size: 폰트 크기
            bold: 굵은 글씨 여부

        Returns:
            PIL ImageFont 객체
        """
        cache_key = f"{size}_{bold}"

        if cache_key in self._font_cache:
            return self._font_cache[cache_key]

        # 한글 폰트 우선 시도
        for font_path in self.korean_fonts:
            if bold and ('Bold' not in font_path and 'bold' not in font_path.lower()):
                continue
            if not bold and ('Bold' in font_path or 'bold' in font_path.lower()):
                continue

            try:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, size)
                    # 한글 텍스트로 폰트 테스트
                    test_text = "한글테스트"
                    try:
                        font.getbbox(test_text)
                        logger.info(f"Korean font loaded: {font_path} (size: {size})")
                        self._font_cache[cache_key] = font
                        return font
                    except Exception:
                        continue
            except Exception as e:
                logger.debug(f"Failed to load font {font_path}: {e}")
                continue

        # 대안 폰트 시도
        for font_path in self.fallback_fonts:
            try:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, size)
                    logger.warning(f"Using fallback font: {font_path} (Korean support may be limited)")
                    self._font_cache[cache_key] = font
                    return font
            except Exception as e:
                logger.debug(f"Failed to load fallback font {font_path}: {e}")
                continue

        # 최후 수단: 기본 폰트
        logger.warning("No suitable font found, using default font (Korean may not display correctly)")
        font = ImageFont.load_default()
        self._font_cache[cache_key] = font
        return font

    def get_font_pair(self, regular_size: int = 12, title_size: int = 16) -> Tuple[ImageFont.FreeTypeFont, ImageFont.FreeTypeFont]:
        """
        일반 폰트와 제목 폰트 쌍 가져오기

        Args:
            regular_size: 일반 텍스트 크기
            title_size: 제목 텍스트 크기

        Returns:
            (일반폰트, 제목폰트) 튜플
        """
        regular_font = self.get_korean_font(regular_size, bold=False)
        title_font = self.get_korean_font(title_size, bold=True)

        return regular_font, title_font

    def test_korean_rendering(self, font: ImageFont.FreeTypeFont, test_text: str = "한글 테스트 텍스트") -> bool:
        """
        폰트의 한글 렌더링 테스트

        Args:
            font: 테스트할 폰트
            test_text: 테스트 텍스트

        Returns:
            한글 렌더링 가능 여부
        """
        try:
            # getbbox가 성공하면 해당 폰트가 텍스트를 렌더링할 수 있음
            bbox = font.getbbox(test_text)
            return bbox[2] > bbox[0] and bbox[3] > bbox[1]  # 너비와 높이가 0보다 큰지 확인
        except Exception as e:
            logger.debug(f"Korean rendering test failed: {e}")
            return False

    def list_available_fonts(self) -> dict:
        """
        사용 가능한 폰트 목록 반환

        Returns:
            폰트 타입별 사용 가능한 폰트 경로들
        """
        available = {
            'korean_fonts': [],
            'fallback_fonts': [],
            'system_default': True
        }

        # 한글 폰트 확인
        for font_path in self.korean_fonts:
            if os.path.exists(font_path):
                try:
                    font = ImageFont.truetype(font_path, 12)
                    if self.test_korean_rendering(font):
                        available['korean_fonts'].append(font_path)
                except Exception:
                    pass

        # 대안 폰트 확인
        for font_path in self.fallback_fonts:
            if os.path.exists(font_path):
                try:
                    ImageFont.truetype(font_path, 12)
                    available['fallback_fonts'].append(font_path)
                except Exception:
                    pass

        return available


# 전역 폰트 매니저 인스턴스
font_manager = FontManager()


def get_korean_fonts(regular_size: int = 12, title_size: int = 16) -> Tuple[ImageFont.FreeTypeFont, ImageFont.FreeTypeFont]:
    """
    한글 지원 폰트 쌍 가져오기 (편의 함수)

    Args:
        regular_size: 일반 텍스트 크기
        title_size: 제목 텍스트 크기

    Returns:
        (일반폰트, 제목폰트) 튜플
    """
    return font_manager.get_font_pair(regular_size, title_size)


def test_font_availability():
    """폰트 사용 가능성 테스트 (디버깅용)"""
    available = font_manager.list_available_fonts()

    print("=== Font Availability Test ===")
    print(f"Korean fonts available: {len(available['korean_fonts'])}")
    for font in available['korean_fonts']:
        print(f"  ✓ {font}")

    print(f"Fallback fonts available: {len(available['fallback_fonts'])}")
    for font in available['fallback_fonts']:
        print(f"  ✓ {font}")

    print(f"System default available: {available['system_default']}")

    # 실제 폰트 로드 테스트
    regular_font, title_font = get_korean_fonts()
    print(f"\nSelected fonts:")
    print(f"  Regular: {regular_font}")
    print(f"  Title: {title_font}")

    # 한글 렌더링 테스트
    korean_test = font_manager.test_korean_rendering(regular_font, "한글 테스트")
    print(f"  Korean rendering test: {'✓ PASS' if korean_test else '✗ FAIL'}")


if __name__ == "__main__":
    test_font_availability()
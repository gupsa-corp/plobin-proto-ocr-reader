#!/usr/bin/env python3
"""
Validate image files and formats
"""

import os
from pathlib import Path


def validate_image(image_path, supported_formats=None):
    """
    이미지 파일의 유효성을 검증

    Args:
        image_path: 이미지 파일 경로
        supported_formats: 지원하는 포맷 리스트 (기본값: ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'webp'])

    Returns:
        bool: 유효한 이미지 파일인지 여부

    Raises:
        FileNotFoundError: 파일이 존재하지 않을 때
    """
    if supported_formats is None:
        supported_formats = ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'webp']

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {image_path}")

    # 파일 확장자 확인
    file_extension = Path(image_path).suffix.lower().lstrip('.')

    if file_extension not in supported_formats:
        return False

    # 파일 크기 확인 (0바이트가 아닌지)
    if os.path.getsize(image_path) == 0:
        return False

    return True


__all__ = ['validate_image']
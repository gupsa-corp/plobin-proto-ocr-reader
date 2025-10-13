#!/usr/bin/env python3
"""
Extract metadata and information from images
"""

from pathlib import Path
from .io import read_image


def get_image_info(image_path):
    """
    이미지 파일의 메타데이터 정보 추출

    Args:
        image_path: 이미지 파일 경로

    Returns:
        dict: 이미지 정보가 담긴 딕셔너리
    """
    image = read_image(image_path)
    file_path = Path(image_path)

    height, width = image.shape[:2]
    channels = image.shape[2] if len(image.shape) > 2 else 1

    info = {
        'path': str(image_path),
        'filename': file_path.name,
        'stem': file_path.stem,
        'suffix': file_path.suffix,
        'size_bytes': file_path.stat().st_size,
        'width': width,
        'height': height,
        'channels': channels,
        'total_pixels': width * height,
        'aspect_ratio': width / height if height > 0 else 0,
        'color_space': 'BGR' if channels == 3 else 'Grayscale' if channels == 1 else f'{channels}-channel'
    }

    return info


__all__ = ['get_image_info']
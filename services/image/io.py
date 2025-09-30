#!/usr/bin/env python3
"""
Read and load image files
"""

import cv2
import os


def read_image(image_path):
    """
    이미지 파일을 읽어서 반환

    Args:
        image_path: 이미지 파일 경로

    Returns:
        읽어온 이미지 배열 (BGR 형식)

    Raises:
        FileNotFoundError: 파일이 존재하지 않을 때
        ValueError: 이미지를 읽을 수 없을 때
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")

    image = cv2.imread(image_path)

    if image is None:
        raise ValueError(f"이미지를 읽을 수 없습니다: {image_path}")

    return image


__all__ = ['read_image']
#!/usr/bin/env python3
"""
Extract text blocks from images using OCR
"""

import os
import cv2
import numpy as np
from typing import Dict
from .merging import merge_adjacent_blocks


def extract_blocks(ocr_instance, image_path: str, confidence_threshold: float = 0.5, merge_blocks: bool = True, merge_threshold: int = 30) -> Dict:
    """
    이미지에서 문서 블록 추출

    Args:
        ocr_instance: PaddleOCR 인스턴스
        image_path: 이미지 파일 경로
        confidence_threshold: 신뢰도 임계값
        merge_blocks: 블록 병합 여부
        merge_threshold: 병합 임계값

    Returns:
        블록 정보가 포함된 딕셔너리
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")

    # 이미지 읽기
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"이미지를 읽을 수 없습니다: {image_path}")

    # PaddleOCR 실행
    print("OCR 처리 중...")
    result = ocr_instance.ocr(image_path, cls=True)

    # 결과 파싱
    blocks = []
    if result and result[0]:
        for idx, detection in enumerate(result[0]):
            bbox, (text, confidence) = detection

            # 신뢰도 필터링
            if confidence < confidence_threshold:
                continue

            # 바운딩 박스 좌표 정규화
            bbox = np.array(bbox).astype(int)
            x_min = int(np.min(bbox[:, 0]))
            y_min = int(np.min(bbox[:, 1]))
            x_max = int(np.max(bbox[:, 0]))
            y_max = int(np.max(bbox[:, 1]))

            # 블록 분류 (단순화)
            block_type = 'other'  # Simplified - no complex classification needed

            block_info = {
                'id': idx,
                'text': text,
                'confidence': float(confidence),
                'bbox': {
                    'x_min': x_min,
                    'y_min': y_min,
                    'x_max': x_max,
                    'y_max': y_max,
                    'width': x_max - x_min,
                    'height': y_max - y_min
                },
                'bbox_points': bbox.tolist(),
                'type': block_type,
                'area': (x_max - x_min) * (y_max - y_min)
            }
            blocks.append(block_info)

    # 블록 병합 처리
    if merge_blocks and blocks:
        blocks = merge_adjacent_blocks(blocks, merge_threshold)

    # 이미지 정보
    height, width = image.shape[:2]

    return {
        'image_info': {
            'path': image_path,
            'width': width,
            'height': height,
            'total_blocks': len(blocks)
        },
        'blocks': blocks,
        'processing_info': {
            'confidence_threshold': confidence_threshold,
            'language': 'korean',  # Default language
            'merge_blocks': merge_blocks,
            'merge_threshold': merge_threshold
        }
    }


__all__ = ['extract_blocks']
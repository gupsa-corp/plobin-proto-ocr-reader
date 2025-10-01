#!/usr/bin/env python3
"""
Extract text blocks from images using OCR with enhanced table recognition
"""

import os
import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
from .merging import merge_adjacent_blocks
from .table_recognition import create_table_recognizer


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


def extract_blocks_with_layout_analysis(ocr_instance, image_path: str, confidence_threshold: float = 0.5,
                                        merge_blocks: bool = True, merge_threshold: int = 30,
                                        enable_table_recognition: bool = True) -> Dict:
    """
    레이아웃 분석 및 표 인식을 포함한 향상된 블록 추출

    Args:
        ocr_instance: PaddleOCR 인스턴스
        image_path: 이미지 파일 경로
        confidence_threshold: 신뢰도 임계값
        merge_blocks: 블록 병합 여부
        merge_threshold: 병합 임계값
        enable_table_recognition: 표 인식 활성화 여부

    Returns:
        레이아웃 분석 결과가 포함된 블록 정보 딕셔너리
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")

    # 기본 OCR 블록 추출
    basic_result = extract_blocks(ocr_instance, image_path, confidence_threshold,
                                 merge_blocks, merge_threshold)

    blocks = basic_result['blocks']
    layout_info = {'tables': [], 'layout_elements': {}}

    # 표 인식 수행 (선택적)
    if enable_table_recognition:
        try:
            print("표 인식 및 레이아웃 분석 수행 중...")

            # 표 인식기 생성
            table_recognizer = create_table_recognizer(lang='korean', use_gpu=False)

            # 표 감지
            detected_tables = table_recognizer.detect_tables(image_path)
            layout_analysis = table_recognizer.analyze_layout(image_path)

            # 표 정보 추가
            layout_info['tables'] = detected_tables
            layout_info['layout_elements'] = layout_analysis.get('layout_elements', {})
            layout_info['layout_summary'] = layout_analysis.get('summary', {})

            # 기존 블록들의 타입을 레이아웃 분석 결과로 업데이트
            blocks = _enhance_blocks_with_layout_info(blocks, layout_analysis)

            print(f"표 {len(detected_tables)}개 감지됨")

        except Exception as e:
            print(f"표 인식 중 오류 (기본 OCR로 계속): {e}")

    return {
        'metadata': {
            'image_path': image_path,
            'total_blocks': len(blocks),
            'tables_detected': len(layout_info.get('tables', [])),
            'layout_analysis_enabled': enable_table_recognition
        },
        'blocks': blocks,
        'layout_info': layout_info,
        'processing_info': {
            'confidence_threshold': confidence_threshold,
            'language': 'korean',
            'merge_blocks': merge_blocks,
            'merge_threshold': merge_threshold,
            'table_recognition': enable_table_recognition
        }
    }


def _enhance_blocks_with_layout_info(blocks: List[Dict], layout_analysis: Dict) -> List[Dict]:
    """
    레이아웃 분석 결과를 사용해 블록 타입을 향상

    Args:
        blocks: 기존 블록 리스트
        layout_analysis: 레이아웃 분석 결과

    Returns:
        타입이 향상된 블록 리스트
    """
    try:
        layout_elements = layout_analysis.get('layout_elements', {})

        for block in blocks:
            block_bbox = block.get('bbox', {})
            block_center = (
                (block_bbox.get('x_min', 0) + block_bbox.get('x_max', 0)) / 2,
                (block_bbox.get('y_min', 0) + block_bbox.get('y_max', 0)) / 2
            )

            # 각 레이아웃 요소와 비교하여 타입 결정
            best_match_type = 'other'
            best_overlap = 0

            for element_type, elements in layout_elements.items():
                if element_type == 'tables':
                    element_type_name = 'table'
                elif element_type == 'titles':
                    element_type_name = 'title'
                elif element_type == 'paragraphs':
                    element_type_name = 'paragraph'
                else:
                    element_type_name = 'other'

                for element in elements:
                    element_bbox = element.get('bbox', [])
                    if len(element_bbox) >= 4:
                        # 겹침 정도 계산
                        overlap = _calculate_overlap_ratio(
                            [block_bbox.get('x_min', 0), block_bbox.get('y_min', 0),
                             block_bbox.get('x_max', 0), block_bbox.get('y_max', 0)],
                            element_bbox
                        )

                        if overlap > best_overlap:
                            best_overlap = overlap
                            best_match_type = element_type_name

            # 일정 겹침 비율 이상일 때만 타입 업데이트
            if best_overlap > 0.3:
                block['type'] = best_match_type
                block['layout_confidence'] = best_overlap

    except Exception as e:
        print(f"블록 타입 향상 중 오류: {e}")

    return blocks


def _calculate_overlap_ratio(bbox1: List[float], bbox2: List[float]) -> float:
    """두 바운딩 박스의 겹침 비율 계산"""
    try:
        x1_min, y1_min, x1_max, y1_max = bbox1
        x2_min, y2_min, x2_max, y2_max = bbox2

        # 겹치는 영역 계산
        overlap_x_min = max(x1_min, x2_min)
        overlap_y_min = max(y1_min, y2_min)
        overlap_x_max = min(x1_max, x2_max)
        overlap_y_max = min(y1_max, y2_max)

        if overlap_x_min >= overlap_x_max or overlap_y_min >= overlap_y_max:
            return 0.0

        overlap_area = (overlap_x_max - overlap_x_min) * (overlap_y_max - overlap_y_min)
        bbox1_area = (x1_max - x1_min) * (y1_max - y1_min)

        return overlap_area / bbox1_area if bbox1_area > 0 else 0.0

    except Exception:
        return 0.0


def crop_block_image(image_path: str, bbox: Dict, padding: int = 5) -> np.ndarray:
    """
    이미지에서 특정 블록 영역을 크롭

    Args:
        image_path: 원본 이미지 경로
        bbox: 바운딩 박스 정보 {'x_min', 'y_min', 'x_max', 'y_max'}
        padding: 크롭 시 추가할 패딩 (픽셀)

    Returns:
        크롭된 이미지 (numpy 배열)
    """
    # 이미지 읽기
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"이미지를 읽을 수 없습니다: {image_path}")

    height, width = image.shape[:2]

    # 패딩을 포함한 크롭 영역 계산
    x_min = max(0, bbox['x_min'] - padding)
    y_min = max(0, bbox['y_min'] - padding)
    x_max = min(width, bbox['x_max'] + padding)
    y_max = min(height, bbox['y_max'] + padding)

    # 크롭 실행
    cropped_image = image[y_min:y_max, x_min:x_max]

    return cropped_image


def crop_all_blocks(image_path: str, blocks: List[Dict], padding: int = 5) -> List[Tuple[int, np.ndarray]]:
    """
    모든 블록 이미지를 크롭

    Args:
        image_path: 원본 이미지 경로
        blocks: 블록 정보 리스트
        padding: 크롭 시 추가할 패딩

    Returns:
        (블록_id, 크롭된_이미지) 튜플 리스트
    """
    cropped_blocks = []

    for block in blocks:
        try:
            cropped_image = crop_block_image(image_path, block['bbox'], padding)
            cropped_blocks.append((block['id'], cropped_image))
        except Exception as e:
            print(f"블록 {block['id']} 크롭 실패: {e}")
            continue

    return cropped_blocks


__all__ = ['extract_blocks', 'crop_block_image', 'crop_all_blocks']
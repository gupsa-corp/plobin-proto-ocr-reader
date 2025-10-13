#!/usr/bin/env python3
"""
Extract text blocks from images using Surya OCR
"""

import os
import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
from PIL import Image
from .merging import merge_adjacent_blocks
from .section_grouping import group_blocks_by_sections, classify_sections_by_type
from .hierarchy import build_hierarchy, get_hierarchy_statistics


def extract_blocks(ocr_predictors, image_path: str, confidence_threshold: float = 0.5,
                  merge_blocks: bool = True, merge_threshold: int = 30,
                  lang: str = 'ko', create_sections: bool = False,
                  build_hierarchy_tree: bool = False, **kwargs) -> Dict:
    """
    이미지에서 문서 블록 추출 (Surya OCR 사용)

    Args:
        ocr_predictors: Surya OCR predictor 튜플 (det_predictor, rec_predictor)
        image_path: 이미지 파일 경로
        confidence_threshold: 신뢰도 임계값
        merge_blocks: 블록 병합 여부
        merge_threshold: 병합 임계값
        lang: 언어 코드 ('ko', 'en' 등)
        **kwargs: 추가 설정 (호환성 유지)

    Returns:
        블록 정보가 포함된 딕셔너리
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")

    det_predictor, rec_predictor = ocr_predictors

    # 이미지 읽기
    print("이미지 로드 중...")
    pil_image = Image.open(image_path).convert("RGB")
    cv_image = cv2.imread(image_path)
    if cv_image is None:
        raise ValueError(f"이미지를 읽을 수 없습니다: {image_path}")

    # Surya OCR 실행
    print("Surya OCR 처리 중...")

    # 텍스트 감지
    det_results = det_predictor([pil_image])

    # 텍스트 인식 (task_names는 언어별 작업 지정, None이면 기본 OCR)
    rec_results = rec_predictor([pil_image], det_predictor=det_predictor)

    # 결과 파싱
    blocks = []
    if rec_results and len(rec_results) > 0:
        page_result = rec_results[0]
        text_lines = page_result.text_lines

        print(f"OCR 감지된 총 텍스트 라인 수: {len(text_lines)}")

        for idx, text_line in enumerate(text_lines):
            # 신뢰도 확인
            confidence = text_line.confidence if hasattr(text_line, 'confidence') else 1.0
            if confidence < confidence_threshold:
                print(f"신뢰도 낮음 제외 (confidence={confidence:.3f}): {text_line.text}")
                continue

            # 바운딩 박스 좌표 추출
            bbox = text_line.bbox
            x_min, y_min, x_max, y_max = map(int, bbox)

            # 블록 타입 분류 (단순화)
            block_type = 'text'

            block_info = {
                'id': idx,
                'text': text_line.text,
                'confidence': float(confidence),
                'bbox': {
                    'x_min': x_min,
                    'y_min': y_min,
                    'x_max': x_max,
                    'y_max': y_max,
                    'width': x_max - x_min,
                    'height': y_max - y_min
                },
                'bbox_points': [[x_min, y_min], [x_max, y_min], [x_max, y_max], [x_min, y_max]],
                'type': block_type,
                'area': (x_max - x_min) * (y_max - y_min)
            }
            blocks.append(block_info)

    # 블록 병합 처리
    print(f"병합 전 블록 수: {len(blocks)}")
    if merge_blocks and blocks:
        blocks = merge_adjacent_blocks(blocks, merge_threshold)
        print(f"병합 후 블록 수: {len(blocks)}")

    # 이미지 정보
    height, width = cv_image.shape[:2]

    result = {
        'image_info': {
            'path': image_path,
            'width': width,
            'height': height,
            'total_blocks': len(blocks)
        },
        'blocks': blocks,
        'processing_info': {
            'confidence_threshold': confidence_threshold,
            'language': lang,
            'merge_blocks': merge_blocks,
            'merge_threshold': merge_threshold,
            'ocr_engine': 'surya',
            'sections_created': create_sections,
            'hierarchy_built': build_hierarchy_tree
        }
    }

    # 섹션 그룹핑 (선택적)
    if create_sections and blocks:
        print("섹션 그룹핑 수행 중...")
        sections = group_blocks_by_sections(blocks)
        sections = classify_sections_by_type(sections)
        result['sections'] = sections
        result['section_summary'] = {
            'total_sections': len(sections),
            'section_types': {
                section_type: len([s for s in sections if s.get('section_type') == section_type])
                for section_type in set([s.get('section_type', 'unknown') for s in sections])
            }
        }
        print(f"섹션 그룹핑 완료: {len(sections)}개 섹션 생성")

    # 계층 구조 구축 (선택적)
    if build_hierarchy_tree and blocks:
        print("계층 구조 구축 중...")
        hierarchical_blocks = build_hierarchy(blocks)
        hierarchy_stats = get_hierarchy_statistics(hierarchical_blocks)
        result['hierarchical_blocks'] = hierarchical_blocks
        result['hierarchy_statistics'] = hierarchy_stats
        print(f"계층 구조 구축 완료: {hierarchy_stats['max_depth']}단계 깊이")

    return result


def extract_blocks_with_layout_analysis(ocr_predictors, image_path: str, confidence_threshold: float = 0.5,
                                        merge_blocks: bool = True, merge_threshold: int = 30,
                                        enable_table_recognition: bool = True, lang: str = 'ko',
                                        use_cache: bool = True) -> Dict:
    """
    레이아웃 분석을 포함한 향상된 블록 추출 (Surya OCR 사용)

    Args:
        ocr_predictors: Surya OCR predictor 튜플
        image_path: 이미지 파일 경로
        confidence_threshold: 신뢰도 임계값
        merge_blocks: 블록 병합 여부
        merge_threshold: 병합 임계값
        enable_table_recognition: 표 인식 활성화 여부
        lang: 언어 코드
        use_cache: 캐싱 사용 여부

    Returns:
        레이아웃 분석 결과가 포함된 블록 정보 딕셔너리
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")

    # 캐시 확인
    if use_cache:
        try:
            from ..cache import get_ocr_cache
            cache_config = {
                'confidence_threshold': confidence_threshold,
                'merge_blocks': merge_blocks,
                'merge_threshold': merge_threshold,
                'enable_table_recognition': enable_table_recognition,
                'function': 'extract_blocks_with_layout_analysis',
                'ocr_engine': 'surya'
            }
            cache = get_ocr_cache()
            cached_result = cache.get(image_path, cache_config)
            if cached_result:
                print("캐시된 결과 사용")
                return cached_result
        except Exception as e:
            print(f"캐시 확인 중 오류: {e}")

    # 기본 OCR 블록 추출
    basic_result = extract_blocks(ocr_predictors, image_path, confidence_threshold,
                                 merge_blocks, merge_threshold, lang=lang)

    blocks = basic_result['blocks']
    layout_info = {'tables': [], 'layout_elements': {}}

    # Surya의 레이아웃 분석 (선택적, 현재 간소화)
    if enable_table_recognition:
        try:
            print("레이아웃 분석 수행 중...")
            # 현재는 간단한 레이아웃 정보만 제공
            # Surya의 고급 레이아웃 분석은 추후 구현 가능
            layout_info['layout_elements'] = {
                'texts': blocks,
                'tables': [],
                'titles': [],
                'paragraphs': [],
                'figures': []
            }
            layout_info['layout_summary'] = {
                'total_tables': 0,
                'total_titles': 0,
                'total_paragraphs': 0,
                'total_figures': 0
            }

            print("레이아웃 분석 완료")

        except Exception as e:
            print(f"레이아웃 분석 중 오류 (기본 OCR로 계속): {e}")

    result = {
        'metadata': {
            'image_path': image_path,
            'total_blocks': len(blocks),
            'tables_detected': len(layout_info.get('tables', [])),
            'layout_analysis_enabled': enable_table_recognition,
            'ocr_engine': 'surya'
        },
        'blocks': blocks,
        'layout_info': layout_info,
        'processing_info': {
            'confidence_threshold': confidence_threshold,
            'language': lang,
            'merge_blocks': merge_blocks,
            'merge_threshold': merge_threshold,
            'table_recognition': enable_table_recognition,
            'ocr_engine': 'surya'
        }
    }

    # 결과 캐시에 저장
    if use_cache:
        try:
            from ..cache import get_ocr_cache
            cache = get_ocr_cache()
            cache.set(image_path, cache_config, result)
        except Exception as e:
            print(f"캐시 저장 중 오류: {e}")

    return result


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


__all__ = ['extract_blocks', 'extract_blocks_with_layout_analysis', 'crop_block_image', 'crop_all_blocks']

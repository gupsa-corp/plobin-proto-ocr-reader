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
from ..cache import get_ocr_cache
from ..analysis import create_chart_detector


def extract_blocks(ocr_instance, image_path: str, confidence_threshold: float = 0.5, merge_blocks: bool = True, merge_threshold: int = 30,
                  use_korean_enhancement: bool = False, preprocessing_level: str = 'medium') -> Dict:
    """
    이미지에서 문서 블록 추출

    Args:
        ocr_instance: PaddleOCR 인스턴스
        image_path: 이미지 파일 경로
        confidence_threshold: 신뢰도 임계값
        merge_blocks: 블록 병합 여부
        merge_threshold: 병합 임계값
        use_korean_enhancement: 한글 최적화 사용 (현재 미구현, 호환성 유지용)
        preprocessing_level: 전처리 레벨 (현재 미구현, 호환성 유지용)

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
        print(f"OCR 감지된 총 텍스트 수: {len(result[0])}")
        for idx, detection in enumerate(result[0]):
            bbox, (text, confidence) = detection

            # 신뢰도 필터링
            if confidence < confidence_threshold:
                print(f"신뢰도 낮음 제외 (confidence={confidence:.3f}): {text}")
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
    print(f"병합 전 블록 수: {len(blocks)}")
    if merge_blocks and blocks:
        blocks = merge_adjacent_blocks(blocks, merge_threshold)
        print(f"병합 후 블록 수: {len(blocks)}")

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
                                        enable_table_recognition: bool = True, use_cache: bool = True) -> Dict:
    """
    레이아웃 분석 및 표 인식을 포함한 향상된 블록 추출 (캐싱 지원)

    Args:
        ocr_instance: PaddleOCR 인스턴스
        image_path: 이미지 파일 경로
        confidence_threshold: 신뢰도 임계값
        merge_blocks: 블록 병합 여부
        merge_threshold: 병합 임계값
        enable_table_recognition: 표 인식 활성화 여부
        use_cache: 캐싱 사용 여부

    Returns:
        레이아웃 분석 결과가 포함된 블록 정보 딕셔너리
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")

    # 캐시 설정
    cache_config = {
        'confidence_threshold': confidence_threshold,
        'merge_blocks': merge_blocks,
        'merge_threshold': merge_threshold,
        'enable_table_recognition': enable_table_recognition,
        'function': 'extract_blocks_with_layout_analysis'
    }

    # 캐시 확인
    if use_cache:
        cache = get_ocr_cache()
        cached_result = cache.get(image_path, cache_config)
        if cached_result:
            print("캐시된 결과 사용")
            return cached_result

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

    # 경량 차트 감지 수행 (선택적)
    if enable_table_recognition:
        try:
            print("경량 차트 감지 수행 중...")
            chart_detector = create_chart_detector()
            detected_charts = chart_detector.detect_charts(image_path, blocks)

            # 차트 정보를 레이아웃 정보에 추가
            layout_info['charts'] = detected_charts

            # 차트 영역과 겹치는 블록들을 chart 타입으로 재분류
            blocks = _update_blocks_with_chart_info(blocks, detected_charts)

            print(f"경량 차트 {len(detected_charts)}개 감지됨")

        except Exception as e:
            print(f"차트 감지 중 오류 (무시하고 계속): {e}")

    result = {
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

    # 결과 캐시에 저장
    if use_cache:
        cache = get_ocr_cache()
        cache.set(image_path, cache_config, result)

    return result


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
                elif element_type == 'figures':
                    element_type_name = 'figure'
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
            else:
                # 레이아웃 분석이 실패한 경우 텍스트 기반 분류 시도
                enhanced_type = _classify_block_by_content(block)
                if enhanced_type != 'other':
                    block['type'] = enhanced_type
                    block['content_confidence'] = 0.8

    except Exception as e:
        print(f"블록 타입 향상 중 오류: {e}")

    return blocks


def _classify_block_by_content(block: Dict) -> str:
    """
    텍스트 내용을 기반으로 블록 타입을 분류

    Args:
        block: 블록 정보

    Returns:
        분류된 블록 타입
    """
    import re

    text = block.get('text', '').strip()
    if not text:
        return 'other'

    text_lower = text.lower()

    # 수식 패턴 (간단한 수학 기호 감지)
    math_patterns = [
        r'[∑∏∫∂∇αβγδεζηθικλμνξοπρστυφχψω]',  # 그리스 문자 및 수학 기호
        r'\b\d+[\+\-\×\÷]\d+\b',  # 간단한 수식
        r'\$.*\$',  # LaTeX 수식
        r'[=≠<>≤≥±∞]',  # 수학 연산자
        r'\b(sin|cos|tan|log|ln|exp|sqrt)\b'  # 수학 함수
    ]

    # 금액/가격 패턴
    money_patterns = [
        r'[\$￦€£¥]\s*[\d,]+',  # 통화 기호 + 숫자
        r'\b\d+원\b',  # 원화
        r'\btotal\s*[:=]\s*[\$￦]\d+',  # 총계
        r'\bsubtotal\s*[:=]',  # 소계
        r'\btax\s*[:=]'  # 세금
    ]

    # 제목 패턴 (크기나 위치 정보도 고려)
    title_patterns = [
        r'^[A-Z\s]{3,50}$',  # 모두 대문자인 짧은 텍스트
        r'^\d+\.\s+[A-Z]',  # 번호가 있는 제목
        r'^(CHAPTER|SECTION|PART)\s+\d+',  # 챕터/섹션
        r'^(제\s*\d+\s*장|제\s*\d+\s*절)',  # 한국어 장/절
    ]

    # 서명 패턴
    signature_patterns = [
        r'(signature|서명|sign)',
        r'(date|날짜|일자).*\d{4}',
        r'^[A-Za-z가-힣\s]{2,20}$'  # 사람 이름 길이의 텍스트
    ]

    # 차트/그래프 관련 패턴
    chart_patterns = [
        r'(chart|graph|그래프|차트|도표)',
        r'(figure|fig\.|그림)\s*\d+',
        r'(table|표)\s*\d+',
        r'\b(x-axis|y-axis|축)\b'
    ]

    bbox = block.get('bbox', {})
    width = bbox.get('x_max', 0) - bbox.get('x_min', 0)
    height = bbox.get('y_max', 0) - bbox.get('y_min', 0)

    # 수식 검사
    for pattern in math_patterns:
        if re.search(pattern, text):
            return 'equation'

    # 금액/표 관련 검사
    for pattern in money_patterns:
        if re.search(pattern, text_lower):
            return 'table'

    # 차트/그래프 검사
    for pattern in chart_patterns:
        if re.search(pattern, text_lower):
            return 'figure'

    # 제목 검사 (텍스트 크기도 고려)
    if height > 20:  # 큰 텍스트일 가능성
        for pattern in title_patterns:
            if re.search(pattern, text):
                return 'title'

    # 서명 검사 (작고 독립적인 텍스트)
    if len(text) < 30 and width < 200:
        for pattern in signature_patterns:
            if re.search(pattern, text_lower):
                return 'signature'

    # 로고 패턴 (매우 짧고 위쪽에 위치)
    if len(text) < 10 and bbox.get('y_min', 1000) < 100:
        if re.search(r'^[A-Z]{2,8}$', text) or '©' in text or '®' in text:
            return 'logo'

    return 'other'


def _update_blocks_with_chart_info(blocks: List[Dict], charts: List[Dict]) -> List[Dict]:
    """
    차트 정보를 사용해 블록 타입을 업데이트

    Args:
        blocks: OCR 블록 리스트
        charts: 감지된 차트 리스트

    Returns:
        업데이트된 블록 리스트
    """
    try:
        for block in blocks:
            block_bbox = [
                block.get('bbox', {}).get('x_min', 0),
                block.get('bbox', {}).get('y_min', 0),
                block.get('bbox', {}).get('x_max', 0),
                block.get('bbox', {}).get('y_max', 0)
            ]

            for chart in charts:
                chart_bbox = chart.get('bbox', [])
                if len(chart_bbox) >= 4:
                    overlap = _calculate_overlap_ratio(block_bbox, chart_bbox)

                    # 차트와 겹치는 블록을 차트 관련 타입으로 분류
                    if overlap > 0.3:  # 30% 이상 겹침
                        chart_type = chart.get('type', 'chart')
                        if chart_type == 'bar_chart':
                            block['type'] = 'chart'
                            block['chart_subtype'] = 'bar'
                        elif chart_type == 'line_chart':
                            block['type'] = 'chart'
                            block['chart_subtype'] = 'line'
                        elif chart_type == 'pie_chart':
                            block['type'] = 'chart'
                            block['chart_subtype'] = 'pie'
                        else:
                            block['type'] = 'figure'

                        block['chart_confidence'] = chart.get('confidence', 0.5)
                        block['chart_overlap'] = overlap
                        break

    except Exception as e:
        print(f"차트 블록 업데이트 중 오류: {e}")

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
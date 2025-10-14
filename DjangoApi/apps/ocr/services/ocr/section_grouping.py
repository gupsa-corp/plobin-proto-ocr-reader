"""
섹션 단위 블록 그룹핑

위치, 스타일, 의미적 유사성을 기반으로 텍스트 블록들을 논리적 섹션으로 그룹화
"""

from typing import List, Dict, Optional, Tuple
import numpy as np
from collections import defaultdict


def calculate_vertical_gap(block1: Dict, block2: Dict) -> float:
    """
    두 블록 간의 수직 간격 계산

    Args:
        block1: 첫 번째 블록
        block2: 두 번째 블록

    Returns:
        수직 간격 (픽셀)
    """
    bbox1 = block1['bbox']
    bbox2 = block2['bbox']

    # block1이 위에 있고 block2가 아래에 있다고 가정
    if bbox1['y_max'] < bbox2['y_min']:
        return bbox2['y_min'] - bbox1['y_max']
    elif bbox2['y_max'] < bbox1['y_min']:
        return bbox1['y_min'] - bbox2['y_max']
    else:
        return 0  # 겹침


def calculate_horizontal_alignment(block1: Dict, block2: Dict) -> float:
    """
    두 블록의 수평 정렬 정도 계산

    Args:
        block1: 첫 번째 블록
        block2: 두 번째 블록

    Returns:
        정렬 점수 (0.0 ~ 1.0, 1.0이 완벽한 정렬)
    """
    bbox1 = block1['bbox']
    bbox2 = block2['bbox']

    # 왼쪽 정렬 점수
    left_diff = abs(bbox1['x_min'] - bbox2['x_min'])

    # 오른쪽 정렬 점수
    right_diff = abs(bbox1['x_max'] - bbox2['x_max'])

    # 중앙 정렬 점수
    center1 = (bbox1['x_min'] + bbox1['x_max']) / 2
    center2 = (bbox2['x_min'] + bbox2['x_max']) / 2
    center_diff = abs(center1 - center2)

    # 이미지 너비 대비 상대적 차이
    max_width = max(bbox1['width'], bbox2['width'])
    if max_width == 0:
        return 0.0

    # 가장 좋은 정렬 점수 반환
    best_alignment = min(left_diff, right_diff, center_diff) / max_width

    return max(0.0, 1.0 - best_alignment)


def group_blocks_by_sections(
    blocks: List[Dict],
    vertical_gap_threshold: float = 30.0,
    horizontal_alignment_threshold: float = 0.8,
    min_section_blocks: int = 1
) -> List[Dict]:
    """
    블록들을 섹션 단위로 그룹화

    Args:
        blocks: OCR 블록 리스트
        vertical_gap_threshold: 섹션 구분을 위한 수직 간격 임계값 (픽셀)
        horizontal_alignment_threshold: 수평 정렬 임계값 (0.0 ~ 1.0)
        min_section_blocks: 최소 섹션 블록 수

    Returns:
        섹션 정보가 포함된 리스트
    """
    if not blocks:
        return []

    # Y 좌표 기준으로 블록 정렬
    sorted_blocks = sorted(blocks, key=lambda b: b['bbox']['y_min'])

    sections = []
    current_section = {
        'section_id': 0,
        'blocks': [sorted_blocks[0].copy()],
        'bbox': sorted_blocks[0]['bbox'].copy(),
        'type': 'section'
    }

    for i in range(1, len(sorted_blocks)):
        prev_block = sorted_blocks[i-1]
        curr_block = sorted_blocks[i]

        # 수직 간격 계산
        vertical_gap = calculate_vertical_gap(prev_block, curr_block)

        # 수평 정렬 계산
        horizontal_alignment = calculate_horizontal_alignment(prev_block, curr_block)

        # 새 섹션 시작 조건
        should_start_new_section = (
            vertical_gap > vertical_gap_threshold or
            horizontal_alignment < horizontal_alignment_threshold
        )

        if should_start_new_section:
            # 현재 섹션 완료
            if len(current_section['blocks']) >= min_section_blocks:
                sections.append(current_section)

            # 새 섹션 시작
            current_section = {
                'section_id': len(sections),
                'blocks': [curr_block.copy()],
                'bbox': curr_block['bbox'].copy(),
                'type': 'section'
            }
        else:
            # 현재 섹션에 블록 추가
            current_section['blocks'].append(curr_block.copy())

            # 섹션 bbox 업데이트 (병합)
            current_bbox = current_section['bbox']
            curr_bbox = curr_block['bbox']

            current_section['bbox'] = {
                'x_min': min(current_bbox['x_min'], curr_bbox['x_min']),
                'y_min': min(current_bbox['y_min'], curr_bbox['y_min']),
                'x_max': max(current_bbox['x_max'], curr_bbox['x_max']),
                'y_max': max(current_bbox['y_max'], curr_bbox['y_max']),
                'width': 0,  # 나중에 계산
                'height': 0  # 나중에 계산
            }
            current_section['bbox']['width'] = (
                current_section['bbox']['x_max'] - current_section['bbox']['x_min']
            )
            current_section['bbox']['height'] = (
                current_section['bbox']['y_max'] - current_section['bbox']['y_min']
            )

    # 마지막 섹션 추가
    if len(current_section['blocks']) >= min_section_blocks:
        sections.append(current_section)

    # 섹션 메타데이터 추가
    for section in sections:
        section['total_blocks'] = len(section['blocks'])
        section['text'] = ' '.join([b['text'] for b in section['blocks']])
        section['avg_confidence'] = sum([b['confidence'] for b in section['blocks']]) / len(section['blocks'])
        section['area'] = section['bbox']['width'] * section['bbox']['height']

    return sections


def classify_sections_by_type(sections: List[Dict]) -> List[Dict]:
    """
    섹션 타입 분류 (헤더, 본문, 푸터 등)

    Args:
        sections: 섹션 리스트

    Returns:
        타입이 분류된 섹션 리스트
    """
    if not sections:
        return []

    # 이미지 전체 높이 계산
    all_y_coords = []
    for section in sections:
        all_y_coords.extend([section['bbox']['y_min'], section['bbox']['y_max']])

    img_height = max(all_y_coords) if all_y_coords else 1

    for i, section in enumerate(sections):
        # 위치 기반 분류
        y_position = section['bbox']['y_min'] / img_height

        # 기본 타입 설정
        if y_position < 0.15:
            section['section_type'] = 'header'
        elif y_position > 0.85:
            section['section_type'] = 'footer'
        else:
            section['section_type'] = 'body'

        # 텍스트 내용 기반 추가 분류
        text_lower = section['text'].lower()

        # 제목 패턴
        if i == 0 or (section['total_blocks'] == 1 and len(section['text']) < 50):
            if any(keyword in text_lower for keyword in ['제목', 'title', '공고', 'notice']):
                section['section_type'] = 'title'

        # 표 패턴
        if section['total_blocks'] > 3:
            # 블록들의 x 좌표가 일정하게 정렬되어 있는지 확인 (표의 특징)
            x_coords = [b['bbox']['x_min'] for b in section['blocks']]
            if len(set(x_coords)) <= 3:  # 최대 3개의 열
                section['section_type'] = 'table'

        # 리스트 패턴
        if any(b['text'].strip().startswith(('•', '-', '*', '1.', '2.', '3.')) for b in section['blocks']):
            section['section_type'] = 'list'

    return sections


def create_hierarchical_structure(blocks: List[Dict], sections: List[Dict]) -> Dict:
    """
    블록과 섹션을 결합한 계층 구조 생성

    Args:
        blocks: 원본 블록 리스트
        sections: 섹션 리스트

    Returns:
        계층 구조 딕셔너리
    """
    return {
        'document': {
            'total_sections': len(sections),
            'total_blocks': len(blocks),
            'sections': sections
        },
        'metadata': {
            'section_types': {
                section_type: len([s for s in sections if s.get('section_type') == section_type])
                for section_type in set([s.get('section_type', 'unknown') for s in sections])
            }
        }
    }


def extract_section_summary(section: Dict) -> Dict:
    """
    섹션 요약 정보 추출

    Args:
        section: 섹션 딕셔너리

    Returns:
        요약 정보 딕셔너리
    """
    return {
        'section_id': section['section_id'],
        'section_type': section.get('section_type', 'unknown'),
        'total_blocks': section['total_blocks'],
        'text_preview': section['text'][:100] + '...' if len(section['text']) > 100 else section['text'],
        'avg_confidence': round(section['avg_confidence'], 3),
        'bbox': section['bbox'],
        'area': section['area']
    }


def get_sections_by_type(sections: List[Dict], section_type: str) -> List[Dict]:
    """
    특정 타입의 섹션들만 필터링

    Args:
        sections: 섹션 리스트
        section_type: 섹션 타입 ('header', 'body', 'footer', 'title', 'table', 'list')

    Returns:
        필터링된 섹션 리스트
    """
    return [s for s in sections if s.get('section_type') == section_type]


__all__ = [
    'group_blocks_by_sections',
    'classify_sections_by_type',
    'create_hierarchical_structure',
    'extract_section_summary',
    'get_sections_by_type'
]

"""
블록 계층 구조 감지 및 관리
"""

from typing import List, Dict, Optional, Set
import numpy as np


def calculate_overlap_ratio(box1: Dict, box2: Dict) -> float:
    """
    두 바운딩 박스의 겹침 비율 계산

    Args:
        box1: 첫 번째 박스 (bbox 또는 bbox_points)
        box2: 두 번째 박스 (bbox 또는 bbox_points)

    Returns:
        겹침 비율 (0.0 ~ 1.0)
    """
    # bbox 정보 추출
    if 'bbox' in box1:
        x1_min, y1_min = box1['bbox']['x_min'], box1['bbox']['y_min']
        x1_max, y1_max = box1['bbox']['x_max'], box1['bbox']['y_max']
    else:
        points = box1.get('bbox_points', [])
        if not points:
            return 0.0
        x_coords = [p[0] for p in points]
        y_coords = [p[1] for p in points]
        x1_min, x1_max = min(x_coords), max(x_coords)
        y1_min, y1_max = min(y_coords), max(y_coords)

    if 'bbox' in box2:
        x2_min, y2_min = box2['bbox']['x_min'], box2['bbox']['y_min']
        x2_max, y2_max = box2['bbox']['x_max'], box2['bbox']['y_max']
    else:
        points = box2.get('bbox_points', [])
        if not points:
            return 0.0
        x_coords = [p[0] for p in points]
        y_coords = [p[1] for p in points]
        x2_min, x2_max = min(x_coords), max(x_coords)
        y2_min, y2_max = min(y_coords), max(y_coords)

    # 겹치는 영역 계산
    x_overlap = max(0, min(x1_max, x2_max) - max(x1_min, x2_min))
    y_overlap = max(0, min(y1_max, y2_max) - max(y1_min, y2_min))
    overlap_area = x_overlap * y_overlap

    # 작은 박스의 면적
    area1 = (x1_max - x1_min) * (y1_max - y1_min)
    area2 = (x2_max - x2_min) * (y2_max - y2_min)
    smaller_area = min(area1, area2)

    if smaller_area == 0:
        return 0.0

    return overlap_area / smaller_area


def is_contained(child: Dict, parent: Dict, threshold: float = 0.9) -> bool:
    """
    child 블록이 parent 블록에 포함되는지 확인

    Args:
        child: 자식 블록 후보
        parent: 부모 블록 후보
        threshold: 포함 판정 임계값 (기본 90%)

    Returns:
        포함 여부
    """
    # child가 parent보다 큰 경우 포함될 수 없음
    child_area = child.get('area', 0)
    parent_area = parent.get('area', 0)

    if child_area >= parent_area:
        return False

    # 겹침 비율 계산
    overlap_ratio = calculate_overlap_ratio(child, parent)

    return overlap_ratio >= threshold


def build_hierarchy(blocks: List[Dict], containment_threshold: float = 0.9) -> List[Dict]:
    """
    블록 리스트에서 계층 구조 구축

    Args:
        blocks: 블록 리스트
        containment_threshold: 포함 판정 임계값

    Returns:
        계층 구조가 추가된 블록 리스트 (최상위 블록만)
    """
    if not blocks:
        return []

    # 블록 복사 (원본 수정 방지)
    blocks_copy = [block.copy() for block in blocks]

    # 각 블록에 계층 정보 초기화
    for i, block in enumerate(blocks_copy):
        block['block_id'] = i
        block['parent_id'] = None
        block['children'] = []
        block['level'] = 0

    # 블록을 면적 순으로 정렬 (큰 것부터)
    sorted_blocks = sorted(blocks_copy, key=lambda x: x.get('area', 0), reverse=True)

    # 부모-자식 관계 구축
    for i, potential_parent in enumerate(sorted_blocks):
        for potential_child in sorted_blocks[i+1:]:  # 자신보다 작은 블록들만 확인
            # 이미 부모가 있는지 확인
            if potential_child['parent_id'] is not None:
                continue

            # 포함 관계 확인
            if is_contained(potential_child, potential_parent, containment_threshold):
                potential_child['parent_id'] = potential_parent['block_id']
                potential_parent['children'].append(potential_child['block_id'])

    # 레벨 계산 (깊이)
    def calculate_level(block_id: int, blocks_dict: Dict[int, Dict]) -> int:
        block = blocks_dict[block_id]
        if block['parent_id'] is None:
            return 0
        return 1 + calculate_level(block['parent_id'], blocks_dict)

    blocks_dict = {b['block_id']: b for b in sorted_blocks}
    for block in sorted_blocks:
        block['level'] = calculate_level(block['block_id'], blocks_dict)

    # 모든 블록을 block_id 순으로 반환 (계층 정보 포함)
    return sorted(sorted_blocks, key=lambda x: x['block_id'])


def get_block_hierarchy_tree(blocks: List[Dict]) -> List[Dict]:
    """
    계층 구조를 트리 형태로 변환

    Args:
        blocks: build_hierarchy로 처리된 블록 리스트

    Returns:
        트리 구조의 블록 리스트
    """
    blocks_dict = {b['block_id']: b for b in blocks}

    def build_tree(block: Dict) -> Dict:
        """재귀적으로 트리 구조 생성"""
        tree_block = block.copy()

        # children ID를 실제 블록 객체로 변환
        if block['children']:
            tree_block['children'] = [
                build_tree(blocks_dict[child_id])
                for child_id in block['children']
            ]
        else:
            tree_block['children'] = []

        return tree_block

    # 최상위 블록들만 처리
    root_blocks = [b for b in blocks if b.get('parent_id') is None]

    return [build_tree(block) for block in root_blocks]


def get_hierarchy_statistics(blocks: List[Dict]) -> Dict:
    """
    계층 구조 통계 정보 반환

    Args:
        blocks: build_hierarchy로 처리된 평면 블록 리스트

    Returns:
        통계 정보 딕셔너리
    """
    if not blocks:
        return {
            'total_blocks': 0,
            'root_blocks': 0,
            'max_depth': 0,
            'avg_children': 0.0,
            'blocks_by_level': {}
        }

    # 평면 리스트에서 직접 통계 계산
    root_blocks = [b for b in blocks if b.get('parent_id') is None]
    max_depth = max([b.get('level', 0) for b in blocks]) if blocks else 0

    # 레벨별 블록 수
    blocks_by_level = {}
    for block in blocks:
        level = block.get('level', 0)
        blocks_by_level[level] = blocks_by_level.get(level, 0) + 1

    # 평균 자식 수 (자식이 있는 블록만)
    blocks_with_children = [b for b in blocks if b.get('children')]
    avg_children = (
        sum(len(b['children']) for b in blocks_with_children) / len(blocks_with_children)
        if blocks_with_children else 0.0
    )

    return {
        'total_blocks': len(blocks),
        'root_blocks': len(root_blocks),
        'max_depth': max_depth,
        'avg_children': round(avg_children, 2),
        'blocks_by_level': blocks_by_level
    }


def flatten_hierarchy(hierarchical_blocks: List[Dict]) -> List[Dict]:
    """
    계층 구조를 평면 리스트로 변환 (계층 정보는 유지)

    Args:
        hierarchical_blocks: 트리 구조의 블록 리스트

    Returns:
        평면화된 블록 리스트
    """
    flat_blocks = []

    def flatten_recursive(block: Dict):
        # children을 ID 리스트로 변환
        child_ids = []
        children_objects = block.get('children', [])

        # 현재 블록 추가
        block_copy = block.copy()

        # children 객체들을 재귀 처리
        if isinstance(children_objects, list) and children_objects:
            if isinstance(children_objects[0], dict):
                for child in children_objects:
                    child_ids.append(child['block_id'])
                    flatten_recursive(child)

        block_copy['children'] = child_ids
        flat_blocks.append(block_copy)

    for block in hierarchical_blocks:
        flatten_recursive(block)

    # block_id 순으로 정렬
    return sorted(flat_blocks, key=lambda x: x['block_id'])


__all__ = [
    'calculate_overlap_ratio',
    'is_contained',
    'build_hierarchy',
    'get_block_hierarchy_tree',
    'get_hierarchy_statistics',
    'flatten_hierarchy'
]

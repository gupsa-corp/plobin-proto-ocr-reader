#!/usr/bin/env python3
"""
Merge adjacent text blocks for better sentence grouping
"""

from typing import List, Dict


def merge_adjacent_blocks(blocks: List[Dict], merge_threshold: int = 30) -> List[Dict]:
    """
    인접한 블록들을 병합하여 문장 단위로 그룹화

    Args:
        blocks: 원본 블록 리스트
        merge_threshold: 병합할 최대 거리 (픽셀)

    Returns:
        병합된 블록 리스트
    """
    if not blocks:
        return blocks

    # Y 좌표 기준으로 정렬 (위에서 아래로)
    sorted_blocks = sorted(blocks, key=lambda b: b['bbox']['y_min'])

    merged_blocks = []
    current_line_blocks = [sorted_blocks[0]]

    for i in range(1, len(sorted_blocks)):
        current_block = sorted_blocks[i]
        last_block = current_line_blocks[-1]

        # Y 좌표 차이가 임계값 이하이고 X 좌표가 겹치지 않으면 같은 줄로 간주
        y_diff = abs(current_block['bbox']['y_min'] - last_block['bbox']['y_min'])
        height_avg = (current_block['bbox']['height'] + last_block['bbox']['height']) / 2

        # 같은 줄인지 판단 (Y 차이가 평균 높이의 절반 이하)
        if y_diff <= height_avg * 0.5:
            current_line_blocks.append(current_block)
        else:
            # 현재 줄의 블록들을 X 좌표 기준으로 정렬하여 병합
            if len(current_line_blocks) > 1:
                merged_block = merge_line_blocks(current_line_blocks, merge_threshold)
                merged_blocks.append(merged_block)
            else:
                merged_blocks.append(current_line_blocks[0])

            # 새로운 줄 시작
            current_line_blocks = [current_block]

    # 마지막 줄 처리
    if len(current_line_blocks) > 1:
        merged_block = merge_line_blocks(current_line_blocks, merge_threshold)
        merged_blocks.append(merged_block)
    else:
        merged_blocks.append(current_line_blocks[0])

    return merged_blocks


def merge_line_blocks(line_blocks: List[Dict], merge_threshold: int) -> Dict:
    """
    같은 줄의 블록들을 하나로 병합

    Args:
        line_blocks: 같은 줄의 블록들
        merge_threshold: 병합할 최대 거리

    Returns:
        병합된 블록
    """
    # X 좌표 기준으로 정렬 (왼쪽에서 오른쪽으로)
    sorted_blocks = sorted(line_blocks, key=lambda b: b['bbox']['x_min'])

    merged_groups = []
    current_group = [sorted_blocks[0]]

    for i in range(1, len(sorted_blocks)):
        current_block = sorted_blocks[i]
        last_block = current_group[-1]

        # X 좌표 거리 계산
        x_distance = current_block['bbox']['x_min'] - last_block['bbox']['x_max']

        # 거리가 임계값 이하면 같은 그룹으로 병합
        if x_distance <= merge_threshold:
            current_group.append(current_block)
        else:
            # 현재 그룹을 병합하여 추가
            if len(current_group) > 1:
                merged_groups.append(create_merged_block(current_group))
            else:
                merged_groups.append(current_group[0])

            # 새로운 그룹 시작
            current_group = [current_block]

    # 마지막 그룹 처리
    if len(current_group) > 1:
        merged_groups.append(create_merged_block(current_group))
    else:
        merged_groups.append(current_group[0])

    # 그룹이 하나면 그대로 반환, 여러 개면 다시 병합
    if len(merged_groups) == 1:
        return merged_groups[0]
    else:
        return create_merged_block(merged_groups)


def create_merged_block(blocks: List[Dict]) -> Dict:
    """
    여러 블록을 하나로 병합

    Args:
        blocks: 병합할 블록들

    Returns:
        병합된 블록
    """
    if len(blocks) == 1:
        return blocks[0]

    # 텍스트 병합 (공백으로 구분)
    merged_text = ' '.join(block['text'] for block in blocks)

    # 신뢰도 평균 계산
    avg_confidence = sum(block['confidence'] for block in blocks) / len(blocks)

    # 바운딩 박스 계산 (모든 블록을 포함하는 최소 직사각형)
    x_mins = [block['bbox']['x_min'] for block in blocks]
    y_mins = [block['bbox']['y_min'] for block in blocks]
    x_maxs = [block['bbox']['x_max'] for block in blocks]
    y_maxs = [block['bbox']['y_max'] for block in blocks]

    merged_x_min = min(x_mins)
    merged_y_min = min(y_mins)
    merged_x_max = max(x_maxs)
    merged_y_max = max(y_maxs)

    # 병합된 바운딩 박스 포인트 (직사각형)
    merged_bbox_points = [
        [merged_x_min, merged_y_min],
        [merged_x_max, merged_y_min],
        [merged_x_max, merged_y_max],
        [merged_x_min, merged_y_max]
    ]

    # 첫 번째 블록의 타입을 사용 (또는 가장 빈번한 타입)
    block_types = [block['type'] for block in blocks]
    merged_type = max(set(block_types), key=block_types.count)

    merged_block = {
        'id': blocks[0]['id'],  # 첫 번째 블록의 ID 사용
        'text': merged_text,
        'confidence': float(avg_confidence),
        'bbox': {
            'x_min': merged_x_min,
            'y_min': merged_y_min,
            'x_max': merged_x_max,
            'y_max': merged_y_max,
            'width': merged_x_max - merged_x_min,
            'height': merged_y_max - merged_y_min
        },
        'bbox_points': merged_bbox_points,
        'type': merged_type,
        'area': (merged_x_max - merged_x_min) * (merged_y_max - merged_y_min),
        'merged_from': len(blocks)  # 몇 개의 블록에서 병합되었는지 표시
    }

    return merged_block


__all__ = ['merge_adjacent_blocks', 'merge_line_blocks', 'create_merged_block']
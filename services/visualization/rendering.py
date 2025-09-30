#!/usr/bin/env python3
"""
Draw bounding boxes on images
"""

import matplotlib.patches as patches


def draw_bounding_boxes(ax, blocks, colors=None):
    """
    이미지에 바운딩 박스를 그리기

    Args:
        ax: matplotlib axes 객체
        blocks: 블록 정보 리스트
        colors: 타입별 색상 딕셔너리

    Returns:
        None (axes 객체에 직접 그리기)
    """
    if colors is None:
        colors = {
            'title': 'red',
            'paragraph': 'blue',
            'table': 'green',
            'list': 'orange',
            'other': 'purple'
        }

    # 블록 시각화
    for block in blocks:
        bbox = block['bbox']
        block_type = block['type']
        confidence = block['confidence']

        # 바운딩 박스 그리기
        rect = patches.Rectangle(
            (bbox['x_min'], bbox['y_min']),
            bbox['width'],
            bbox['height'],
            linewidth=2,
            edgecolor=colors.get(block_type, 'gray'),
            facecolor='none',
            alpha=0.8
        )
        ax.add_patch(rect)

        # 텍스트 라벨 추가
        label = f"{block_type}\n{confidence:.2f}"
        ax.text(
            bbox['x_min'],
            bbox['y_min'] - 5,
            label,
            fontsize=8,
            color=colors.get(block_type, 'gray'),
            bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8)
        )


__all__ = ['draw_bounding_boxes']
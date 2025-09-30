#!/usr/bin/env python3
"""
Create legend for visualization
"""

import matplotlib.patches as patches


def create_legend(ax, colors=None):
    """
    시각화를 위한 범례 생성

    Args:
        ax: matplotlib axes 객체
        colors: 타입별 색상 딕셔너리

    Returns:
        None (axes 객체에 직접 범례 추가)
    """
    if colors is None:
        colors = {
            'title': 'red',
            'paragraph': 'blue',
            'table': 'green',
            'list': 'orange',
            'other': 'purple'
        }

    # 범례 추가
    legend_elements = [
        patches.Patch(color=color, label=block_type.title())
        for block_type, color in colors.items()
    ]
    ax.legend(handles=legend_elements, loc='upper right')


__all__ = ['create_legend']
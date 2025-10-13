#!/usr/bin/env python3
"""
Create legend for visualization
"""

import matplotlib.patches as patches
import matplotlib

# 한글 폰트 설정
matplotlib.rcParams['font.family'] = ['Noto Sans CJK JP', 'DejaVu Sans', 'sans-serif']
matplotlib.rcParams['axes.unicode_minus'] = False


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

    # 한글 타입명 매핑
    type_names = {
        'title': '제목',
        'paragraph': '문단',
        'table': '표',
        'list': '목록',
        'other': '기타'
    }

    # 범례 추가 (한글)
    legend_elements = [
        patches.Patch(color=color, label=type_names.get(block_type, block_type))
        for block_type, color in colors.items()
    ]
    ax.legend(handles=legend_elements, loc='upper right')


__all__ = ['create_legend']
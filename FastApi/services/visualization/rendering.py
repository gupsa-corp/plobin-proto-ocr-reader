#!/usr/bin/env python3
"""
Draw bounding boxes on images
"""

import matplotlib.patches as patches
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
from pathlib import Path

# 프로젝트 루트에서 폰트 파일 경로 찾기
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
font_path = project_root / 'fonts' / 'NotoSansCJK-Regular.ttc'

# 폰트 등록
if font_path.exists():
    font_prop = fm.FontProperties(fname=str(font_path))
    fm.fontManager.addfont(str(font_path))
    matplotlib.rcParams['font.family'] = font_prop.get_name()
else:
    # 폴백: 시스템 폰트 사용
    matplotlib.rcParams['font.family'] = ['Noto Sans CJK JP', 'DejaVu Sans', 'sans-serif']

matplotlib.rcParams['axes.unicode_minus'] = False


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

    # 한글 타입명 매핑
    type_names = {
        'title': '제목',
        'paragraph': '문단',
        'table': '표',
        'list': '목록',
        'other': '기타'
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

        # 텍스트 라벨 추가 (한글)
        korean_type = type_names.get(block_type, block_type)
        label = f"{korean_type}\n{confidence:.2f}"
        ax.text(
            bbox['x_min'],
            bbox['y_min'] - 5,
            label,
            fontsize=8,
            color=colors.get(block_type, 'gray'),
            bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8)
        )


__all__ = ['draw_bounding_boxes']
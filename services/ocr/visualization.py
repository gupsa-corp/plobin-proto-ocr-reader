#!/usr/bin/env python3
"""
Visualize extracted text blocks
"""

import cv2
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import Dict, Optional


def visualize_blocks(image_path: str, result: Dict, save_path: Optional[str] = None):
    """
    추출된 블록을 시각화

    Args:
        image_path: 원본 이미지 경로
        result: extract_blocks 결과
        save_path: 저장할 경로 (None이면 화면에 표시)
    """
    # 이미지 로드
    image = cv2.imread(image_path)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # 플롯 설정
    fig, ax = plt.subplots(1, 1, figsize=(15, 10))
    ax.imshow(image_rgb)
    ax.set_title(f"Document Blocks Detection ({len(result['blocks'])} blocks)", fontsize=16)

    # 타입별 색상 정의
    colors = {
        'title': 'red',
        'paragraph': 'blue',
        'table': 'green',
        'list': 'orange',
        'other': 'purple'
    }

    # 블록 시각화
    for block in result['blocks']:
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

    # 범례 추가
    legend_elements = [
        patches.Patch(color=color, label=block_type.title())
        for block_type, color in colors.items()
    ]
    ax.legend(handles=legend_elements, loc='upper right')

    ax.axis('off')
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"시각화 결과 저장: {save_path}")
    else:
        plt.show()

    plt.close()


__all__ = ['visualize_blocks']
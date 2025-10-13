#!/usr/bin/env python3
"""
Save visualization plots to files
"""

import cv2
import matplotlib.pyplot as plt
import matplotlib
from .rendering import draw_bounding_boxes
from .legend import create_legend

# 한글 폰트 설정
matplotlib.rcParams['font.family'] = ['Noto Sans CJK JP', 'DejaVu Sans', 'sans-serif']
matplotlib.rcParams['axes.unicode_minus'] = False


def save_visualization(image_path, blocks, save_path, title=None):
    """
    블록 시각화 이미지를 저장

    Args:
        image_path: 원본 이미지 경로
        blocks: 블록 정보 리스트
        save_path: 저장할 경로
        title: 플롯 제목 (기본값: 자동 생성)

    Returns:
        None
    """
    # 이미지 로드
    image = cv2.imread(image_path)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # 플롯 설정
    fig, ax = plt.subplots(1, 1, figsize=(15, 10))
    ax.imshow(image_rgb)

    # 제목 설정 (한글)
    if title is None:
        title = f"문서 블록 감지 ({len(blocks)}개 블록)"
    ax.set_title(title, fontsize=16)

    # 바운딩 박스 그리기
    draw_bounding_boxes(ax, blocks)

    # 범례 추가
    create_legend(ax)

    ax.axis('off')
    plt.tight_layout()

    # 저장
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"시각화 결과 저장: {save_path}")

    plt.close()


__all__ = ['save_visualization']
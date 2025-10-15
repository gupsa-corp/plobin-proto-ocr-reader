#!/usr/bin/env python3
"""
Visualize extracted text blocks
"""

import cv2
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib
import matplotlib.font_manager as fm
from typing import Dict, Optional

# 한글 폰트 찾기 (시스템에서 사용 가능한 한글 폰트)
def get_korean_font():
    """시스템에서 사용 가능한 한글 폰트를 찾아 반환"""
    korean_fonts = [
        'NanumGothic', 'NanumBarunGothic', 'NanumMyeongjo',
        'AppleSDGothicNeoR00', 'AppleSDGothicNeoM00', 'AppleSDGothicNeoB00',
        'AppleGothic', 'Apple SD Gothic Neo', 'AppleSDGothicNeo-Regular',
        'Noto Sans CJK KR', 'Malgun Gothic', 'Dotum', 'Gulim'
    ]

    for font_name in korean_fonts:
        try:
            font_path = fm.findfont(fm.FontProperties(family=font_name))
            if font_path and 'DejaVu' not in font_path:
                print(f"✅ 한글 폰트 사용: {font_name} ({font_path})")
                return fm.FontProperties(fname=font_path)
        except:
            continue

    # 폴백: 기본 폰트
    print("⚠️ 한글 폰트를 찾을 수 없어 기본 폰트를 사용합니다.")
    return fm.FontProperties()

# 한글 폰트 설정
korean_font = get_korean_font()
matplotlib.rcParams['axes.unicode_minus'] = False

# matplotlib 전역 폰트 설정
try:
    # Nanum 폰트가 있으면 전역으로 설정
    available_fonts = [f.name for f in fm.fontManager.ttflist]
    if 'NanumGothic' in available_fonts:
        matplotlib.rcParams['font.family'] = 'NanumGothic'
        print("✅ matplotlib 전역 폰트 설정: NanumGothic")
    elif 'NanumBarunGothic' in available_fonts:
        matplotlib.rcParams['font.family'] = 'NanumBarunGothic'
        print("✅ matplotlib 전역 폰트 설정: NanumBarunGothic")
except Exception as e:
    print(f"⚠️ 전역 폰트 설정 실패: {e}")


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
    ax.set_title(f"문서 블록 감지 ({len(result['blocks'])}개 블록)", fontsize=16, fontproperties=korean_font)

    # 타입별 색상 정의 (한글)
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

        # 텍스트 라벨 추가 (한글)
        korean_type = type_names.get(block_type, block_type)
        label = f"{korean_type}\n{confidence:.2f}"
        ax.text(
            bbox['x_min'],
            bbox['y_min'] - 5,
            label,
            fontsize=8,
            fontproperties=korean_font,
            color=colors.get(block_type, 'gray'),
            bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8)
        )

    # 범례 추가 (한글)
    legend_elements = [
        patches.Patch(color=color, label=type_names.get(block_type, block_type))
        for block_type, color in colors.items()
    ]
    ax.legend(handles=legend_elements, loc='upper right', prop=korean_font)

    ax.axis('off')
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"시각화 결과 저장: {save_path}")
    else:
        plt.show()

    plt.close()


__all__ = ['visualize_blocks']
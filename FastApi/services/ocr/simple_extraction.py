#!/usr/bin/env python3
"""
Simple OCR extraction following blog.tinstack.net approach
블로그 방식의 간단한 OCR 추출
"""

import os
import numpy as np
from typing import Dict, List
from PIL import Image, ImageDraw, ImageFont


def extract_text_simple(ocr_instance, image_path: str, confidence_threshold: float = 0.3) -> Dict:
    """
    간단한 PaddleOCR 텍스트 추출 (블로그 방식)

    Args:
        ocr_instance: PaddleOCR 인스턴스
        image_path: 이미지 파일 경로
        confidence_threshold: 신뢰도 임계값

    Returns:
        추출된 텍스트 블록 정보
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")

    print(f"OCR 처리 중: {image_path}")

    # PaddleOCR 실행 (간단하게!)
    result = ocr_instance.ocr(image_path, cls=True)

    # 결과 파싱
    blocks = []
    if result and result[0]:
        print(f"✅ 감지된 텍스트: {len(result[0])}개")

        for idx, detection in enumerate(result[0]):
            bbox, (text, confidence) = detection

            # 신뢰도 필터링
            if confidence < confidence_threshold:
                continue

            # bbox를 numpy 배열로 변환
            bbox = np.array(bbox, dtype=np.int32)

            # 좌표 계산
            x_min = int(np.min(bbox[:, 0]))
            y_min = int(np.min(bbox[:, 1]))
            x_max = int(np.max(bbox[:, 0]))
            y_max = int(np.max(bbox[:, 1]))

            block_info = {
                'id': idx + 1,
                'text': text,
                'confidence': float(confidence),
                'bbox': {
                    'x_min': x_min,
                    'y_min': y_min,
                    'x_max': x_max,
                    'y_max': y_max,
                    'width': x_max - x_min,
                    'height': y_max - y_min
                },
                'bbox_points': bbox.tolist(),
                'type': 'text'
            }
            blocks.append(block_info)

    print(f"✅ 최종 블록: {len(blocks)}개 (신뢰도 >={confidence_threshold})")

    # 이미지 정보
    image = Image.open(image_path)
    width, height = image.size

    return {
        'image_info': {
            'path': image_path,
            'width': width,
            'height': height,
            'total_blocks': len(blocks)
        },
        'blocks': blocks,
        'processing_info': {
            'confidence_threshold': confidence_threshold,
            'language': 'korean'
        }
    }


def visualize_with_pil(image_path: str, result: Dict, save_path: str = None,
                       font_path: str = None, font_size: int = 12) -> Image.Image:
    """
    PIL을 사용한 간단한 시각화 (블로그 방식)

    Args:
        image_path: 원본 이미지 경로
        result: extract_text_simple 결과
        save_path: 저장 경로 (None이면 저장 안 함)
        font_path: 폰트 파일 경로 (None이면 시스템 기본 폰트)
        font_size: 폰트 크기

    Returns:
        시각화된 PIL Image
    """
    # 이미지 로드
    image = Image.open(image_path)
    if image.mode != 'RGB':
        image = image.convert('RGB')

    # Draw 객체 생성
    draw = ImageDraw.Draw(image)

    # 한글 폰트 로드
    try:
        if font_path and os.path.exists(font_path):
            font = ImageFont.truetype(font_path, font_size)
        else:
            # macOS 기본 한글 폰트 시도
            korean_fonts = [
                '/System/Library/Fonts/AppleSDGothicNeo.ttc',
                '/System/Library/Fonts/AppleGothic.ttf',
                '/Library/Fonts/NanumGothic.ttf'
            ]
            font = None
            for font_candidate in korean_fonts:
                if os.path.exists(font_candidate):
                    font = ImageFont.truetype(font_candidate, font_size)
                    break

            if font is None:
                # 폴백: 기본 폰트
                font = ImageFont.load_default()
                print("⚠️ 한글 폰트를 찾을 수 없어 기본 폰트를 사용합니다")
    except Exception as e:
        print(f"⚠️ 폰트 로드 실패: {e}, 기본 폰트 사용")
        font = ImageFont.load_default()

    # 블록 그리기
    blocks = result.get('blocks', [])
    for block in blocks:
        bbox_points = block['bbox_points']
        text = block['text']
        confidence = block['confidence']

        # 바운딩 박스 그리기 (빨간색, 두께 3)
        draw.polygon([tuple(point) for point in bbox_points],
                     outline='red', width=3)

        # 텍스트 라벨 그리기 (초록색)
        x, y = bbox_points[0]
        label = f"{text} ({confidence:.2f})"
        draw.text((x, y - 15), label, font=font, fill=(0, 255, 0))

    # 제목 추가
    title = f"OCR 결과: {len(blocks)}개 블록"
    draw.text((10, 10), title, font=font, fill=(255, 0, 0))

    # 저장
    if save_path:
        image.save(save_path)
        print(f"✅ 시각화 저장: {save_path}")

    return image


__all__ = ['extract_text_simple', 'visualize_with_pil']

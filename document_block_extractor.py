#!/usr/bin/env python3
"""
Document Block Extractor using PaddleOCR
RTX 3090 GPU 가속 지원
"""

import os
import cv2
import numpy as np
import json
from typing import List, Dict, Tuple, Optional
from paddleocr import PaddleOCR
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib import font_manager
import argparse


class DocumentBlockExtractor:
    """PaddleOCR을 사용한 문서 블록 추출기"""

    def __init__(self, use_gpu: bool = True, lang: str = 'korean'):
        """
        초기화

        Args:
            use_gpu: GPU 사용 여부 (RTX 3090 활용)
            lang: 인식 언어 ('korean', 'en', 'ch' 등)
        """
        self.lang = lang
        self.use_gpu = use_gpu

        # PaddleOCR 초기화 (간단한 설정으로 시작)
        try:
            # 먼저 기본 설정으로 시도
            self.ocr = PaddleOCR(lang=lang)
            print(f"PaddleOCR 초기화 완료 - 언어: {lang}")

            # GPU 사용 여부는 PaddlePaddle 환경에 따라 자동 결정됨
            if use_gpu:
                print("GPU 가속 활성화 시도 (PaddlePaddle 환경에 따라 자동 결정)")
            else:
                print("CPU 모드로 실행")

        except Exception as e:
            print(f"PaddleOCR 초기화 실패: {e}")
            # 영어로 폴백 시도
            try:
                print("영어 모드로 재시도...")
                self.ocr = PaddleOCR(lang='en')
                print("영어 모드로 PaddleOCR 초기화 완료")
            except Exception as e2:
                print(f"영어 모드 초기화도 실패: {e2}")
                raise e

    def extract_blocks(self, image_path: str, confidence_threshold: float = 0.5) -> Dict:
        """
        이미지에서 문서 블록 추출

        Args:
            image_path: 이미지 파일 경로
            confidence_threshold: 신뢰도 임계값

        Returns:
            블록 정보가 포함된 딕셔너리
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")

        # 이미지 읽기
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"이미지를 읽을 수 없습니다: {image_path}")

        # PaddleOCR 실행
        print("OCR 처리 중...")
        result = self.ocr.ocr(image_path, cls=True)

        # 결과 파싱
        blocks = []
        if result and result[0]:
            for idx, detection in enumerate(result[0]):
                bbox, (text, confidence) = detection

                # 신뢰도 필터링
                if confidence < confidence_threshold:
                    continue

                # 바운딩 박스 좌표 정규화
                bbox = np.array(bbox).astype(int)
                x_min = int(np.min(bbox[:, 0]))
                y_min = int(np.min(bbox[:, 1]))
                x_max = int(np.max(bbox[:, 0]))
                y_max = int(np.max(bbox[:, 1]))

                # 블록 분류 (간단한 휴리스틱)
                block_type = self._classify_block(text, bbox, image.shape)

                block_info = {
                    'id': idx,
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
                    'type': block_type,
                    'area': (x_max - x_min) * (y_max - y_min)
                }
                blocks.append(block_info)

        # 이미지 정보
        height, width = image.shape[:2]

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
                'gpu_used': self.use_gpu,
                'language': self.lang
            }
        }

    def _classify_block(self, text: str, bbox: np.ndarray, image_shape: Tuple) -> str:
        """
        텍스트 블록 분류 (간단한 휴리스틱)

        Args:
            text: 추출된 텍스트
            bbox: 바운딩 박스 좌표
            image_shape: 이미지 크기 (height, width, channels)

        Returns:
            블록 타입 ('title', 'paragraph', 'table', 'list', 'other')
        """
        # 크기 기반 분류
        width = np.max(bbox[:, 0]) - np.min(bbox[:, 0])
        height = np.max(bbox[:, 1]) - np.min(bbox[:, 1])

        # 이미지 대비 크기 비율
        width_ratio = width / image_shape[1]
        height_ratio = height / image_shape[0]

        # 텍스트 길이
        text_length = len(text.strip())

        # 분류 규칙
        if height_ratio > 0.05 and text_length < 50:
            return 'title'
        elif width_ratio > 0.7 and text_length > 100:
            return 'paragraph'
        elif '|' in text or '\t' in text:
            return 'table'
        elif text.strip().startswith(('•', '-', '1.', '2.', '3.')):
            return 'list'
        else:
            return 'other'

    def visualize_blocks(self, image_path: str, result: Dict, save_path: Optional[str] = None):
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

    def save_results(self, result: Dict, output_path: str):
        """
        결과를 JSON 파일로 저장

        Args:
            result: extract_blocks 결과
            output_path: 저장할 JSON 파일 경로
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"결과 저장 완료: {output_path}")

    def get_summary(self, result: Dict) -> Dict:
        """
        추출 결과 요약

        Args:
            result: extract_blocks 결과

        Returns:
            요약 정보
        """
        blocks = result['blocks']

        # 타입별 통계
        type_counts = {}
        total_confidence = 0

        for block in blocks:
            block_type = block['type']
            type_counts[block_type] = type_counts.get(block_type, 0) + 1
            total_confidence += block['confidence']

        avg_confidence = total_confidence / len(blocks) if blocks else 0

        return {
            'total_blocks': len(blocks),
            'average_confidence': avg_confidence,
            'block_types': type_counts,
            'image_dimensions': f"{result['image_info']['width']}x{result['image_info']['height']}",
            'gpu_used': result['processing_info']['gpu_used']
        }


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description='PaddleOCR Document Block Extractor')
    parser.add_argument('--image', '-i', required=True, help='입력 이미지 경로')
    parser.add_argument('--output', '-o', help='출력 디렉토리 (기본: ./output)')
    parser.add_argument('--confidence', '-c', type=float, default=0.5,
                       help='신뢰도 임계값 (기본: 0.5)')
    parser.add_argument('--lang', '-l', default='korean',
                       help='인식 언어 (기본: korean)')
    parser.add_argument('--no-gpu', action='store_true',
                       help='GPU 사용 안함')
    parser.add_argument('--visualize', '-v', action='store_true',
                       help='결과 시각화')

    args = parser.parse_args()

    # 출력 디렉토리 설정
    output_dir = args.output or './output'
    os.makedirs(output_dir, exist_ok=True)

    # 추출기 초기화
    extractor = DocumentBlockExtractor(
        use_gpu=not args.no_gpu,
        lang=args.lang
    )

    try:
        # 블록 추출
        print(f"이미지 처리 시작: {args.image}")
        result = extractor.extract_blocks(args.image, args.confidence)

        # 결과 요약 출력
        summary = extractor.get_summary(result)
        print("\n=== 추출 결과 요약 ===")
        print(f"총 블록 수: {summary['total_blocks']}")
        print(f"평균 신뢰도: {summary['average_confidence']:.3f}")
        print(f"이미지 크기: {summary['image_dimensions']}")
        print(f"GPU 사용: {summary['gpu_used']}")
        print("블록 타입별 개수:")
        for block_type, count in summary['block_types'].items():
            print(f"  {block_type}: {count}")

        # 결과 저장
        base_name = os.path.splitext(os.path.basename(args.image))[0]
        json_path = os.path.join(output_dir, f"{base_name}_blocks.json")
        extractor.save_results(result, json_path)

        # 시각화
        if args.visualize:
            viz_path = os.path.join(output_dir, f"{base_name}_visualization.png")
            extractor.visualize_blocks(args.image, result, viz_path)

        print(f"\n처리 완료! 결과는 {output_dir}에 저장되었습니다.")

    except Exception as e:
        print(f"오류 발생: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
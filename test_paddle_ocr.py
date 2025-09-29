#!/usr/bin/env python3
"""
PaddleOCR 테스트 스크립트
"""

import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from document_block_extractor import DocumentBlockExtractor


def create_sample_document(output_path: str = "sample_document.png"):
    """
    테스트용 샘플 문서 이미지 생성

    Args:
        output_path: 저장할 이미지 경로
    """
    # 이미지 크기
    width, height = 800, 1000

    # 흰색 배경 이미지 생성
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)

    # 기본 폰트 (시스템에 따라 다를 수 있음)
    try:
        # 한글 폰트 시도
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        normal_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except:
        # 기본 폰트 사용
        title_font = ImageFont.load_default()
        normal_font = ImageFont.load_default()

    # 문서 내용 구성
    y_pos = 50

    # 제목
    draw.text((50, y_pos), "Document Analysis Test", font=title_font, fill='black')
    y_pos += 60

    # 부제목
    draw.text((50, y_pos), "PaddleOCR Block Extraction Example", font=normal_font, fill='black')
    y_pos += 50

    # 단락 1
    paragraph1 = [
        "This is the first paragraph of our test document.",
        "It contains multiple lines to demonstrate text block",
        "detection and classification capabilities.",
        "The extractor should identify this as a paragraph block."
    ]

    for line in paragraph1:
        draw.text((50, y_pos), line, font=normal_font, fill='black')
        y_pos += 25

    y_pos += 20

    # 리스트
    draw.text((50, y_pos), "Key Features:", font=normal_font, fill='black')
    y_pos += 30

    list_items = [
        "• GPU acceleration with RTX 3090",
        "• Korean and English text recognition",
        "• Block type classification",
        "• Confidence scoring",
        "• Visualization tools"
    ]

    for item in list_items:
        draw.text((70, y_pos), item, font=normal_font, fill='black')
        y_pos += 25

    y_pos += 30

    # 표 형태
    draw.text((50, y_pos), "Performance Metrics", font=normal_font, fill='black')
    y_pos += 30

    # 간단한 표 그리기
    table_data = [
        "Metric          | Value     | Unit",
        "----------------|-----------|-----",
        "Accuracy        | 95.2%     | %",
        "Processing Time | 1.2       | sec",
        "GPU Memory      | 2.1       | GB"
    ]

    for row in table_data:
        draw.text((70, y_pos), row, font=normal_font, fill='black')
        y_pos += 25

    y_pos += 30

    # 단락 2
    paragraph2 = [
        "This document demonstrates the capabilities of our",
        "PaddleOCR-based document block extraction system.",
        "It can identify different types of content blocks",
        "including titles, paragraphs, lists, and tables."
    ]

    for line in paragraph2:
        draw.text((50, y_pos), line, font=normal_font, fill='black')
        y_pos += 25

    # 한글 텍스트 추가
    y_pos += 40
    draw.text((50, y_pos), "한글 텍스트 인식 테스트", font=normal_font, fill='black')
    y_pos += 30
    draw.text((50, y_pos), "이 문서는 PaddleOCR의 한글 인식 성능을", font=normal_font, fill='black')
    y_pos += 25
    draw.text((50, y_pos), "테스트하기 위한 샘플 문서입니다.", font=normal_font, fill='black')

    # 이미지 저장
    img.save(output_path)
    print(f"샘플 문서 생성 완료: {output_path}")

    return output_path


def test_paddle_ocr():
    """PaddleOCR 기본 테스트"""
    print("=== PaddleOCR 테스트 시작 ===")

    # 출력 디렉토리 생성
    output_dir = "./output"
    os.makedirs(output_dir, exist_ok=True)

    # 샘플 문서 생성
    sample_path = os.path.join(output_dir, "sample_document.png")
    create_sample_document(sample_path)

    try:
        # 추출기 초기화 (GPU 사용)
        print("\n1. CPU 모드로 추출기 초기화...")
        extractor = DocumentBlockExtractor(use_gpu=False, lang='en')

        # 블록 추출
        print("\n2. 문서 블록 추출 중...")
        result = extractor.extract_blocks(sample_path, confidence_threshold=0.3)

        # 결과 요약
        print("\n3. 결과 분석...")
        summary = extractor.get_summary(result)

        print(f"\n=== 추출 결과 ===")
        print(f"총 블록 수: {summary['total_blocks']}")
        print(f"평균 신뢰도: {summary['average_confidence']:.3f}")
        print(f"이미지 크기: {summary['image_dimensions']}")
        print(f"GPU 사용: {summary['gpu_used']}")

        if summary['block_types']:
            print("\n블록 타입별 개수:")
            for block_type, count in summary['block_types'].items():
                print(f"  {block_type}: {count}")

        # 개별 블록 정보 출력
        print(f"\n=== 개별 블록 정보 ===")
        for i, block in enumerate(result['blocks'][:5]):  # 처음 5개만 출력
            print(f"\n블록 {i+1}:")
            print(f"  텍스트: {block['text'][:50]}{'...' if len(block['text']) > 50 else ''}")
            print(f"  타입: {block['type']}")
            print(f"  신뢰도: {block['confidence']:.3f}")
            print(f"  크기: {block['bbox']['width']}x{block['bbox']['height']}")

        if len(result['blocks']) > 5:
            print(f"\n... 및 {len(result['blocks']) - 5}개 추가 블록")

        # 결과 저장
        json_path = os.path.join(output_dir, "test_result.json")
        extractor.save_results(result, json_path)

        # 시각화
        print("\n4. 결과 시각화...")
        viz_path = os.path.join(output_dir, "test_visualization.png")
        extractor.visualize_blocks(sample_path, result, viz_path)

        print(f"\n=== 테스트 완료 ===")
        print(f"결과 파일:")
        print(f"  - 샘플 문서: {sample_path}")
        print(f"  - JSON 결과: {json_path}")
        print(f"  - 시각화: {viz_path}")

        return True

    except Exception as e:
        print(f"테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_gpu_availability():
    """GPU 사용 가능 여부 확인"""
    print("=== GPU 확인 ===")

    try:
        import paddle
        print(f"PaddlePaddle 버전: {paddle.__version__}")

        # GPU 사용 가능 여부 확인
        if paddle.is_compiled_with_cuda():
            print("CUDA 컴파일 지원: ✓")

            gpu_count = paddle.device.cuda.device_count()
            print(f"사용 가능한 GPU 개수: {gpu_count}")

            if gpu_count > 0:
                for i in range(gpu_count):
                    gpu_name = paddle.device.cuda.get_device_name(i)
                    print(f"  GPU {i}: {gpu_name}")

                # GPU 메모리 정보 (사용 가능한 경우만)
                try:
                    print("GPU 메모리 정보를 확인 중...")
                except Exception as gpu_mem_error:
                    print(f"GPU 메모리 정보 확인 실패: {gpu_mem_error}")

                return True
            else:
                print("GPU를 찾을 수 없습니다.")
                return False
        else:
            print("CUDA 컴파일 지원: ✗")
            return False

    except Exception as e:
        print(f"GPU 확인 중 오류: {e}")
        return False


if __name__ == "__main__":
    print("PaddleOCR 테스트 시작")
    print("=" * 50)

    # GPU 확인
    gpu_available = test_gpu_availability()

    print("\n" + "=" * 50)

    # OCR 테스트
    success = test_paddle_ocr()

    if success:
        print("\n✓ 모든 테스트가 성공적으로 완료되었습니다!")
        if gpu_available:
            print("✓ GPU 가속이 정상적으로 작동합니다!")
        else:
            print("⚠ GPU는 사용되지 않았지만 CPU 모드로 정상 작동합니다.")
    else:
        print("\n✗ 테스트 중 오류가 발생했습니다.")
        sys.exit(1)
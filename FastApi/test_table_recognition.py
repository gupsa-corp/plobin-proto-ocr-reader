#!/usr/bin/env python3
"""
표 인식 기능 테스트 스크립트
"""

import sys
import os
sys.path.append('.')

from services.ocr.table_recognition import create_table_recognizer
from services.ocr.extraction import extract_blocks_with_layout_analysis
from services.ocr.initialization import initialize_ocr
import json
from pathlib import Path


def test_table_recognition():
    """표 인식 기능 테스트"""

    # 테스트 이미지 찾기
    test_images = [
        "demo/processed/business/images/sample_business_report_page_004.png",
        "demo/processed/manuals/images/technical_manual_page_001.png",
        "demo/processed/academic/images/sample_research_paper_page_001.png"
    ]

    print("=== 표 인식 기능 테스트 시작 ===\n")

    # OCR 인스턴스 초기화
    print("1. OCR 인스턴스 초기화...")
    ocr = initialize_ocr(use_gpu=False, lang='korean', enable_layout_analysis=True)

    # 표 인식기 초기화
    print("2. 표 인식기 초기화...")
    table_recognizer = create_table_recognizer(lang='korean', use_gpu=False)

    for i, image_path in enumerate(test_images):
        if not os.path.exists(image_path):
            print(f"이미지 없음: {image_path}")
            continue

        print(f"\n--- 테스트 {i+1}: {Path(image_path).name} ---")

        try:
            # 1. 기본 표 감지 테스트
            print("표 감지 중...")
            tables = table_recognizer.detect_tables(image_path)
            print(f"감지된 표: {len(tables)}개")

            if tables:
                for j, table in enumerate(tables):
                    print(f"  표 {j+1}: 신뢰도 {table.get('confidence', 0):.2f}, "
                          f"크기 {table.get('rows', 0)}x{table.get('columns', 0)}")

            # 2. 레이아웃 분석 테스트
            print("레이아웃 분석 중...")
            layout = table_recognizer.analyze_layout(image_path)
            summary = layout.get('summary', {})
            print(f"레이아웃 요소: 표 {summary.get('total_tables', 0)}개, "
                  f"제목 {summary.get('total_titles', 0)}개, "
                  f"단락 {summary.get('total_paragraphs', 0)}개")

            # 3. 통합 추출 테스트
            print("통합 블록 추출 중...")
            result = extract_blocks_with_layout_analysis(
                ocr, image_path,
                enable_table_recognition=True
            )

            blocks = result.get('blocks', [])
            layout_info = result.get('layout_info', {})

            print(f"전체 블록: {len(blocks)}개")

            # 타입별 블록 수 계산
            type_counts = {}
            for block in blocks:
                block_type = block.get('type', 'other')
                type_counts[block_type] = type_counts.get(block_type, 0) + 1

            print("블록 타입별 분포:")
            for block_type, count in type_counts.items():
                print(f"  {block_type}: {count}개")

            # 표 상세 정보
            tables_info = layout_info.get('tables', [])
            if tables_info:
                print(f"표 상세 정보: {len(tables_info)}개")
                for j, table in enumerate(tables_info):
                    cells = table.get('cells', [])
                    print(f"  표 {j+1}: {len(cells)}개 셀")

        except Exception as e:
            print(f"오류 발생: {e}")
            import traceback
            traceback.print_exc()

    print("\n=== 표 인식 기능 테스트 완료 ===")


def test_simple_table_detection():
    """간단한 표 감지 테스트"""
    print("=== 간단한 표 감지 테스트 ===")

    # 기존 처리된 파일 중에서 테스트
    test_image = "output/01999bb4-6117-4479-b535-550a2ef15fd2/pages/001/original.png"

    if not os.path.exists(test_image):
        print("테스트 이미지를 찾을 수 없습니다.")
        return

    try:
        table_recognizer = create_table_recognizer(lang='korean', use_gpu=False)

        print(f"테스트 이미지: {test_image}")
        tables = table_recognizer.detect_tables(test_image)

        print(f"감지된 표: {len(tables)}개")

        for i, table in enumerate(tables):
            print(f"표 {i+1}:")
            print(f"  - 신뢰도: {table.get('confidence', 0):.3f}")
            print(f"  - 위치: {table.get('bbox', [])}")
            print(f"  - 크기: {table.get('rows', 0)}행 x {table.get('columns', 0)}열")
            print(f"  - 셀 개수: {len(table.get('cells', []))}")

            # HTML 구조가 있으면 출력
            html = table.get('html_structure', '')
            if html:
                print(f"  - HTML 구조: {html[:100]}...")

    except Exception as e:
        print(f"오류: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 간단한 테스트부터 시작
    test_simple_table_detection()

    print("\n" + "="*50 + "\n")

    # 전체 테스트
    test_table_recognition()
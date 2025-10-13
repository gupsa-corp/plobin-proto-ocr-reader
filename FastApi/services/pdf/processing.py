#!/usr/bin/env python3
"""
Process PDF with OCR extraction
"""

import json
from pathlib import Path
from .conversion import pdf_to_images
from services.ocr import DocumentBlockExtractor


def process_pdf_with_ocr(pdf_path, output_dir="demo/processed", confidence_threshold=0.5):
    """
    PDF를 이미지로 변환하고 OCR 처리

    Args:
        pdf_path: PDF 파일 경로
        output_dir: 결과 저장 디렉토리
        confidence_threshold: OCR 신뢰도 임계값

    Returns:
        처리 결과 딕셔너리
    """
    print(f"🔍 PDF 처리 시작: {pdf_path}")

    # 출력 디렉토리 생성
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 이미지 변환 디렉토리
    images_dir = output_path / "images"
    images_dir.mkdir(exist_ok=True)

    try:
        # 1. PDF를 이미지로 변환
        print("🖼️  PDF를 이미지로 변환 중...")
        image_paths = pdf_to_images(pdf_path, images_dir)

        if not image_paths:
            print("❌ 이미지 변환 실패")
            return None

        # 2. OCR 초기화
        print("🤖 PaddleOCR 초기화 중...")
        extractor = DocumentBlockExtractor(use_gpu=False, lang='en')

        # 3. 각 페이지별 OCR 처리
        pdf_name = Path(pdf_path).stem
        all_results = {
            'pdf_file': pdf_path,
            'total_pages': len(image_paths),
            'pages': [],
            'summary': {
                'total_blocks': 0,
                'average_confidence': 0,
                'block_types': {}
            }
        }

        total_blocks = 0
        total_confidence_sum = 0
        block_type_counts = {}

        for i, image_path in enumerate(image_paths):
            print(f"📖 페이지 {i+1}/{len(image_paths)} 처리 중...")

            try:
                # OCR 실행
                result = extractor.extract_blocks(image_path, confidence_threshold)

                # 페이지 결과 저장
                page_result = {
                    'page_number': i + 1,
                    'image_path': image_path,
                    'blocks': result['blocks'],
                    'block_count': len(result['blocks'])
                }

                all_results['pages'].append(page_result)

                # 통계 업데이트
                total_blocks += len(result['blocks'])
                for block in result['blocks']:
                    total_confidence_sum += block['confidence']
                    block_type = block['type']
                    block_type_counts[block_type] = block_type_counts.get(block_type, 0) + 1

                print(f"   ✅ 페이지 {i+1}: {len(result['blocks'])}개 블록 추출")

                # 페이지별 시각화 (선택적)
                viz_path = output_path / f"{pdf_name}_page_{i+1:03d}_visualization.png"
                extractor.visualize_blocks(image_path, result, str(viz_path))

            except Exception as e:
                print(f"   ❌ 페이지 {i+1} 처리 실패: {e}")
                continue

        # 4. 전체 요약 계산
        if total_blocks > 0:
            all_results['summary']['total_blocks'] = total_blocks
            all_results['summary']['average_confidence'] = total_confidence_sum / total_blocks
            all_results['summary']['block_types'] = block_type_counts

        # 5. 결과 저장
        result_json_path = output_path / f"{pdf_name}_ocr_results.json"
        with open(result_json_path, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)

        print(f"\n📊 PDF 처리 완료:")
        print(f"   📁 PDF: {pdf_name}")
        print(f"   📄 총 페이지: {len(image_paths)}")
        print(f"   🔍 총 블록: {total_blocks}")
        if total_blocks > 0:
            print(f"   🎯 평균 신뢰도: {all_results['summary']['average_confidence']:.1%}")
            print(f"   📋 결과 파일: {result_json_path}")

        return all_results

    except Exception as e:
        print(f"❌ PDF 처리 중 오류 발생: {e}")
        return None


__all__ = ['process_pdf_with_ocr']
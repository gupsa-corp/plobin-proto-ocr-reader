#!/usr/bin/env python3
"""
PDF를 이미지로 변환하고 PaddleOCR로 블록 추출하는 스크립트
"""

import os
import json
from pathlib import Path
import sys

try:
    import fitz  # PyMuPDF
except ImportError:
    print("❌ PyMuPDF가 설치되지 않았습니다.")
    print("다음 명령어로 설치하세요: pip install PyMuPDF")
    sys.exit(1)

from document_block_extractor import DocumentBlockExtractor


class PDFToImageProcessor:
    """PDF를 이미지로 변환하는 클래스"""

    def __init__(self, dpi=150):
        self.dpi = dpi

    def convert_pdf_to_images(self, pdf_path, output_dir):
        """
        PDF를 페이지별 이미지로 변환

        Args:
            pdf_path: PDF 파일 경로
            output_dir: 이미지 저장 디렉토리

        Returns:
            변환된 이미지 파일 경로 리스트
        """
        return pdf_to_images(pdf_path, output_dir, self.dpi)


def pdf_to_images(pdf_path, output_dir, dpi=150):
    """
    PDF를 페이지별 이미지로 변환

    Args:
        pdf_path: PDF 파일 경로
        output_dir: 이미지 저장 디렉토리
        dpi: 이미지 해상도

    Returns:
        변환된 이미지 파일 경로 리스트
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # PDF 열기
    doc = fitz.open(pdf_path)
    image_paths = []

    pdf_name = Path(pdf_path).stem

    print(f"📄 PDF '{pdf_name}' 변환 중... ({len(doc)} 페이지)")

    for page_num in range(len(doc)):
        # 페이지 가져오기
        page = doc[page_num]

        # 이미지로 변환 (DPI 설정)
        mat = fitz.Matrix(dpi/72, dpi/72)  # 72 DPI가 기본값
        pix = page.get_pixmap(matrix=mat)

        # 이미지 파일명
        image_filename = f"{pdf_name}_page_{page_num + 1:03d}.png"
        image_path = output_dir / image_filename

        # 이미지 저장
        pix.save(str(image_path))
        image_paths.append(str(image_path))

        print(f"   ✅ 페이지 {page_num + 1}/{len(doc)} 변환 완료: {image_filename}")

    doc.close()
    return image_paths


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


def process_demo_pdfs():
    """demo 폴더의 모든 PDF 파일 처리"""
    print("🚀 Demo PDF 파일들 일괄 처리 시작")
    print("=" * 60)

    demo_path = Path("demo")
    if not demo_path.exists():
        print("❌ demo 폴더가 존재하지 않습니다.")
        return

    # PDF 파일 찾기
    pdf_files = []
    for subdir in demo_path.iterdir():
        if subdir.is_dir():
            for pdf_file in subdir.glob("*.pdf"):
                pdf_files.append(pdf_file)

    if not pdf_files:
        print("❌ demo 폴더에서 PDF 파일을 찾을 수 없습니다.")
        return

    print(f"📁 발견된 PDF 파일: {len(pdf_files)}개")

    # 처리 결과 저장용
    all_results = {
        'processed_date': str(Path.cwd()),
        'total_pdfs': len(pdf_files),
        'results': []
    }

    # 각 PDF 처리
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"\n{'='*20} PDF {i}/{len(pdf_files)} {'='*20}")

        result = process_pdf_with_ocr(
            str(pdf_file),
            f"demo/processed/{pdf_file.parent.name}",
            confidence_threshold=0.3
        )

        if result:
            all_results['results'].append({
                'pdf_path': str(pdf_file),
                'category': pdf_file.parent.name,
                'summary': result['summary']
            })

    # 전체 결과 저장
    summary_path = Path("demo/processed/complete_analysis_summary.json")
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print(f"\n🎉 모든 PDF 처리 완료!")
    print(f"📋 전체 요약: {summary_path}")

    # 간단한 통계 출력
    total_blocks = sum(r['summary']['total_blocks'] for r in all_results['results'])
    avg_confidence = sum(r['summary']['average_confidence'] for r in all_results['results'] if r['summary']['total_blocks'] > 0) / len([r for r in all_results['results'] if r['summary']['total_blocks'] > 0])

    print(f"\n📊 전체 통계:")
    print(f"   📄 처리된 PDF: {len(all_results['results'])}개")
    print(f"   🔍 총 추출 블록: {total_blocks}개")
    print(f"   🎯 전체 평균 신뢰도: {avg_confidence:.1%}")


def main():
    """메인 실행 함수"""
    import argparse

    parser = argparse.ArgumentParser(description='PDF to Image OCR Processor')
    parser.add_argument('--pdf', '-p', help='특정 PDF 파일 처리')
    parser.add_argument('--all', '-a', action='store_true', help='demo 폴더의 모든 PDF 처리')
    parser.add_argument('--confidence', '-c', type=float, default=0.5, help='신뢰도 임계값')

    args = parser.parse_args()

    if args.pdf:
        # 특정 PDF 처리
        if not os.path.exists(args.pdf):
            print(f"❌ 파일을 찾을 수 없습니다: {args.pdf}")
            return

        result = process_pdf_with_ocr(args.pdf, confidence_threshold=args.confidence)
        if result:
            print(f"✅ 처리 완료: {args.pdf}")
    elif args.all:
        # 모든 demo PDF 처리
        process_demo_pdfs()
    else:
        print("사용법:")
        print("  특정 PDF 처리: python pdf_to_image_processor.py -p file.pdf")
        print("  모든 PDF 처리: python pdf_to_image_processor.py -a")


if __name__ == "__main__":
    main()
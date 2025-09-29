#!/usr/bin/env python3
"""
PaddleOCR 문서 블록 추출 사용 예제
"""

import os
from document_block_extractor import DocumentBlockExtractor


def main():
    """간단한 사용 예제"""
    print("🐼 PaddleOCR 문서 블록 추출 예제")
    print("=" * 50)

    # 이미지 파일 경로 (사용자가 지정)
    image_path = "./output/sample_document.png"

    # 출력 디렉토리 생성
    output_dir = "./results"
    os.makedirs(output_dir, exist_ok=True)

    try:
        # 1. 추출기 초기화
        print("📋 PaddleOCR 초기화 중...")
        extractor = DocumentBlockExtractor(
            use_gpu=False,  # CPU 모드 (CUDNN 문제로 인해)
            lang='en'       # 영어 모델 사용
        )

        # 2. 문서 블록 추출
        print(f"🔍 문서 분석 중: {image_path}")
        result = extractor.extract_blocks(
            image_path=image_path,
            confidence_threshold=0.5  # 신뢰도 임계값
        )

        # 3. 결과 요약
        summary = extractor.get_summary(result)
        print(f"\n✅ 분석 완료!")
        print(f"   📄 총 블록 수: {summary['total_blocks']}")
        print(f"   🎯 평균 신뢰도: {summary['average_confidence']:.1%}")
        print(f"   📐 이미지 크기: {summary['image_dimensions']}")

        # 블록 타입별 분포
        if summary['block_types']:
            print("\n📊 블록 타입 분포:")
            for block_type, count in summary['block_types'].items():
                print(f"   {block_type}: {count}개")

        # 4. 결과 저장
        base_name = os.path.splitext(os.path.basename(image_path))[0]

        # JSON 결과 저장
        json_path = os.path.join(output_dir, f"{base_name}_analysis.json")
        extractor.save_results(result, json_path)

        # 시각화 저장
        viz_path = os.path.join(output_dir, f"{base_name}_visualization.png")
        extractor.visualize_blocks(image_path, result, viz_path)

        print(f"\n💾 결과 파일:")
        print(f"   📄 JSON: {json_path}")
        print(f"   🖼️  시각화: {viz_path}")

        # 5. 몇 가지 블록 내용 미리보기
        print(f"\n📝 추출된 텍스트 미리보기:")
        for i, block in enumerate(result['blocks'][:3]):  # 처음 3개만
            confidence = block['confidence'] * 100
            text = block['text'][:50] + "..." if len(block['text']) > 50 else block['text']
            print(f"   {i+1}. [{confidence:.1f}%] {text}")

        if len(result['blocks']) > 3:
            print(f"   ... 및 {len(result['blocks']) - 3}개 추가 블록")

        print(f"\n🎉 모든 작업이 완료되었습니다!")

    except FileNotFoundError:
        print(f"❌ 오류: 이미지 파일을 찾을 수 없습니다: {image_path}")
        print("   먼저 test_paddle_ocr.py를 실행하여 샘플 이미지를 생성하세요.")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")


if __name__ == "__main__":
    main()
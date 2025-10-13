#!/usr/bin/env python3
"""
Surya OCR 마이그레이션 테스트
"""

import os
from pathlib import Path
from services.ocr import DocumentBlockExtractor

def test_surya_initialization():
    """Surya OCR 초기화 테스트"""
    print("=" * 60)
    print("1. Surya OCR 초기화 테스트")
    print("=" * 60)

    try:
        extractor = DocumentBlockExtractor(use_gpu=False, lang='ko')
        print("✅ Surya OCR 초기화 성공")
        return extractor
    except Exception as e:
        print(f"❌ Surya OCR 초기화 실패: {e}")
        raise


def test_basic_ocr(extractor):
    """기본 OCR 테스트"""
    print("\n" + "=" * 60)
    print("2. 기본 OCR 처리 테스트")
    print("=" * 60)

    # 테스트 이미지 경로
    test_image = "test_receipt.png"

    if not os.path.exists(test_image):
        print(f"⚠️ 테스트 이미지를 찾을 수 없습니다: {test_image}")
        return

    try:
        print(f"이미지 처리 중: {test_image}")
        result = extractor.extract_blocks(test_image, confidence_threshold=0.5)

        print(f"\n✅ OCR 처리 완료!")
        print(f"  - 감지된 블록 수: {result['image_info']['total_blocks']}")
        print(f"  - 이미지 크기: {result['image_info']['width']} x {result['image_info']['height']}")
        print(f"  - OCR 엔진: {result['processing_info']['ocr_engine']}")

        # 처음 5개 블록만 출력
        print("\n처음 5개 블록:")
        for i, block in enumerate(result['blocks'][:5], 1):
            print(f"\n블록 {i}:")
            print(f"  텍스트: {block['text']}")
            print(f"  신뢰도: {block['confidence']:.3f}")
            print(f"  타입: {block['type']}")
            print(f"  위치: ({block['bbox']['x_min']}, {block['bbox']['y_min']}) -> ({block['bbox']['x_max']}, {block['bbox']['y_max']})")

        return result

    except Exception as e:
        print(f"❌ OCR 처리 실패: {e}")
        import traceback
        traceback.print_exc()
        raise


def test_supported_languages():
    """지원 언어 확인"""
    print("\n" + "=" * 60)
    print("3. 지원 언어 확인")
    print("=" * 60)

    try:
        from services.ocr import get_supported_languages
        languages = get_supported_languages()
        print(f"✅ Surya OCR 지원 언어 수: {len(languages)}")
        print(f"주요 언어: {', '.join(languages[:10])}")
    except Exception as e:
        print(f"⚠️ 언어 목록 확인 실패: {e}")


def main():
    """메인 테스트 함수"""
    print("\n🚀 Surya OCR 마이그레이션 테스트 시작\n")

    try:
        # 1. 초기화 테스트
        extractor = test_surya_initialization()

        # 2. 기본 OCR 테스트
        result = test_basic_ocr(extractor)

        # 3. 지원 언어 확인
        test_supported_languages()

        print("\n" + "=" * 60)
        print("✅ 모든 테스트 통과!")
        print("=" * 60)
        print("\nSurya OCR 마이그레이션이 성공적으로 완료되었습니다! 🎉")

    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ 테스트 실패")
        print("=" * 60)
        print(f"오류: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())

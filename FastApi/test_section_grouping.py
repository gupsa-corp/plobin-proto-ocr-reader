#!/usr/bin/env python3
"""
섹션 그룹핑 기능 테스트
"""

import json
from services.ocr import DocumentBlockExtractor


def test_section_grouping():
    """섹션 그룹핑 테스트"""
    print("=" * 80)
    print("섹션 그룹핑 & 계층 구조 테스트")
    print("=" * 80)

    # OCR 초기화
    print("\n1. Surya OCR 초기화 중...")
    extractor = DocumentBlockExtractor(use_gpu=False, lang='ko')
    print("✅ 초기화 완료")

    # 테스트 이미지
    test_image = "test_korean_receipt.png"

    print(f"\n2. 이미지 처리 중: {test_image}")
    print("-" * 80)

    # 기본 블록 추출
    print("\n📄 [1단계] 기본 블록 추출 (평면 구조)")
    result_basic = extractor.extract_blocks(
        test_image,
        confidence_threshold=0.5,
        create_sections=False,
        build_hierarchy_tree=False
    )
    print(f"  ✅ 총 {result_basic['image_info']['total_blocks']}개 블록 추출")

    # 섹션 그룹핑
    print("\n📚 [2단계] 섹션 그룹핑 (논리적 섹션)")
    result_sections = extractor.extract_blocks(
        test_image,
        confidence_threshold=0.5,
        create_sections=True,
        build_hierarchy_tree=False
    )

    if 'sections' in result_sections:
        sections = result_sections['sections']
        print(f"  ✅ 총 {len(sections)}개 섹션 생성")

        # 섹션 타입별 통계
        section_summary = result_sections.get('section_summary', {})
        print(f"\n  📊 섹션 타입별 통계:")
        for section_type, count in section_summary.get('section_types', {}).items():
            print(f"    - {section_type}: {count}개")

        # 각 섹션 상세 정보
        print(f"\n  📋 섹션 상세 정보:")
        for i, section in enumerate(sections, 1):
            print(f"\n    섹션 {i} ({section.get('section_type', 'unknown')})")
            print(f"      블록 수: {section['total_blocks']}개")
            print(f"      평균 신뢰도: {section['avg_confidence']:.1%}")
            print(f"      텍스트 미리보기: {section['text'][:60]}...")
            print(f"      위치: ({section['bbox']['x_min']}, {section['bbox']['y_min']})")

    # 계층 구조
    print("\n🏗️  [3단계] 계층 구조 (포함 관계)")
    result_hierarchy = extractor.extract_blocks(
        test_image,
        confidence_threshold=0.5,
        create_sections=False,
        build_hierarchy_tree=True
    )

    if 'hierarchy_statistics' in result_hierarchy:
        stats = result_hierarchy['hierarchy_statistics']
        print(f"  ✅ 계층 구조 구축 완료")
        print(f"\n  📊 계층 구조 통계:")
        print(f"    - 총 블록 수: {stats['total_blocks']}개")
        print(f"    - 최상위 블록: {stats['root_blocks']}개")
        print(f"    - 최대 깊이: {stats['max_depth']}단계")
        print(f"    - 평균 자식 수: {stats['avg_children']}")
        print(f"\n    레벨별 블록 분포:")
        for level, count in stats['blocks_by_level'].items():
            print(f"      Level {level}: {count}개")

    # 통합 구조 (섹션 + 계층)
    print("\n🎯 [4단계] 통합 구조 (섹션 + 계층)")
    result_combined = extractor.extract_blocks(
        test_image,
        confidence_threshold=0.5,
        create_sections=True,
        build_hierarchy_tree=True
    )

    print(f"  ✅ 통합 구조 생성 완료")
    print(f"    - 평면 블록: {result_combined['image_info']['total_blocks']}개")
    if 'sections' in result_combined:
        print(f"    - 논리 섹션: {len(result_combined['sections'])}개")
    if 'hierarchy_statistics' in result_combined:
        print(f"    - 계층 깊이: {result_combined['hierarchy_statistics']['max_depth']}단계")

    # 결과를 JSON 파일로 저장
    output_file = "/tmp/section_grouping_result.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result_combined, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n💾 결과 저장: {output_file}")

    print("\n" + "=" * 80)
    print("✅ 모든 테스트 완료!")
    print("=" * 80)

    # 사용 예시 출력
    print("\n📖 사용 예시:")
    print("""
    # 기본 사용 (평면 구조)
    result = extractor.extract_blocks(image_path)

    # 섹션 그룹핑
    result = extractor.extract_blocks(image_path, create_sections=True)
    sections = result['sections']

    # 계층 구조
    result = extractor.extract_blocks(image_path, build_hierarchy_tree=True)
    hierarchy = result['hierarchical_blocks']

    # 통합 (섹션 + 계층)
    result = extractor.extract_blocks(
        image_path,
        create_sections=True,
        build_hierarchy_tree=True
    )
    """)


if __name__ == "__main__":
    test_section_grouping()

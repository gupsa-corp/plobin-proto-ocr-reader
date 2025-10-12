#!/usr/bin/env python3
"""
섹션 시각화 및 API 테스트 스크립트
"""

import requests
import json
from pathlib import Path
import time

# API 서버 설정
BASE_URL = "http://localhost:6003"

def test_sections_processing():
    """섹션 생성 및 시각화 테스트"""
    print("=" * 60)
    print("섹션 처리 테스트")
    print("=" * 60)

    # 테스트 이미지 찾기
    test_images = [
        "test_korean_receipt.png",
        "demo/images/sample.png",
        "demo/invoices/sample_invoice.pdf"
    ]

    test_file = None
    for img in test_images:
        if Path(img).exists():
            test_file = img
            break

    if not test_file:
        print("❌ 테스트 파일을 찾을 수 없습니다")
        return None

    print(f"✅ 테스트 파일: {test_file}")

    # 섹션 생성 활성화하여 문서 처리
    print("\n📤 문서 처리 중 (create_sections=True)...")
    with open(test_file, 'rb') as f:
        files = {'file': f}
        data = {
            'description': '섹션 시각화 테스트',
            'create_sections': True
        }
        response = requests.post(f"{BASE_URL}/process-request", files=files, data=data)

    if response.status_code != 200:
        print(f"❌ 문서 처리 실패: {response.status_code}")
        print(response.text)
        return None

    result = response.json()
    request_id = result['request_id']
    print(f"✅ 요청 ID: {request_id}")
    print(f"   처리 시간: {result['processing_time']}초")
    print(f"   페이지 수: {result['total_pages']}")

    return request_id


def test_sections_api(request_id: str):
    """섹션 API 엔드포인트 테스트"""
    print("\n" + "=" * 60)
    print("섹션 API 테스트")
    print("=" * 60)

    page_number = 1

    # 1. 섹션 목록 조회
    print(f"\n1️⃣ 섹션 목록 조회 (페이지 {page_number})")
    response = requests.get(f"{BASE_URL}/requests/{request_id}/pages/{page_number}/sections")

    if response.status_code == 200:
        sections = response.json()
        print(f"✅ 섹션 개수: {len(sections)}")
        for section in sections:
            print(f"   섹션 {section['section_id']}: {section['section_type']} "
                  f"(블록 {section['block_count']}개, 신뢰도 {section['avg_confidence']:.2f})")
    else:
        print(f"❌ 섹션 목록 조회 실패: {response.status_code}")
        print(response.text)
        return

    # 2. 개별 섹션 데이터 조회
    if sections:
        section_id = int(sections[0]['section_id'])
        print(f"\n2️⃣ 섹션 {section_id} 상세 데이터 조회")
        response = requests.get(f"{BASE_URL}/requests/{request_id}/pages/{page_number}/sections/{section_id}")

        if response.status_code == 200:
            section_data = response.json()
            print(f"✅ 섹션 타입: {section_data['section_type']}")
            print(f"   블록 개수: {section_data['block_count']}")
            print(f"   포함 블록: {', '.join(section_data['blocks'])}")
            print(f"   텍스트 미리보기: {section_data['text_content'][:100]}...")
        else:
            print(f"❌ 섹션 데이터 조회 실패: {response.status_code}")

    # 3. 섹션 크롭 이미지 다운로드
    if sections:
        section_id = int(sections[0]['section_id'])
        print(f"\n3️⃣ 섹션 {section_id} 이미지 다운로드")
        response = requests.get(f"{BASE_URL}/requests/{request_id}/pages/{page_number}/sections/{section_id}/image")

        if response.status_code == 200:
            output_file = f"test_section_{section_id}.png"
            with open(output_file, 'wb') as f:
                f.write(response.content)
            print(f"✅ 이미지 저장 완료: {output_file}")
        else:
            print(f"❌ 섹션 이미지 다운로드 실패: {response.status_code}")

    # 4. 전체 섹션 시각화 다운로드
    print(f"\n4️⃣ 전체 섹션 시각화 다운로드")
    response = requests.get(f"{BASE_URL}/requests/{request_id}/pages/{page_number}/sections-visualization")

    if response.status_code == 200:
        output_file = "test_sections_visualization.png"
        with open(output_file, 'wb') as f:
            f.write(response.content)
        print(f"✅ 시각화 저장 완료: {output_file}")
    else:
        print(f"❌ 섹션 시각화 다운로드 실패: {response.status_code}")
        print(response.text)


def test_directory_structure(request_id: str):
    """디렉토리 구조 확인"""
    print("\n" + "=" * 60)
    print("디렉토리 구조 확인")
    print("=" * 60)

    output_dir = Path("output") / request_id / "pages" / "001"

    if not output_dir.exists():
        print(f"❌ 출력 디렉토리를 찾을 수 없습니다: {output_dir}")
        return

    print(f"\n📁 페이지 디렉토리: {output_dir}")

    # 기본 파일들
    files = ["page_info.json", "result.json", "original.png", "visualization.png"]
    for file in files:
        file_path = output_dir / file
        if file_path.exists():
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file}")

    # 섹션 시각화
    sections_viz = output_dir / "sections_visualization.png"
    if sections_viz.exists():
        print(f"   ✅ sections_visualization.png")
    else:
        print(f"   ❌ sections_visualization.png (섹션이 생성되지 않았을 수 있음)")

    # blocks 폴더
    blocks_dir = output_dir / "blocks"
    if blocks_dir.exists():
        block_count = len(list(blocks_dir.glob("block_*.json")))
        print(f"   ✅ blocks/ ({block_count}개 블록)")
    else:
        print(f"   ❌ blocks/")

    # sections 폴더
    sections_dir = output_dir / "sections"
    if sections_dir.exists():
        section_count = len(list(sections_dir.glob("section_*.json")))
        section_images = len(list(sections_dir.glob("section_*.png")))
        print(f"   ✅ sections/ ({section_count}개 섹션, {section_images}개 이미지)")

        # 섹션 파일 상세
        for section_file in sorted(sections_dir.glob("section_*.json")):
            with open(section_file, 'r', encoding='utf-8') as f:
                section_data = json.load(f)
            print(f"      - {section_file.name}: {section_data['section_type']} "
                  f"(블록 {section_data['block_count']}개)")
    else:
        print(f"   ❌ sections/ (섹션이 생성되지 않았음)")


def main():
    """메인 테스트 실행"""
    print("\n🚀 섹션 시각화 통합 테스트 시작\n")

    # 서버 연결 확인
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("❌ API 서버에 연결할 수 없습니다")
            return
        print("✅ API 서버 연결 확인")
    except Exception as e:
        print(f"❌ API 서버 연결 실패: {e}")
        return

    # 1. 섹션 처리 테스트
    request_id = test_sections_processing()
    if not request_id:
        return

    # 잠시 대기 (파일 시스템 동기화)
    time.sleep(0.5)

    # 2. 섹션 API 테스트
    test_sections_api(request_id)

    # 3. 디렉토리 구조 확인
    test_directory_structure(request_id)

    print("\n" + "=" * 60)
    print("✅ 모든 테스트 완료")
    print("=" * 60)
    print(f"\n📊 요청 ID: {request_id}")
    print(f"📁 출력 경로: output/{request_id}/")
    print(f"🔍 API 문서: {BASE_URL}/docs")


if __name__ == "__main__":
    main()

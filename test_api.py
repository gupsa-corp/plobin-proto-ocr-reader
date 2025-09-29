#!/usr/bin/env python3
"""
API 테스트 스크립트
"""

import requests
import json
from pathlib import Path

API_BASE = "http://localhost:6003"

def test_health():
    """Health check 테스트"""
    print("🔍 Health check 테스트...")
    response = requests.get(f"{API_BASE}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_supported_formats():
    """지원 포맷 확인"""
    print("📋 지원 포맷 확인...")
    response = requests.get(f"{API_BASE}/supported-formats")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_server_status():
    """서버 상태 확인"""
    print("📊 서버 상태 확인...")
    response = requests.get(f"{API_BASE}/status")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        status = response.json()
        print(f"✅ 서버 정보:")
        print(f"   상태: {status['status']}")
        print(f"   업타임: {status['uptime_formatted']}")
        print(f"   총 요청 수: {status['total_requests']}")
        print(f"   처리된 PDF: {status['total_pdfs_processed']}")
        print(f"   처리된 이미지: {status['total_images_processed']}")
        print(f"   추출된 블록: {status['total_blocks_extracted']}")
        print(f"   평균 처리 시간: {status['average_processing_time']}초")
        print(f"   메모리 사용량: {status['system_info']['memory_used_mb']}MB / {status['system_info']['memory_total_mb']}MB ({status['system_info']['memory_percent']}%)")
        print(f"   CPU 사용률: {status['system_info']['cpu_percent']}%")
        print(f"   오류 수: {status['errors']}")
    else:
        print(f"❌ 상태 확인 실패: {response.text}")
    print()

def test_pdf_processing():
    """PDF 처리 테스트"""
    print("📄 PDF 처리 테스트...")
    pdf_path = "demo/invoices/sample_invoice.pdf"

    if not Path(pdf_path).exists():
        print(f"❌ PDF 파일을 찾을 수 없습니다: {pdf_path}")
        return

    with open(pdf_path, 'rb') as f:
        files = {'file': (pdf_path, f, 'application/pdf')}
        response = requests.post(f"{API_BASE}/process-pdf", files=files)

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"✅ 처리 성공!")
        print(f"   페이지 수: {len(result)}")
        for i, page in enumerate(result):
            print(f"   페이지 {i+1}: {page['total_blocks']}개 블록, 평균 신뢰도: {page['average_confidence']:.3f}")
    else:
        print(f"❌ 처리 실패: {response.text}")
    print()

def test_image_processing():
    """이미지 처리 테스트"""
    print("🖼️  이미지 처리 테스트...")

    # 먼저 demo/processed 폴더에서 이미지 찾기
    image_dir = Path("demo/processed")
    image_files = []

    if image_dir.exists():
        for subdir in image_dir.iterdir():
            if subdir.is_dir():
                for img_file in subdir.glob("images/*.png"):
                    image_files.append(img_file)
                    break  # 첫 번째 이미지만
            if image_files:
                break

    if not image_files:
        print("❌ 테스트할 이미지 파일을 찾을 수 없습니다.")
        return

    image_path = image_files[0]
    print(f"테스트 이미지: {image_path}")

    with open(image_path, 'rb') as f:
        files = {'file': (image_path.name, f, 'image/png')}
        response = requests.post(f"{API_BASE}/process-image", files=files)

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"✅ 처리 성공!")
        print(f"   블록 수: {result['total_blocks']}")
        print(f"   평균 신뢰도: {result['average_confidence']:.3f}")

        # 첫 3개 블록 텍스트 출력
        for i, block in enumerate(result['blocks'][:3]):
            print(f"   블록 {i+1}: '{block['text']}' (신뢰도: {block['confidence']:.3f})")
    else:
        print(f"❌ 처리 실패: {response.text}")
    print()

def test_general_processing():
    """범용 처리 테스트"""
    print("🔄 범용 문서 처리 테스트...")
    pdf_path = "demo/business/business_report.pdf"

    if not Path(pdf_path).exists():
        print(f"❌ PDF 파일을 찾을 수 없습니다: {pdf_path}")
        return

    with open(pdf_path, 'rb') as f:
        files = {'file': (pdf_path, f, 'application/pdf')}
        response = requests.post(f"{API_BASE}/process-document", files=files)

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"✅ 처리 성공!")
        if isinstance(result, list):
            print(f"   페이지 수: {len(result)}")
            total_blocks = sum(page['total_blocks'] for page in result)
            print(f"   총 블록 수: {total_blocks}")
        else:
            print(f"   블록 수: {result['total_blocks']}")
    else:
        print(f"❌ 처리 실패: {response.text}")
    print()

def main():
    """메인 테스트 함수"""
    print("🚀 Document OCR API 테스트 시작")
    print("=" * 50)

    try:
        test_health()
        test_supported_formats()
        test_server_status()
        test_pdf_processing()
        test_image_processing()
        test_general_processing()
        test_server_status()  # 처리 후 상태 다시 확인

        print("✅ 모든 테스트 완료!")

    except requests.exceptions.ConnectionError:
        print("❌ API 서버에 연결할 수 없습니다.")
        print("서버가 실행 중인지 확인하세요: python3 -m uvicorn api_server:app --host 0.0.0.0 --port 6003")
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")

if __name__ == "__main__":
    main()
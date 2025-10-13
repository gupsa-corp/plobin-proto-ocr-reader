#!/usr/bin/env python3
"""
LLM 분석 API 테스트 스크립트
"""

import requests
import json
import time
import os
from pathlib import Path


class AnalysisAPITester:
    """분석 API 테스트 클래스"""

    def __init__(self, base_url="http://localhost:6003"):
        self.base_url = base_url
        self.session = requests.Session()

    def test_health_check(self):
        """분석 서비스 상태 확인 테스트"""
        print("=== 분석 서비스 상태 확인 ===")
        try:
            response = self.session.get(f"{self.base_url}/analysis/health")
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
            return response.status_code == 200
        except Exception as e:
            print(f"Health check failed: {e}")
            return False

    def test_get_models(self):
        """사용 가능한 모델 목록 조회 테스트"""
        print("\n=== 사용 가능한 LLM 모델 조회 ===")
        try:
            response = self.session.get(f"{self.base_url}/analysis/models")
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
            return response.status_code == 200
        except Exception as e:
            print(f"Models fetch failed: {e}")
            return False

    def test_section_analysis(self):
        """개별 섹션 분석 테스트"""
        print("\n=== 개별 섹션 분석 테스트 ===")

        test_data = {
            "text": "상호: 테스트 카페\\n주소: 서울시 강남구 테헤란로 123\\n전화번호: 02-1234-5678\\n\\n메뉴:\\n아메리카노 4,500원\\n카페라떼 5,000원\\n케이크 6,000원\\n\\n총액: 15,500원\\n결제방법: 카드",
            "section_type": "receipt",
            "model": "gpt-3.5-turbo"
        }

        try:
            response = self.session.post(
                f"{self.base_url}/analysis/sections/analyze",
                json=test_data
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Section ID: {result['section_id']}")
                print(f"Section Type: {result['section_type']}")
                print(f"Analyzed Content: {result['analyzed_content'][:200]}...")
                print(f"Extracted Data: {json.dumps(result['extracted_data'], ensure_ascii=False, indent=2)}")
            else:
                print(f"Error Response: {response.text}")
            return response.status_code == 200
        except Exception as e:
            print(f"Section analysis failed: {e}")
            return False

    def test_document_upload_and_analysis(self):
        """문서 업로드 후 분석 테스트"""
        print("\n=== 문서 업로드 및 분석 테스트 ===")

        # 1. 먼저 문서를 업로드하여 OCR 처리
        test_file = Path("demo/images/sample.png")
        if not test_file.exists():
            print(f"테스트 파일을 찾을 수 없습니다: {test_file}")
            return False

        print("1. 문서 OCR 처리 중...")
        try:
            with open(test_file, "rb") as f:
                files = {"file": (test_file.name, f, "image/png")}
                data = {"description": "분석 테스트용 문서"}

                response = self.session.post(
                    f"{self.base_url}/process-request",
                    files=files,
                    data=data
                )

            print(f"OCR Status: {response.status_code}")
            if response.status_code != 200:
                print(f"OCR 처리 실패: {response.text}")
                return False

            ocr_result = response.json()
            request_id = ocr_result["request_id"]
            print(f"Request ID: {request_id}")

            # 잠시 대기 (OCR 처리 완료까지)
            time.sleep(2)

        except Exception as e:
            print(f"문서 업로드 실패: {e}")
            return False

        # 2. LLM 분석 실행
        print("2. LLM 분석 실행 중...")
        try:
            analysis_config = {
                "model": "gpt-3.5-turbo",
                "temperature": 0.1,
                "section_configs": [
                    {
                        "section_index": 0,
                        "section_type": "general",
                        "custom_prompt": "이 텍스트에서 중요한 정보를 추출하고 JSON 형태로 정리해주세요."
                    }
                ]
            }

            response = self.session.post(
                f"{self.base_url}/analysis/documents/{request_id}/pages/1/analyze",
                json=analysis_config
            )

            print(f"Analysis Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Total Sections: {result['total_sections']}")
                print(f"Processing Time: {result['processing_time']:.2f} seconds")
                print(f"Summary: {json.dumps(result['summary'], ensure_ascii=False, indent=2)}")

                # 3. 분석 결과 조회 테스트
                print("3. 분석 결과 조회 테스트...")
                get_response = self.session.get(
                    f"{self.base_url}/analysis/documents/{request_id}/pages/1/analysis"
                )
                print(f"Get Analysis Status: {get_response.status_code}")

                return True
            else:
                print(f"분석 실패: {response.text}")
                return False

        except Exception as e:
            print(f"LLM 분석 실패: {e}")
            return False

    def test_document_analysis_summary(self):
        """문서 분석 요약 조회 테스트"""
        print("\n=== 문서 분석 요약 조회 테스트 ===")

        # 기존 요청 목록에서 하나 선택
        try:
            response = self.session.get(f"{self.base_url}/requests")
            if response.status_code == 200:
                requests_list = response.json()
                if requests_list["requests"]:
                    request_id = requests_list["requests"][0]["request_id"]
                    print(f"Testing with request_id: {request_id}")

                    # 요약 조회
                    summary_response = self.session.get(
                        f"{self.base_url}/analysis/documents/{request_id}/analysis/summary?include_sections=true"
                    )
                    print(f"Summary Status: {summary_response.status_code}")
                    if summary_response.status_code == 200:
                        summary = summary_response.json()
                        print(f"Total Pages: {summary.get('total_pages', 0)}")
                        print(f"Analyzed Pages: {summary.get('analyzed_pages', 0)}")
                        print(f"Total Sections: {summary.get('total_sections', 0)}")
                        return True
                    else:
                        print(f"요약 조회 실패: {summary_response.text}")
                else:
                    print("기존 요청이 없습니다.")
            else:
                print(f"요청 목록 조회 실패: {response.text}")
                return False

        except Exception as e:
            print(f"분석 요약 조회 실패: {e}")
            return False

    def run_all_tests(self):
        """모든 테스트 실행"""
        print("LLM 분석 API 테스트 시작\\n")

        tests = [
            ("Health Check", self.test_health_check),
            ("Models List", self.test_get_models),
            ("Section Analysis", self.test_section_analysis),
            ("Document Analysis", self.test_document_upload_and_analysis),
            ("Analysis Summary", self.test_document_analysis_summary)
        ]

        results = {}
        for test_name, test_func in tests:
            print(f"\\n{'='*50}")
            print(f"Running: {test_name}")
            print('='*50)

            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"Test {test_name} crashed: {e}")
                results[test_name] = False

            time.sleep(1)  # 테스트 간 간격

        # 결과 요약
        print(f"\\n{'='*50}")
        print("테스트 결과 요약")
        print('='*50)

        passed = 0
        total = len(tests)

        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name}: {status}")
            if result:
                passed += 1

        print(f"\\n총 {passed}/{total} 테스트 통과")

        if passed == total:
            print("🎉 모든 테스트가 성공했습니다!")
        else:
            print("⚠️  일부 테스트가 실패했습니다.")

        return passed == total


def main():
    """메인 함수"""
    print("LLM 분석 API 테스트 시작...")

    # API 서버 연결 확인
    try:
        response = requests.get("http://localhost:6003/health", timeout=5)
        if response.status_code != 200:
            print("❌ API 서버가 실행되고 있지 않습니다.")
            print("다음 명령으로 서버를 시작하세요:")
            print("python3 -m uvicorn api_server:app --host 0.0.0.0 --port 6003 --reload")
            return
    except requests.exceptions.RequestException:
        print("❌ API 서버에 연결할 수 없습니다.")
        print("서버가 http://localhost:6003에서 실행 중인지 확인하세요.")
        return

    # 테스트 실행
    tester = AnalysisAPITester()
    success = tester.run_all_tests()

    if success:
        print("\\n✅ 모든 분석 API 테스트가 완료되었습니다.")
    else:
        print("\\n❌ 일부 테스트가 실패했습니다. 로그를 확인하세요.")


if __name__ == "__main__":
    main()
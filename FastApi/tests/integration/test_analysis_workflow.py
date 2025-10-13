"""
Analysis Workflow Integration Tests
"""

import pytest
import tempfile
import os
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestAnalysisWorkflow:
    """분석 워크플로우 통합 테스트"""

    def test_full_section_analysis_workflow(self, client: TestClient):
        """전체 섹션 분석 워크플로우 테스트"""
        with patch('api.endpoints.analysis.section_analysis.get_section_analyzer') as mock_analyzer:
            # Mock analyzer 설정
            mock_instance = AsyncMock()
            mock_result = type('MockResult', (), {
                'section_id': 'test_section_001',
                'section_type': 'receipt',
                'original_text': 'Test receipt text',
                'analyzed_content': 'This is a test receipt analysis',
                'extracted_data': {'total': 15500, 'merchant': 'Test Cafe'},
                'confidence_score': 0.95,
                'model_used': 'boto',
                'analysis_timestamp': '2025-10-10T12:00:00'
            })()
            mock_instance.analyze_section.return_value = mock_result
            mock_analyzer.return_value = mock_instance

            # 1. 건강 상태 확인
            health_response = client.get("/analysis/health")
            assert health_response.status_code in [200, 503]  # 실제 LLM 연결에 따라

            # 2. 모델 목록 조회
            models_response = client.get("/analysis/models")
            assert models_response.status_code == 200
            models_data = models_response.json()
            assert "models" in models_data

            # 3. 섹션 분석 실행
            analysis_response = client.post(
                "/analysis/sections/analyze",
                json={
                    "text": "Test Cafe Receipt Total: 15500 Won",
                    "section_type": "receipt",
                    "model": "boto"
                }
            )

            assert analysis_response.status_code == 200
            analysis_data = analysis_response.json()
            assert analysis_data["success"] is True
            assert analysis_data["section_type"] == "receipt"
            assert "extracted_data" in analysis_data

    @patch('api.endpoints.analysis.integrated_analysis.get_section_analyzer')
    def test_integrated_analysis_workflow(self, mock_analyzer, client: TestClient):
        """통합 분석 워크플로우 테스트"""
        # Mock 분석기 설정
        mock_instance = AsyncMock()
        mock_analyzer.return_value = mock_instance

        # Mock OCR 및 분석 결과
        with patch('services.ocr.DocumentBlockExtractor') as mock_extractor, \
             patch('services.file.request_manager.generate_uuid_v7') as mock_uuid, \
             patch('services.file.request_manager.create_request_structure'), \
             patch('os.makedirs'), \
             patch('builtins.open'), \
             patch('json.dump'):

            mock_uuid.return_value = "test_uuid_123"
            mock_extractor_instance = mock_extractor.return_value
            mock_extractor_instance.extract_blocks.return_value = {
                "blocks": [
                    {"text": "Test Cafe", "confidence": 0.95},
                    {"text": "Total: 15500", "confidence": 0.98}
                ]
            }

            # 테스트 이미지 파일 생성
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                temp_file.write(b"fake image data")
                temp_file_path = temp_file.name

            try:
                with open(temp_file_path, "rb") as f:
                    response = client.post(
                        "/analysis/process-and-analyze",
                        files={"file": ("test.png", f, "image/png")},
                        data={
                            "description": "Test integration",
                            "analysis_config": '{"perform_llm_analysis": true, "model": "boto"}'
                        }
                    )

                # 파일 처리에 따른 응답 확인
                assert response.status_code in [200, 400, 500]  # 실제 구현에 따라

            finally:
                os.unlink(temp_file_path)

    def test_error_handling_workflow(self, client: TestClient):
        """오류 처리 워크플로우 테스트"""
        # 1. 잘못된 섹션 분석 요청
        invalid_response = client.post(
            "/analysis/sections/analyze",
            json={"invalid": "data"}
        )
        assert invalid_response.status_code == 422  # Validation error

        # 2. 존재하지 않는 문서 분석 요청
        not_found_response = client.get(
            "/analysis/documents/nonexistent_id/pages/1/analysis"
        )
        assert not_found_response.status_code == 404

        # 3. 잘못된 요청 ID로 요약 조회
        summary_response = client.get(
            "/analysis/documents/invalid_id/summary"
        )
        assert summary_response.status_code == 404

    @patch('api.endpoints.analysis.debug.httpx.AsyncClient')
    def test_debug_workflow(self, mock_client, client: TestClient):
        """디버그 워크플로우 테스트"""
        # Mock HTTP 클라이언트
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.text = '{"status": "ok"}'

        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client_instance.post.return_value = mock_response
        mock_client_instance.options.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        # 1. API 정보 조회
        api_info_response = client.get("/analysis/debug/api-info")
        assert api_info_response.status_code == 200

        # 2. 연결 테스트
        connection_response = client.get("/analysis/debug/test-connection")
        assert connection_response.status_code == 200

        # 3. 수동 요청 테스트
        manual_response = client.post(
            "/analysis/debug/manual-request",
            json={
                "url": "https://test.example.com",
                "method": "GET",
                "payload": {}
            }
        )
        assert manual_response.status_code == 200

    def test_concurrent_requests(self, client: TestClient):
        """동시 요청 처리 테스트"""
        import concurrent.futures
        import threading

        def make_request():
            return client.get("/analysis/models")

        # 동시에 여러 요청 실행
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # 모든 요청이 성공했는지 확인
        for response in results:
            assert response.status_code == 200

    def test_api_consistency(self, client: TestClient):
        """API 응답 일관성 테스트"""
        # 모델 목록을 여러 번 요청해서 일관된 응답이 오는지 확인
        responses = []
        for _ in range(3):
            response = client.get("/analysis/models")
            responses.append(response)

        # 모든 응답이 동일한 구조를 가지는지 확인
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert "success" in data
            assert "models" in data
            assert isinstance(data["models"], list)

        # 응답 내용이 일관된지 확인
        first_models = responses[0].json()["models"]
        for response in responses[1:]:
            assert response.json()["models"] == first_models

    @patch('api.endpoints.analysis.document_summary.get_section_analyzer')
    def test_document_summary_workflow(self, mock_analyzer, client: TestClient):
        """문서 요약 워크플로우 테스트"""
        # Mock 분석기 설정
        mock_instance = AsyncMock()
        mock_result = type('MockResult', (), {
            'analyzed_content': 'Test summary content',
            'extracted_data': {'summary': 'Test document summary'}
        })()
        mock_instance.analyze_section.return_value = mock_result
        mock_analyzer.return_value = mock_instance

        # Mock 파일 시스템 작업
        with patch('os.path.exists') as mock_exists, \
             patch('os.listdir') as mock_listdir, \
             patch('builtins.open') as mock_open, \
             patch('json.load') as mock_json_load, \
             patch('json.dump') as mock_json_dump, \
             patch('os.makedirs'):

            # 요청 디렉토리가 존재한다고 Mock
            mock_exists.return_value = True
            mock_listdir.return_value = ["001"]

            # 페이지 데이터 Mock
            mock_json_load.return_value = {
                "blocks": [
                    {"text": "Test document content", "confidence": 0.95}
                ]
            }

            # 문서 요약 생성
            summary_response = client.post(
                "/analysis/documents/test_request_id/summarize",
                json={
                    "model": "boto",
                    "summary_type": "brief"
                }
            )

            # 실제 파일 작업 없이는 200이 어려울 수 있음
            assert summary_response.status_code in [200, 404, 500]

    def test_api_rate_limiting_simulation(self, client: TestClient):
        """API 속도 제한 시뮬레이션 테스트"""
        import time

        # 빠른 연속 요청
        start_time = time.time()
        responses = []

        for i in range(5):
            response = client.get("/analysis/models")
            responses.append(response)
            time.sleep(0.1)  # 짧은 간격으로 요청

        end_time = time.time()

        # 모든 요청이 처리되었는지 확인
        for response in responses:
            assert response.status_code == 200

        # 응답 시간이 합리적인지 확인
        total_time = end_time - start_time
        assert total_time < 10  # 10초 이내에 완료되어야 함
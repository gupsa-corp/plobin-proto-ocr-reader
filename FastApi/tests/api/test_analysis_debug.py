"""
Debug and Health Check API Tests
"""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient


@pytest.mark.unit
class TestDebugAPI:
    """디버그 API 단위 테스트"""

    def test_health_check_success(self, client: TestClient):
        """정상적인 헬스체크 테스트"""
        from api.endpoints.analysis.dependencies import get_llm_client
        from api_server import app

        def mock_successful_llm_client():
            mock_instance = AsyncMock()
            mock_instance.analyze_text.return_value = "OK"
            return mock_instance

        app.dependency_overrides[get_llm_client] = mock_successful_llm_client

        try:
            response = client.get("/analysis/health")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["status"] == "healthy"
            assert data["llm_connection"] == "connected"
            assert "timestamp" in data
        finally:
            app.dependency_overrides.clear()

    def test_health_check_llm_failure(self, client: TestClient):
        """LLM 연결 실패 시 헬스체크 테스트"""
        from api.endpoints.analysis.dependencies import get_llm_client
        from api_server import app

        def mock_failing_llm_client():
            mock_instance = AsyncMock()
            mock_instance.analyze_text.side_effect = Exception("LLM Connection Failed")
            return mock_instance

        app.dependency_overrides[get_llm_client] = mock_failing_llm_client

        try:
            response = client.get("/analysis/health")

            assert response.status_code == 503
            data = response.json()
            assert data["success"] is False
            assert data["status"] == "unhealthy"
            assert data["llm_connection"] == "failed"
            assert "error" in data
        finally:
            app.dependency_overrides.clear()

    def test_get_models(self, client: TestClient):
        """모델 목록 조회 테스트"""
        response = client.get("/analysis/models")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "models" in data
        assert isinstance(data["models"], list)
        assert len(data["models"]) > 0

        # 기본 모델들이 포함되어 있는지 확인
        model_ids = [model["model_id"] for model in data["models"]]
        assert "boto" in model_ids

    def test_api_info(self, client: TestClient):
        """API 정보 조회 테스트"""
        response = client.get("/analysis/debug/api-info")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "api_config" in data
        assert "supported_models" in data
        assert "timestamp" in data

        # API 설정 확인
        api_config = data["api_config"]
        assert api_config["base_url"] == "https://llm.gupsa.net/v1"
        assert "api_key_configured" in api_config
        assert "endpoints" in api_config

    @patch('api.endpoints.analysis.debug.httpx.AsyncClient')
    def test_connection_test_success(self, mock_client, client: TestClient):
        """연결 테스트 성공 케이스"""
        # Mock HTTP 응답
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.text = '{"status": "ok"}'

        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client_instance.options.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        response = client.get("/analysis/debug/test-connection")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "connection_tests" in data

    @patch('api.endpoints.analysis.debug.httpx.AsyncClient')
    def test_manual_request_get(self, mock_client, client: TestClient):
        """수동 GET 요청 테스트"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.text = '{"data": "test"}'

        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        response = client.post(
            "/analysis/debug/manual-request",
            json={
                "url": "https://test.example.com/api",
                "method": "GET",
                "headers": {"Authorization": "Bearer test"},
                "payload": {"param": "value"}
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "request" in data
        assert "response" in data

    @patch('api.endpoints.analysis.debug.httpx.AsyncClient')
    def test_manual_request_post(self, mock_client, client: TestClient):
        """수동 POST 요청 테스트"""
        mock_response = AsyncMock()
        mock_response.status_code = 201
        mock_response.headers = {"content-type": "application/json"}
        mock_response.text = '{"created": true}'

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        response = client.post(
            "/analysis/debug/manual-request",
            json={
                "url": "https://test.example.com/api",
                "method": "POST",
                "headers": {"Content-Type": "application/json"},
                "payload": {"data": "test"}
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["response"]["status_code"] == 201

    def test_manual_request_invalid_method(self, client: TestClient):
        """지원하지 않는 HTTP 메서드 테스트"""
        response = client.post(
            "/analysis/debug/manual-request",
            json={
                "url": "https://test.example.com/api",
                "method": "PATCH",  # 지원하지 않는 메서드
                "payload": {}
            }
        )

        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert "지원하지 않는 HTTP 메서드" in data["error"]

    @patch('api.endpoints.analysis.debug.httpx.AsyncClient')
    def test_manual_request_network_error(self, mock_client, client: TestClient):
        """네트워크 오류 테스트"""
        mock_client_instance = AsyncMock()
        mock_client_instance.get.side_effect = Exception("Network error")
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        response = client.post(
            "/analysis/debug/manual-request",
            json={
                "url": "https://invalid.example.com/api",
                "method": "GET",
                "payload": {}
            }
        )

        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert "error" in data

    def test_models_response_structure(self, client: TestClient):
        """모델 응답 구조 검증"""
        response = client.get("/analysis/models")
        data = response.json()

        # 각 모델이 필요한 필드를 가지고 있는지 확인
        for model in data["models"]:
            assert "model_id" in model
            assert "name" in model
            assert "description" in model
            assert isinstance(model["model_id"], str)
            assert isinstance(model["name"], str)
            assert isinstance(model["description"], str)
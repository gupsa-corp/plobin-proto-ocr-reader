"""
Section Analysis API Tests
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient


@pytest.mark.unit
class TestSectionAnalysisAPI:
    """섹션 분석 API 단위 테스트"""

    def test_analyze_section_success(self, client: TestClient, mock_llm_response):
        """성공적인 섹션 분석 테스트"""
        with patch('api.endpoints.analysis.section_analysis.get_section_analyzer') as mock_analyzer:
            # Mock analyzer 설정
            mock_instance = AsyncMock()
            mock_instance.analyze_section.return_value = type('MockResult', (), mock_llm_response)()
            mock_analyzer.return_value = mock_instance

            # API 호출
            response = client.post(
                "/analysis/sections/analyze",
                json={
                    "text": "Test Cafe Receipt Total: 15500 Won",
                    "section_type": "receipt",
                    "model": "boto"
                }
            )

            # 검증
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["section_type"] == "receipt"
            assert data["model_used"] == "boto"
            assert "analyzed_content" in data
            assert "extracted_data" in data

    def test_analyze_section_invalid_input(self, client: TestClient):
        """잘못된 입력 데이터 테스트"""
        response = client.post(
            "/analysis/sections/analyze",
            json={
                "text": "",  # 빈 텍스트
                "section_type": "invalid_type"
            }
        )

        # 검증 (실제 구현에 따라 조정 필요)
        assert response.status_code in [400, 422]

    def test_analyze_section_missing_text(self, client: TestClient):
        """필수 필드 누락 테스트"""
        response = client.post(
            "/analysis/sections/analyze",
            json={
                "section_type": "receipt"
                # text 필드 누락
            }
        )

        assert response.status_code == 422  # Validation error

    def test_analyze_section_llm_error(self, client: TestClient):
        """LLM 분석 실패 시 에러 처리 테스트"""
        from api.endpoints.analysis.dependencies import get_section_analyzer
        from api_server import app

        def mock_failing_analyzer():
            mock_instance = AsyncMock()
            mock_instance.analyze_section.side_effect = Exception("LLM API Error")
            return mock_instance

        app.dependency_overrides[get_section_analyzer] = mock_failing_analyzer

        try:
            response = client.post(
                "/analysis/sections/analyze",
                json={
                    "text": "Test text",
                    "section_type": "general"
                }
            )

            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "오류 발생" in data["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_analyze_section_different_models(self, client: TestClient, mock_llm_response):
        """다양한 모델 테스트"""
        from api.endpoints.analysis.dependencies import get_section_analyzer
        from api_server import app

        models = ["boto", "gpt-4", "claude-3-sonnet"]

        for model in models:
            def create_mock_analyzer(model_name):
                def mock_analyzer():
                    mock_instance = AsyncMock()
                    mock_response = mock_llm_response.copy()
                    mock_response["model_used"] = model_name
                    mock_instance.analyze_section.return_value = type('MockResult', (), mock_response)()
                    return mock_instance
                return mock_analyzer

            app.dependency_overrides[get_section_analyzer] = create_mock_analyzer(model)

            try:
                response = client.post(
                    "/analysis/sections/analyze",
                    json={
                        "text": "Test text",
                        "section_type": "general",
                        "model": model
                    }
                )

                assert response.status_code == 200
                data = response.json()
                assert data["model_used"] == model
            finally:
                app.dependency_overrides.clear()

    def test_analyze_section_various_types(self, client: TestClient, mock_llm_response):
        """다양한 섹션 타입 테스트"""
        section_types = ["receipt", "invoice", "contract", "general"]

        for section_type in section_types:
            with patch('api.endpoints.analysis.dependencies.get_section_analyzer') as mock_analyzer:
                mock_instance = AsyncMock()
                mock_response = mock_llm_response.copy()
                mock_response["section_type"] = section_type
                mock_instance.analyze_section.return_value = type('MockResult', (), mock_response)()
                mock_analyzer.return_value = mock_instance

                response = client.post(
                    "/analysis/sections/analyze",
                    json={
                        "text": "Test text for " + section_type,
                        "section_type": section_type
                    }
                )

                assert response.status_code == 200
                data = response.json()
                assert data["section_type"] == section_type

    def test_analyze_section_custom_prompt(self, client: TestClient, mock_llm_response):
        """커스텀 프롬프트 테스트"""
        from api.endpoints.analysis.dependencies import get_section_analyzer
        from api_server import app

        def mock_custom_analyzer():
            mock_instance = AsyncMock()
            mock_instance.analyze_section.return_value = type('MockResult', (), mock_llm_response)()
            return mock_instance

        app.dependency_overrides[get_section_analyzer] = mock_custom_analyzer

        try:
            response = client.post(
                "/analysis/sections/analyze",
                json={
                    "text": "Test text",
                    "section_type": "general",
                    "custom_prompt": "Extract only the price information"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
        finally:
            app.dependency_overrides.clear()

    def test_analyze_section_long_text(self, client: TestClient, mock_llm_response):
        """긴 텍스트 처리 테스트"""
        from api.endpoints.analysis.dependencies import get_section_analyzer
        from api_server import app

        long_text = "Very long text " * 1000  # 긴 텍스트 생성

        def mock_long_text_analyzer():
            mock_instance = AsyncMock()
            mock_instance.analyze_section.return_value = type('MockResult', (), mock_llm_response)()
            return mock_instance

        app.dependency_overrides[get_section_analyzer] = mock_long_text_analyzer

        try:
            response = client.post(
                "/analysis/sections/analyze",
                json={
                    "text": long_text,
                    "section_type": "general"
                }
            )

            assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    def test_analyze_section_special_characters(self, client: TestClient, mock_llm_response):
        """특수 문자 처리 테스트"""
        special_text = "텍스트 with émojis 🎉 and symbols ₩£$€ & <tags>"

        with patch('api.endpoints.analysis.section_analysis.get_section_analyzer') as mock_analyzer:
            mock_instance = AsyncMock()
            mock_instance.analyze_section.return_value = type('MockResult', (), mock_llm_response)()
            mock_analyzer.return_value = mock_instance

            response = client.post(
                "/analysis/sections/analyze",
                json={
                    "text": special_text,
                    "section_type": "general"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["original_text"] == special_text
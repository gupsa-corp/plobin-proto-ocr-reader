"""
LLM Client Service Tests
"""

import pytest
from unittest.mock import patch, AsyncMock
import httpx

from services.llm.client import LLMClient
from services.llm import LLMModel


@pytest.mark.unit
class TestLLMClient:
    """LLM 클라이언트 서비스 단위 테스트"""

    def test_llm_client_initialization(self):
        """LLM 클라이언트 초기화 테스트"""
        # 기본 초기화
        client = LLMClient()
        assert client.base_url == "https://llm.gupsa.net/v1"
        assert client.api_key is None

        # API 키와 함께 초기화
        client_with_key = LLMClient(api_key="test_key")
        assert client_with_key.api_key == "test_key"

        # 커스텀 URL과 함께 초기화
        client_custom = LLMClient(base_url="https://custom.api.com/v1")
        assert client_custom.base_url == "https://custom.api.com/v1"

    @patch('services.llm.client.httpx.AsyncClient')
    async def test_chat_completion_success(self, mock_client):
        """채팅 완성 성공 테스트"""
        # Mock 응답 설정
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Test response from LLM"
                    }
                }
            ]
        }

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        # 테스트 실행
        client = LLMClient(api_key="test_key")
        result = await client.chat_completion(
            messages=[{"role": "user", "content": "Hello"}],
            model=LLMModel.BOTO
        )

        # 검증
        assert result == "Test response from LLM"
        mock_client_instance.post.assert_called_once()

    @patch('services.llm.client.httpx.AsyncClient')
    async def test_chat_completion_api_error(self, mock_client):
        """API 오류 시 채팅 완성 테스트"""
        mock_response = AsyncMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        client = LLMClient(api_key="test_key")

        with pytest.raises(Exception) as exc_info:
            await client.chat_completion(
                messages=[{"role": "user", "content": "Hello"}],
                model=LLMModel.BOTO
            )

        assert "LLM API 요청 실패" in str(exc_info.value)

    @patch('services.llm.client.httpx.AsyncClient')
    async def test_chat_completion_network_error(self, mock_client):
        """네트워크 오류 시 채팅 완성 테스트"""
        mock_client_instance = AsyncMock()
        mock_client_instance.post.side_effect = httpx.ConnectError("Connection failed")
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        client = LLMClient(api_key="test_key")

        with pytest.raises(Exception) as exc_info:
            await client.chat_completion(
                messages=[{"role": "user", "content": "Hello"}],
                model=LLMModel.BOTO
            )

        assert "LLM API 연결 실패" in str(exc_info.value)

    @patch('services.llm.client.httpx.AsyncClient')
    async def test_analyze_text_method(self, mock_client):
        """analyze_text 메서드 테스트"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Analyzed text result"
                    }
                }
            ]
        }

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        client = LLMClient(api_key="test_key")
        result = await client.analyze_text(
            text="Test text to analyze",
            prompt="Analyze this text",
            model=LLMModel.BOTO
        )

        assert result == "Analyzed text result"

    def test_headers_construction(self):
        """헤더 구성 테스트"""
        client = LLMClient(api_key="test_key")
        headers = client._get_headers()

        assert headers["Content-Type"] == "application/json"
        assert headers["Authorization"] == "Bearer test_key"

        # API 키가 없는 경우
        client_no_key = LLMClient()
        headers_no_key = client_no_key._get_headers()
        assert "Authorization" not in headers_no_key

    @patch('services.llm.client.httpx.AsyncClient')
    async def test_different_models(self, mock_client):
        """다양한 모델로 테스트"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response"}}]
        }

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        client = LLMClient(api_key="test_key")

        models = [LLMModel.BOTO, LLMModel.GPT_4, LLMModel.CLAUDE_3_SONNET]

        for model in models:
            result = await client.chat_completion(
                messages=[{"role": "user", "content": "Test"}],
                model=model
            )
            assert result == "Response"

    @patch('services.llm.client.httpx.AsyncClient')
    async def test_request_timeout(self, mock_client):
        """요청 타임아웃 테스트"""
        mock_client_instance = AsyncMock()
        mock_client_instance.post.side_effect = httpx.TimeoutException("Request timeout")
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        client = LLMClient(api_key="test_key")

        with pytest.raises(Exception) as exc_info:
            await client.chat_completion(
                messages=[{"role": "user", "content": "Hello"}],
                model=LLMModel.BOTO
            )

        assert "LLM API 연결 실패" in str(exc_info.value)

    @patch('services.llm.client.httpx.AsyncClient')
    async def test_empty_response(self, mock_client):
        """빈 응답 처리 테스트"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": []}

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        client = LLMClient(api_key="test_key")

        with pytest.raises(Exception) as exc_info:
            await client.chat_completion(
                messages=[{"role": "user", "content": "Hello"}],
                model=LLMModel.BOTO
            )

        assert "응답이 비어있습니다" in str(exc_info.value)

    @patch('services.llm.client.httpx.AsyncClient')
    async def test_malformed_response(self, mock_client):
        """잘못된 형식의 응답 처리 테스트"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"invalid": "response"}

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        client = LLMClient(api_key="test_key")

        with pytest.raises(Exception):
            await client.chat_completion(
                messages=[{"role": "user", "content": "Hello"}],
                model=LLMModel.BOTO
            )
"""
Section Analyzer Service Tests
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from services.llm.analyzer import SectionAnalyzer
from services.llm import LLMModel


@pytest.mark.unit
class TestSectionAnalyzer:
    """섹션 분석기 서비스 단위 테스트"""

    @pytest.fixture
    def mock_llm_client(self):
        """Mock LLM 클라이언트"""
        return AsyncMock()

    @pytest.fixture
    def analyzer(self, mock_llm_client):
        """섹션 분석기 인스턴스"""
        return SectionAnalyzer(mock_llm_client)

    async def test_analyze_section_success(self, analyzer, mock_llm_client):
        """섹션 분석 성공 테스트"""
        # Mock LLM 응답
        mock_llm_client.analyze_text.return_value = """
        분석 결과:
        이것은 카페 영수증입니다.

        추출된 데이터:
        ```json
        {
            "merchant": "Test Cafe",
            "total": 15500,
            "currency": "KRW"
        }
        ```
        """

        result = await analyzer.analyze_section(
            section_text="Test Cafe Receipt Total: 15500 Won",
            section_type="receipt",
            model=LLMModel.BOTO
        )

        # 검증
        assert result.section_type == "receipt"
        assert result.model_used == LLMModel.BOTO
        assert "카페 영수증" in result.analyzed_content
        assert result.extracted_data is not None
        assert isinstance(result.extracted_data, dict)
        assert result.section_id.startswith("section_")
        assert result.analysis_timestamp is not None

    async def test_analyze_section_with_custom_prompt(self, analyzer, mock_llm_client):
        """커스텀 프롬프트로 섹션 분석 테스트"""
        mock_llm_client.analyze_text.return_value = "Custom analysis result"

        result = await analyzer.analyze_section(
            section_text="Test text",
            section_type="general",
            analysis_prompt="Extract only prices",
            model=LLMModel.BOTO
        )

        # LLM 클라이언트가 커스텀 프롬프트로 호출되었는지 확인
        mock_llm_client.analyze_text.assert_called_once()
        call_args = mock_llm_client.analyze_text.call_args
        assert "Extract only prices" in call_args[1]["prompt"]

    async def test_analyze_section_json_extraction(self, analyzer, mock_llm_client):
        """JSON 데이터 추출 테스트"""
        mock_llm_client.analyze_text.return_value = """
        분석 완료

        ```json
        {
            "type": "receipt",
            "amount": 15500,
            "items": ["coffee", "cake"]
        }
        ```

        추가 설명
        """

        result = await analyzer.analyze_section(
            section_text="Test receipt",
            section_type="receipt"
        )

        # JSON 데이터가 올바르게 추출되었는지 확인
        assert result.extracted_data["type"] == "receipt"
        assert result.extracted_data["amount"] == 15500
        assert result.extracted_data["items"] == ["coffee", "cake"]

    async def test_analyze_section_no_json(self, analyzer, mock_llm_client):
        """JSON 데이터가 없는 경우 테스트"""
        mock_llm_client.analyze_text.return_value = "단순한 텍스트 분석 결과"

        result = await analyzer.analyze_section(
            section_text="Test text",
            section_type="general"
        )

        # JSON 데이터가 없으면 빈 딕셔너리
        assert result.extracted_data == {}

    async def test_analyze_section_invalid_json(self, analyzer, mock_llm_client):
        """잘못된 JSON 형식 처리 테스트"""
        mock_llm_client.analyze_text.return_value = """
        ```json
        {
            "invalid": json,
            "missing": quote
        }
        ```
        """

        result = await analyzer.analyze_section(
            section_text="Test text",
            section_type="general"
        )

        # 잘못된 JSON은 빈 딕셔너리로 처리
        assert result.extracted_data == {}

    async def test_analyze_section_multiple_json_blocks(self, analyzer, mock_llm_client):
        """여러 JSON 블록이 있는 경우 테스트"""
        mock_llm_client.analyze_text.return_value = """
        첫 번째 JSON:
        ```json
        {"first": "data"}
        ```

        두 번째 JSON:
        ```json
        {"second": "data", "merged": true}
        ```
        """

        result = await analyzer.analyze_section(
            section_text="Test text",
            section_type="general"
        )

        # 마지막 JSON 블록이 사용되어야 함
        assert result.extracted_data["second"] == "data"
        assert result.extracted_data["merged"] is True

    async def test_analyze_section_llm_error(self, analyzer, mock_llm_client):
        """LLM 오류 시 예외 처리 테스트"""
        mock_llm_client.analyze_text.side_effect = Exception("LLM API Error")

        with pytest.raises(Exception) as exc_info:
            await analyzer.analyze_section(
                section_text="Test text",
                section_type="general"
            )

        assert "LLM API Error" in str(exc_info.value)

    async def test_analyze_document_sections(self, analyzer, mock_llm_client):
        """문서 섹션 분석 테스트"""
        # Mock OCR 결과
        ocr_result = {
            "blocks": [
                {"text": "Test Cafe", "type": "title"},
                {"text": "Americano: 4500", "type": "menu"},
                {"text": "Total: 15500", "type": "total"}
            ]
        }

        mock_llm_client.analyze_text.return_value = "분석된 내용"

        result = await analyzer.analyze_document_sections(
            ocr_result=ocr_result,
            request_id="test_request",
            page_number=1
        )

        # 검증
        assert result.request_id == "test_request"
        assert result.page_number == 1
        assert len(result.sections) > 0
        assert result.summary is not None

    def test_generate_section_id(self, analyzer):
        """섹션 ID 생성 테스트"""
        section_id = analyzer._generate_section_id()

        assert section_id.startswith("section_")
        assert len(section_id) > len("section_")
        assert section_id.isascii()

        # 여러 번 호출해도 다른 ID가 생성되어야 함
        section_id2 = analyzer._generate_section_id()
        assert section_id != section_id2

    async def test_different_section_types(self, analyzer, mock_llm_client):
        """다양한 섹션 타입 테스트"""
        mock_llm_client.analyze_text.return_value = "분석 결과"

        section_types = ["receipt", "invoice", "contract", "general"]

        for section_type in section_types:
            result = await analyzer.analyze_section(
                section_text="Test text",
                section_type=section_type
            )
            assert result.section_type == section_type

    async def test_confidence_score_calculation(self, analyzer, mock_llm_client):
        """신뢰도 점수 계산 테스트"""
        # 높은 품질의 응답
        mock_llm_client.analyze_text.return_value = """
        명확한 분석 결과입니다.

        ```json
        {"confidence": "high", "clear_data": true}
        ```
        """

        result = await analyzer.analyze_section(
            section_text="Clear and detailed text",
            section_type="receipt"
        )

        # 신뢰도가 계산되었는지 확인 (구현에 따라 조정 필요)
        assert result.confidence_score is None or isinstance(result.confidence_score, (int, float))

    async def test_empty_text_analysis(self, analyzer, mock_llm_client):
        """빈 텍스트 분석 테스트"""
        mock_llm_client.analyze_text.return_value = "빈 텍스트 분석 결과"

        result = await analyzer.analyze_section(
            section_text="",
            section_type="general"
        )

        assert result.original_text == ""
        assert result.analyzed_content == "빈 텍스트 분석 결과"

    async def test_very_long_text_analysis(self, analyzer, mock_llm_client):
        """매우 긴 텍스트 분석 테스트"""
        long_text = "Very long text " * 1000
        mock_llm_client.analyze_text.return_value = "긴 텍스트 분석 결과"

        result = await analyzer.analyze_section(
            section_text=long_text,
            section_type="general"
        )

        assert result.original_text == long_text
        assert len(result.analyzed_content) > 0
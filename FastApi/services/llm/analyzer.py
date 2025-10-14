"""
OCR 결과의 섹션별 분석기
"""

import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from .client import LLMClient, LLMModel


@dataclass
class SectionAnalysisResult:
    """섹션 분석 결과"""
    section_id: str
    section_type: str
    original_text: str
    analyzed_content: str
    extracted_data: Dict[str, Any]
    confidence_score: Optional[float] = None
    analysis_timestamp: str = None
    model_used: str = None

    def __post_init__(self):
        if self.analysis_timestamp is None:
            self.analysis_timestamp = datetime.now().isoformat()


@dataclass
class DocumentAnalysisResult:
    """전체 문서 분석 결과"""
    request_id: str
    page_number: int
    sections: List[SectionAnalysisResult]
    summary: Dict[str, Any]
    total_processing_time: float
    analysis_timestamp: str = None

    def __post_init__(self):
        if self.analysis_timestamp is None:
            self.analysis_timestamp = datetime.now().isoformat()


class SectionAnalyzer:
    """OCR 결과의 섹션별 LLM 분석기"""

    def __init__(self, llm_client: LLMClient):
        """
        분석기 초기화

        Args:
            llm_client: LLM API 클라이언트
        """
        self.llm_client = llm_client

    async def analyze_section(
        self,
        section_text: str,
        section_type: str = "general",
        analysis_prompt: Optional[str] = None,
        model: str = LLMModel.BOTO
    ) -> SectionAnalysisResult:
        """
        개별 섹션 분석

        Args:
            section_text: 분석할 섹션 텍스트
            section_type: 섹션 유형 (invoice, receipt, contract, etc.)
            analysis_prompt: 사용자 정의 분석 프롬프트
            model: 사용할 LLM 모델

        Returns:
            섹션 분석 결과
        """
        if not analysis_prompt:
            analysis_prompt = self._get_default_prompt(section_type)

        analyzed_content = await self.llm_client.analyze_text(
            text=section_text,
            prompt=analysis_prompt,
            model=model
        )

        # JSON 형태로 구조화된 데이터 추출 시도
        extracted_data = self._extract_structured_data(analyzed_content)

        return SectionAnalysisResult(
            section_id=f"section_{hash(section_text) % 10000:04d}",
            section_type=section_type,
            original_text=section_text,
            analyzed_content=analyzed_content,
            extracted_data=extracted_data,
            model_used=model
        )

    async def analyze_document_sections(
        self,
        ocr_result: Dict[str, Any],
        request_id: str,
        page_number: int,
        section_configs: Optional[List[Dict[str, Any]]] = None,
        model: str = LLMModel.BOTO
    ) -> DocumentAnalysisResult:
        """
        OCR 결과의 모든 섹션을 분석

        Args:
            ocr_result: OCR 처리 결과 데이터
            request_id: 요청 ID
            page_number: 페이지 번호
            section_configs: 섹션별 분석 설정 리스트
            model: 사용할 LLM 모델

        Returns:
            문서 전체 분석 결과
        """
        start_time = datetime.now()
        sections = []

        # OCR 결과에서 블록들을 섹션으로 그룹화
        text_blocks = self._extract_text_blocks(ocr_result)
        section_groups = self._group_blocks_into_sections(text_blocks)

        for i, section_group in enumerate(section_groups):
            section_text = " ".join([block["text"] for block in section_group])

            # 섹션 설정 찾기
            section_config = self._find_section_config(section_configs, i) if section_configs else {}
            section_type = section_config.get("type", "general")
            analysis_prompt = section_config.get("prompt")

            section_result = await self.analyze_section(
                section_text=section_text,
                section_type=section_type,
                analysis_prompt=analysis_prompt,
                model=model
            )
            sections.append(section_result)

        # 전체 문서 요약 생성
        summary = await self._generate_document_summary(sections, model)

        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        return DocumentAnalysisResult(
            request_id=request_id,
            page_number=page_number,
            sections=sections,
            summary=summary,
            total_processing_time=processing_time
        )

    def _get_default_prompt(self, section_type: str) -> str:
        """섹션 유형별 기본 분석 프롬프트 반환"""
        prompts = {
            "invoice": """
다음 송장/인보이스 텍스트를 분석하여 주요 정보를 추출하고 JSON 형태로 정리해주세요.
추출할 정보: 발행자, 수신자, 날짜, 품목, 수량, 단가, 총액, 세금 정보 등

분석 후 다음 형태로 응답해주세요:
1. 주요 내용 요약
2. 추출된 구조화 데이터 (JSON)
3. 특이사항이나 주의점
""",
            "receipt": """
다음 영수증 텍스트를 분석하여 주요 정보를 추출하고 JSON 형태로 정리해주세요.
추출할 정보: 상호명, 주소, 전화번호, 날짜, 시간, 구매 품목, 가격, 결제 수단 등

분석 후 다음 형태로 응답해주세요:
1. 주요 내용 요약
2. 추출된 구조화 데이터 (JSON)
3. 특이사항이나 주의점
""",
            "contract": """
다음 계약서 텍스트를 분석하여 주요 조항과 정보를 추출해주세요.
추출할 정보: 계약 당사자, 계약 기간, 주요 조건, 금액, 책임사항 등

분석 후 다음 형태로 응답해주세요:
1. 계약서 주요 내용 요약
2. 핵심 조항 및 조건
3. 주의해야 할 사항
""",
            "general": """
다음 텍스트를 분석하여 주요 정보를 추출하고 내용을 요약해주세요.
가능한 경우 구조화된 데이터로 정리해주세요.

분석 후 다음 형태로 응답해주세요:
1. 주요 내용 요약
2. 추출 가능한 구조화 데이터
3. 특이사항이나 주의점
"""
        }
        return prompts.get(section_type, prompts["general"])

    def _extract_text_blocks(self, ocr_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """OCR 결과에서 텍스트 블록 추출"""
        blocks = []

        if "text_blocks" in ocr_result:
            blocks = ocr_result["text_blocks"]
        elif "blocks" in ocr_result:
            # 새로운 OCR 결과 형식 또는 API 페이지 결과 형식 지원
            for block in ocr_result["blocks"]:
                if isinstance(block, dict) and "text" in block:
                    blocks.append({
                        "text": block["text"],
                        "confidence": block.get("confidence", 0.0),
                        "bbox": block.get("bbox", {})
                    })
        elif "results" in ocr_result:
            # 기존 OCR 결과 형식 지원
            for result in ocr_result["results"]:
                if isinstance(result, dict) and "text" in result:
                    blocks.append({
                        "text": result["text"],
                        "confidence": result.get("confidence", 0.0),
                        "bbox": result.get("bbox", [])
                    })

        return blocks

    def _group_blocks_into_sections(self, text_blocks: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """텍스트 블록들을 섹션으로 그룹화 (위치 기반)"""
        if not text_blocks:
            return []

        # 간단한 그룹화: Y 좌표 기준으로 비슷한 위치의 블록들을 묶음
        sections = []
        current_section = []
        last_y = None

        for block in text_blocks:
            if "bbox" in block and len(block["bbox"]) >= 4:
                y_pos = block["bbox"][1]  # Y 좌표

                if last_y is None or abs(y_pos - last_y) < 50:  # 50픽셀 이내면 같은 섹션
                    current_section.append(block)
                else:
                    if current_section:
                        sections.append(current_section)
                    current_section = [block]

                last_y = y_pos
            else:
                current_section.append(block)

        if current_section:
            sections.append(current_section)

        return sections

    def _find_section_config(self, section_configs: List[Dict[str, Any]], section_index: int) -> Dict[str, Any]:
        """섹션 인덱스에 해당하는 설정 찾기"""
        if section_index < len(section_configs):
            return section_configs[section_index]
        return {}

    def _extract_structured_data(self, analyzed_content: str) -> Dict[str, Any]:
        """분석 결과에서 JSON 구조화 데이터 추출 시도"""
        try:
            # JSON 블록 찾기 시도
            start_markers = ["```json", "{", "["]
            end_markers = ["```", "}", "]"]

            for start_marker in start_markers:
                start_idx = analyzed_content.find(start_marker)
                if start_idx != -1:
                    start_idx += len(start_marker) if start_marker.startswith("```") else 0

                    for end_marker in end_markers:
                        end_idx = analyzed_content.find(end_marker, start_idx)
                        if end_idx != -1:
                            json_str = analyzed_content[start_idx:end_idx]
                            if end_marker == "}":
                                json_str += "}"
                            elif end_marker == "]":
                                json_str += "]"

                            try:
                                return json.loads(json_str)
                            except json.JSONDecodeError:
                                continue

            return {"raw_analysis": analyzed_content}

        except Exception:
            return {"raw_analysis": analyzed_content}

    async def _generate_document_summary(self, sections: List[SectionAnalysisResult], model: str) -> Dict[str, Any]:
        """전체 문서 요약 생성"""
        if not sections:
            return {"summary": "분석된 섹션이 없습니다."}

        # 모든 섹션의 분석 결과를 하나로 합침
        combined_analysis = "\n\n".join([
            f"섹션 {i+1} ({section.section_type}): {section.analyzed_content}"
            for i, section in enumerate(sections)
        ])

        summary_prompt = """
다음은 문서의 각 섹션별 분석 결과입니다. 이를 종합하여 전체 문서의 요약을 작성해주세요.

요약에 포함할 내용:
1. 문서 유형 및 주요 목적
2. 핵심 정보 정리
3. 중요한 수치나 날짜
4. 전체적인 특징이나 패턴

JSON 형태로 구조화하여 응답해주세요.
"""

        try:
            summary_content = await self.llm_client.analyze_text(
                text=combined_analysis,
                prompt=summary_prompt,
                model=model
            )

            structured_summary = self._extract_structured_data(summary_content)
            if "raw_analysis" in structured_summary:
                return {
                    "summary": summary_content,
                    "total_sections": len(sections),
                    "section_types": list(set(s.section_type for s in sections))
                }
            else:
                structured_summary.update({
                    "total_sections": len(sections),
                    "section_types": list(set(s.section_type for s in sections))
                })
                return structured_summary

        except Exception as e:
            return {
                "summary": f"요약 생성 중 오류 발생: {str(e)}",
                "total_sections": len(sections),
                "section_types": list(set(s.section_type for s in sections))
            }
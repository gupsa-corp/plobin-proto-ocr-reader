"""
LLM 분석 API 공통 의존성
"""

import os
from typing import Optional

from fastapi import Depends

from services.llm import LLMClient, SectionAnalyzer

# LLM 클라이언트 인스턴스 (싱글톤)
_llm_client: Optional[LLMClient] = None
_section_analyzer: Optional[SectionAnalyzer] = None


def get_llm_client() -> LLMClient:
    """LLM 클라이언트 의존성 주입"""
    global _llm_client
    if _llm_client is None:
        api_key = os.getenv("GUPSA_AI_API_KEY")
        _llm_client = LLMClient(api_key=api_key)
    return _llm_client


def get_section_analyzer(llm_client: LLMClient = Depends(get_llm_client)) -> SectionAnalyzer:
    """섹션 분석기 의존성 주입"""
    global _section_analyzer
    if _section_analyzer is None:
        _section_analyzer = SectionAnalyzer(llm_client)
    return _section_analyzer
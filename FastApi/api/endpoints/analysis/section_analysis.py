"""
기본 섹션 분석 API 엔드포인트
"""

from fastapi import APIRouter, HTTPException, Depends

from api.models.analysis import SectionAnalysisRequest, SectionAnalysisResponse
from services.llm import SectionAnalyzer
from .dependencies import get_section_analyzer

router = APIRouter()


@router.post("/sections/analyze", response_model=SectionAnalysisResponse)
async def analyze_section(
    request: SectionAnalysisRequest,
    analyzer: SectionAnalyzer = Depends(get_section_analyzer)
):
    """
    개별 섹션 텍스트 분석

    - **text**: 분석할 텍스트
    - **section_type**: 섹션 유형 (invoice, receipt, contract, general)
    - **custom_prompt**: 사용자 정의 분석 프롬프트 (선택사항)
    - **model**: 사용할 LLM 모델 (선택사항)
    """
    try:
        result = await analyzer.analyze_section(
            section_text=request.text,
            section_type=request.section_type,
            analysis_prompt=request.custom_prompt,
            model=request.model
        )

        return SectionAnalysisResponse(
            success=True,
            section_id=result.section_id,
            section_type=result.section_type,
            original_text=result.original_text,
            analyzed_content=result.analyzed_content,
            extracted_data=result.extracted_data,
            confidence_score=result.confidence_score,
            model_used=result.model_used,
            analysis_timestamp=result.analysis_timestamp
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"섹션 분석 중 오류 발생: {str(e)}")
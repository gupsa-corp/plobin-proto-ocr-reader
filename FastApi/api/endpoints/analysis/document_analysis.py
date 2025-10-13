"""
문서 페이지 분석 API 엔드포인트
"""

import os
import json
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Body, Depends
from fastapi.responses import JSONResponse

from api.models.analysis import (
    DocumentAnalysisRequest,
    DocumentAnalysisResponse,
    SectionAnalysisResponse,
    AnalysisConfigRequest
)
from services.llm import SectionAnalyzer, LLMModel
from services.file.storage import RequestStorage
from .dependencies import get_section_analyzer

router = APIRouter()


@router.post("/documents/{request_id}/pages/{page_number}/analyze", response_model=DocumentAnalysisResponse)
async def analyze_document_page(
    request_id: str,
    page_number: int,
    config: Optional[AnalysisConfigRequest] = Body(None),
    analyzer: SectionAnalyzer = Depends(get_section_analyzer)
):
    """
    OCR 결과의 특정 페이지를 섹션별로 분석

    - **request_id**: 처리 요청 ID (UUID)
    - **page_number**: 페이지 번호 (1부터 시작)
    - **config**: 분석 설정 (모델, 섹션별 설정 등)
    """
    try:
        # OCR 결과 로드
        storage = RequestStorage()

        # 요청 디렉토리 존재 확인
        request_dir = f"output/{request_id}"
        if not os.path.exists(request_dir):
            raise HTTPException(status_code=404, detail="요청을 찾을 수 없습니다")

        # 페이지 OCR 결과 로드
        page_result_path = f"output/{request_id}/pages/{page_number:03d}/result.json"
        if not os.path.exists(page_result_path):
            raise HTTPException(status_code=404, detail="페이지 OCR 결과를 찾을 수 없습니다")

        with open(page_result_path, 'r', encoding='utf-8') as f:
            ocr_result = json.load(f)

        # 분석 설정 준비
        model = config.model if config and config.model else LLMModel.GPT_3_5_TURBO
        section_configs = config.section_configs if config and config.section_configs else None

        # 문서 분석 실행
        result = await analyzer.analyze_document_sections(
            ocr_result=ocr_result,
            request_id=request_id,
            page_number=page_number,
            section_configs=section_configs,
            model=model
        )

        # 분석 결과 저장
        analysis_dir = f"output/{request_id}/pages/{page_number:03d}/analysis"
        os.makedirs(analysis_dir, exist_ok=True)

        analysis_file_path = f"{analysis_dir}/llm_analysis.json"
        with open(analysis_file_path, 'w', encoding='utf-8') as f:
            # dataclass를 dict로 변환하여 저장
            result_dict = {
                "request_id": result.request_id,
                "page_number": result.page_number,
                "sections": [
                    {
                        "section_id": s.section_id,
                        "section_type": s.section_type,
                        "original_text": s.original_text,
                        "analyzed_content": s.analyzed_content,
                        "extracted_data": s.extracted_data,
                        "confidence_score": s.confidence_score,
                        "analysis_timestamp": s.analysis_timestamp,
                        "model_used": s.model_used
                    }
                    for s in result.sections
                ],
                "summary": result.summary,
                "total_processing_time": result.total_processing_time,
                "analysis_timestamp": result.analysis_timestamp
            }
            json.dump(result_dict, f, ensure_ascii=False, indent=2)

        return DocumentAnalysisResponse(
            success=True,
            request_id=result.request_id,
            page_number=result.page_number,
            total_sections=len(result.sections),
            sections=[
                SectionAnalysisResponse(
                    success=True,
                    section_id=s.section_id,
                    section_type=s.section_type,
                    original_text=s.original_text,
                    analyzed_content=s.analyzed_content,
                    extracted_data=s.extracted_data,
                    confidence_score=s.confidence_score,
                    model_used=s.model_used,
                    analysis_timestamp=s.analysis_timestamp
                )
                for s in result.sections
            ],
            summary=result.summary,
            processing_time=result.total_processing_time,
            analysis_timestamp=result.analysis_timestamp,
            analysis_file_path=f"/requests/{request_id}/pages/{page_number}/analysis"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"문서 분석 중 오류 발생: {str(e)}")


@router.get("/documents/{request_id}/pages/{page_number}/analysis", response_model=DocumentAnalysisResponse)
async def get_document_analysis(
    request_id: str,
    page_number: int
):
    """
    저장된 문서 분석 결과 조회

    - **request_id**: 처리 요청 ID (UUID)
    - **page_number**: 페이지 번호 (1부터 시작)
    """
    try:
        # 분석 결과 파일 경로
        analysis_file_path = f"output/{request_id}/pages/{page_number:03d}/analysis/llm_analysis.json"

        if not os.path.exists(analysis_file_path):
            raise HTTPException(status_code=404, detail="분석 결과를 찾을 수 없습니다")

        with open(analysis_file_path, 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)

        # 응답 형식으로 변환
        sections = [
            SectionAnalysisResponse(
                success=True,
                section_id=s["section_id"],
                section_type=s["section_type"],
                original_text=s["original_text"],
                analyzed_content=s["analyzed_content"],
                extracted_data=s["extracted_data"],
                confidence_score=s.get("confidence_score"),
                model_used=s.get("model_used"),
                analysis_timestamp=s["analysis_timestamp"]
            )
            for s in analysis_data["sections"]
        ]

        return DocumentAnalysisResponse(
            success=True,
            request_id=analysis_data["request_id"],
            page_number=analysis_data["page_number"],
            total_sections=len(sections),
            sections=sections,
            summary=analysis_data["summary"],
            processing_time=analysis_data["total_processing_time"],
            analysis_timestamp=analysis_data["analysis_timestamp"],
            analysis_file_path=f"/requests/{request_id}/pages/{page_number}/analysis"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분석 결과 조회 중 오류 발생: {str(e)}")


@router.get("/documents/{request_id}/analysis/summary")
async def get_document_analysis_summary(
    request_id: str,
    include_sections: bool = Query(False, description="섹션별 상세 내용 포함 여부")
):
    """
    전체 문서의 분석 결과 요약 조회

    - **request_id**: 처리 요청 ID (UUID)
    - **include_sections**: 섹션별 상세 내용 포함 여부
    """
    try:
        # 요청 디렉토리 존재 확인
        request_dir = f"output/{request_id}"
        if not os.path.exists(request_dir):
            raise HTTPException(status_code=404, detail="요청을 찾을 수 없습니다")

        # 메타데이터에서 총 페이지 수 확인
        metadata_path = f"output/{request_id}/metadata.json"
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        total_pages = metadata.get("total_pages", 1)
        page_analyses = []

        # 각 페이지의 분석 결과 수집
        for page_num in range(1, total_pages + 1):
            analysis_file_path = f"output/{request_id}/pages/{page_num:03d}/analysis/llm_analysis.json"

            if os.path.exists(analysis_file_path):
                with open(analysis_file_path, 'r', encoding='utf-8') as f:
                    page_analysis = json.load(f)

                page_summary = {
                    "page_number": page_num,
                    "total_sections": len(page_analysis["sections"]),
                    "summary": page_analysis["summary"],
                    "processing_time": page_analysis["total_processing_time"],
                    "analysis_timestamp": page_analysis["analysis_timestamp"]
                }

                if include_sections:
                    page_summary["sections"] = page_analysis["sections"]

                page_analyses.append(page_summary)

        if not page_analyses:
            raise HTTPException(status_code=404, detail="분석 결과가 없습니다")

        # 전체 요약 생성
        total_sections = sum(p["total_sections"] for p in page_analyses)
        total_processing_time = sum(p["processing_time"] for p in page_analyses)

        return JSONResponse({
            "success": True,
            "request_id": request_id,
            "total_pages": total_pages,
            "analyzed_pages": len(page_analyses),
            "total_sections": total_sections,
            "total_processing_time": total_processing_time,
            "pages": page_analyses,
            "summary_timestamp": datetime.now().isoformat()
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분석 요약 조회 중 오류 발생: {str(e)}")


@router.delete("/documents/{request_id}/analysis")
async def delete_document_analysis(request_id: str):
    """
    문서의 모든 분석 결과 삭제

    - **request_id**: 처리 요청 ID (UUID)
    """
    try:
        import shutil

        # 요청 디렉토리 존재 확인
        request_dir = f"output/{request_id}"
        if not os.path.exists(request_dir):
            raise HTTPException(status_code=404, detail="요청을 찾을 수 없습니다")

        # 분석 디렉토리들 삭제
        base_dir = f"output/{request_id}/pages"
        if os.path.exists(base_dir):
            for page_dir in os.listdir(base_dir):
                analysis_dir = os.path.join(base_dir, page_dir, "analysis")
                if os.path.exists(analysis_dir):
                    shutil.rmtree(analysis_dir)

        return JSONResponse({
            "success": True,
            "message": "분석 결과가 삭제되었습니다",
            "request_id": request_id,
            "deleted_timestamp": datetime.now().isoformat()
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분석 결과 삭제 중 오류 발생: {str(e)}")
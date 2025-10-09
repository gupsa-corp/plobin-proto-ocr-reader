"""
LLM 기반 섹션 분석 API 엔드포인트
"""

import os
import json
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Body, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse

from api.models.analysis import (
    SectionAnalysisRequest,
    DocumentAnalysisRequest,
    SectionAnalysisResponse,
    DocumentAnalysisResponse,
    AnalysisConfigRequest,
    IntegratedAnalysisConfig,
    IntegratedProcessResult,
    PageIntegratedResult
)
from services.llm import LLMClient, SectionAnalyzer, LLMModel
from services.file.storage import RequestStorage

router = APIRouter(prefix="/analysis", tags=["Analysis"])

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


@router.get("/models")
async def get_available_models():
    """
    사용 가능한 LLM 모델 목록 조회
    """
    return JSONResponse({
        "success": True,
        "models": [
            {
                "model_id": LLMModel.GPT_4,
                "name": "GPT-4",
                "description": "고성능 범용 언어 모델"
            },
            {
                "model_id": LLMModel.GPT_3_5_TURBO,
                "name": "GPT-3.5 Turbo",
                "description": "빠르고 효율적인 언어 모델 (기본값)"
            },
            {
                "model_id": LLMModel.CLAUDE_3_SONNET,
                "name": "Claude 3 Sonnet",
                "description": "균형잡힌 성능의 Claude 모델"
            },
            {
                "model_id": LLMModel.CLAUDE_3_HAIKU,
                "name": "Claude 3 Haiku",
                "description": "빠른 응답의 Claude 모델"
            }
        ]
    })


@router.get("/debug/api-info")
async def get_llm_api_info():
    """
    LLM API 연결 정보 및 설정 확인
    """
    api_key = os.getenv("GUPSA_AI_API_KEY")

    return JSONResponse({
        "success": True,
        "api_config": {
            "base_url": "https://llm.gupsa.net/v1",
            "api_key_configured": bool(api_key),
            "api_key_preview": f"{api_key[:10]}..." if api_key else None,
            "endpoints": {
                "chat_completions": "/chat/completions",
                "models": "/models",
                "health": "/health"
            }
        },
        "supported_models": [model.value for model in LLMModel],
        "timestamp": datetime.now().isoformat()
    })


@router.get("/debug/test-connection")
async def test_llm_connection():
    """
    다양한 LLM API 엔드포인트 연결 테스트
    """
    results = {}

    # 기본 URL 테스트
    base_urls = [
        "https://llm.gupsa.net",
        "https://llm.gupsa.net/v1",
        "https://ai.gupsa.net/v1",  # 이전 URL
        "https://api.openai.com/v1"  # 비교용
    ]

    for base_url in base_urls:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(base_url)
                results[base_url] = {
                    "status_code": response.status_code,
                    "accessible": response.status_code < 500,
                    "content_type": response.headers.get("content-type", ""),
                    "response_size": len(response.text)
                }
        except Exception as e:
            results[base_url] = {
                "error": str(e),
                "accessible": False
            }

    # Chat completions 엔드포인트 테스트
    chat_endpoints = [
        "https://llm.gupsa.net/v1/chat/completions",
        "https://ai.gupsa.net/v1/chat/completions",  # 이전 URL
        "https://api.openai.com/v1/chat/completions"  # 비교용
    ]

    results["chat_endpoints"] = {}
    for endpoint in chat_endpoints:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # OPTIONS 요청으로 CORS 확인
                response = await client.options(endpoint)
                results["chat_endpoints"][endpoint] = {
                    "options_status": response.status_code,
                    "cors_headers": dict(response.headers)
                }
        except Exception as e:
            results["chat_endpoints"][endpoint] = {
                "error": str(e)
            }

    return JSONResponse({
        "success": True,
        "connection_tests": results,
        "timestamp": datetime.now().isoformat()
    })


@router.post("/debug/manual-request")
async def manual_llm_request(
    url: str = Body(..., description="LLM API URL"),
    method: str = Body("POST", description="HTTP 메서드"),
    headers: Dict[str, str] = Body({}, description="HTTP 헤더"),
    payload: Dict[str, Any] = Body({}, description="요청 페이로드")
):
    """
    수동 LLM API 요청 테스트
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if method.upper() == "GET":
                response = await client.get(url, headers=headers, params=payload)
            elif method.upper() == "POST":
                response = await client.post(url, headers=headers, json=payload)
            else:
                raise ValueError(f"지원하지 않는 HTTP 메서드: {method}")

            return JSONResponse({
                "success": True,
                "request": {
                    "url": url,
                    "method": method,
                    "headers": headers,
                    "payload": payload
                },
                "response": {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "content": response.text[:1000],  # 처음 1000자만
                    "content_length": len(response.text)
                },
                "timestamp": datetime.now().isoformat()
            })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e),
            "request": {
                "url": url,
                "method": method,
                "headers": headers,
                "payload": payload
            },
            "timestamp": datetime.now().isoformat()
        }, status_code=500)


@router.get("/health")
async def check_analysis_health(llm_client: LLMClient = Depends(get_llm_client)):
    """
    LLM 분석 서비스 상태 확인
    """
    try:
        # 간단한 테스트 요청으로 연결 확인
        test_response = await llm_client.analyze_text(
            text="test",
            prompt="Just respond with 'OK'",
            model=LLMModel.GPT_3_5_TURBO
        )

        return JSONResponse({
            "success": True,
            "status": "healthy",
            "llm_connection": "connected",
            "test_response": test_response[:50] if test_response else "No response",
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "status": "unhealthy",
            "llm_connection": "failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, status_code=503)


# 통합 OCR + LLM 분석 API
@router.post("/process-and-analyze", response_model=IntegratedProcessResult)
async def process_and_analyze_document(
    file: UploadFile = File(..., description="분석할 문서 파일"),
    description: Optional[str] = Form(None, description="요청 설명"),
    analysis_config: Optional[str] = Form(None, description="분석 설정 (JSON)"),
    analyzer: SectionAnalyzer = Depends(get_section_analyzer)
):
    """
    파일 업로드 → OCR 처리 → LLM 분석을 한번에 수행하는 통합 API

    - **file**: 분석할 문서 파일 (이미지 또는 PDF)
    - **description**: 요청 설명 (선택사항)
    - **analysis_config**: LLM 분석 설정 JSON (선택사항)

    전체 과정:
    1. 파일 업로드 및 검증
    2. OCR 처리 (PaddleOCR)
    3. LLM 분석 (섹션별 또는 전체)
    4. 통합 결과 반환
    """
    import time
    from pathlib import Path
    from fastapi import UploadFile, File, Form

    total_start_time = time.time()

    try:
        # 1. 분석 설정 파싱
        config = IntegratedAnalysisConfig()
        if analysis_config:
            try:
                config_dict = json.loads(analysis_config)
                config = IntegratedAnalysisConfig(**config_dict)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"분석 설정 JSON 파싱 오류: {str(e)}")

        # 2. 파일 검증
        if not file.filename:
            raise HTTPException(status_code=400, detail="파일명이 필요합니다")

        file_extension = Path(file.filename).suffix.lower()
        supported_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp', '.pdf'}

        if file_extension not in supported_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"지원하지 않는 파일 형식입니다. 지원 형식: {', '.join(supported_extensions)}"
            )

        # 3. OCR 처리 단계
        ocr_start_time = time.time()

        # 임시 파일 저장
        import tempfile
        import shutil

        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_file_path = temp_file.name

        try:
            # OCR 처리 (기존 process-request API 로직 재사용)
            from services.ocr import DocumentBlockExtractor
            from services.pdf import PDFToImageProcessor
            from services.file.request_manager import generate_request_metadata, create_request_structure

            # 의존성 초기화
            extractor = DocumentBlockExtractor(use_gpu=False)
            pdf_processor = PDFToImageProcessor() if file_extension == '.pdf' else None

            # 요청 ID 생성
            from services.file.request_manager import generate_uuid_v7
            request_id = generate_uuid_v7()

            # 메타데이터 생성
            file_size = os.path.getsize(temp_file_path)
            metadata = generate_request_metadata(file.filename, file_extension[1:], file_size, description)

            # 요청 구조 생성
            output_dir = "output"
            create_request_structure(output_dir, request_id)

            # OCR 처리 실행
            if file_extension == '.pdf':
                # PDF 처리
                images = pdf_processor.convert_pdf_to_images(temp_file_path)
                total_pages = len(images)

                all_results = []
                total_blocks = 0
                confidence_scores = []

                for page_num, image in enumerate(images, 1):
                    # OCR 실행 (이미지를 임시 저장해서 경로로 전달)
                    import tempfile
                    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_img:
                        cv2.imwrite(temp_img.name, image)
                        result = extractor.extract_blocks(temp_img.name)
                        os.unlink(temp_img.name)
                    all_results.append(result)

                    # 블록 수 및 신뢰도 수집
                    if 'text_blocks' in result:
                        total_blocks += len(result['text_blocks'])
                        for block in result['text_blocks']:
                            if 'confidence' in block:
                                confidence_scores.append(block['confidence'])

                    # 페이지 결과 저장
                    storage = RequestStorage(output_dir)
                    blocks = result.get('blocks', [])
                    page_processing_time = 0.0

                    storage.save_page_result(
                        request_id=request_id,
                        page_number=page_num,
                        blocks=blocks,
                        processing_time=page_processing_time
                    )

            else:
                # 이미지 처리
                import cv2
                import numpy as np

                image = cv2.imread(temp_file_path)
                if image is None:
                    raise HTTPException(status_code=400, detail="이미지 파일을 읽을 수 없습니다")

                result = extractor.extract_blocks(temp_file_path)

                all_results = [result]
                total_pages = 1

                # 블록 수 및 신뢰도 수집
                total_blocks = 0
                confidence_scores = []
                if 'text_blocks' in result:
                    total_blocks = len(result['text_blocks'])
                    for block in result['text_blocks']:
                        if 'confidence' in block:
                            confidence_scores.append(block['confidence'])

                # 페이지 결과 저장
                storage = RequestStorage(output_dir)
                blocks = result.get('blocks', [])
                page_processing_time = 0.0

                storage.save_page_result(
                    request_id=request_id,
                    page_number=1,
                    blocks=blocks,
                    processing_time=page_processing_time
                )

            ocr_end_time = time.time()
            ocr_processing_time = ocr_end_time - ocr_start_time
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0

            # 4. LLM 분석 단계 (설정에 따라)
            llm_start_time = time.time()
            llm_analysis_performed = False
            llm_processing_time = 0.0
            llm_model_used = None

            if config.perform_llm_analysis:
                llm_analysis_performed = True
                llm_model_used = config.model

                for page_num in range(1, total_pages + 1):
                    # 각 페이지에 대해 LLM 분석 수행
                    try:
                        analysis_result = await analyzer.analyze_document_sections(
                            ocr_result=all_results[page_num - 1],
                            request_id=request_id,
                            page_number=page_num,
                            section_configs=config.section_configs,
                            model=config.model
                        )

                        # 분석 결과 저장
                        analysis_dir = f"output/{request_id}/pages/{page_num:03d}/analysis"
                        os.makedirs(analysis_dir, exist_ok=True)

                        analysis_file_path = f"{analysis_dir}/llm_analysis.json"
                        with open(analysis_file_path, 'w', encoding='utf-8') as f:
                            result_dict = {
                                "request_id": analysis_result.request_id,
                                "page_number": analysis_result.page_number,
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
                                    for s in analysis_result.sections
                                ],
                                "summary": analysis_result.summary,
                                "total_processing_time": analysis_result.total_processing_time,
                                "analysis_timestamp": analysis_result.analysis_timestamp
                            }
                            json.dump(result_dict, f, ensure_ascii=False, indent=2)

                    except Exception as e:
                        # LLM 분석 실패해도 OCR 결과는 반환
                        print(f"LLM 분석 실패 (페이지 {page_num}): {str(e)}")

            llm_end_time = time.time()
            if llm_analysis_performed:
                llm_processing_time = llm_end_time - llm_start_time

            # 5. 통합 결과 생성
            total_end_time = time.time()
            total_processing_time = total_end_time - total_start_time

            # 페이지별 통합 결과 생성
            pages_results = []
            document_summary = None
            extracted_data = {}

            for page_num in range(1, total_pages + 1):
                # OCR 결과에서 텍스트 추출
                page_result = all_results[page_num - 1]
                extracted_text = ""
                page_blocks = 0
                page_confidence = 0.0

                if 'text_blocks' in page_result:
                    page_blocks = len(page_result['text_blocks'])
                    texts = []
                    confidences = []

                    for block in page_result['text_blocks']:
                        if 'text' in block:
                            texts.append(block['text'])
                        if 'confidence' in block:
                            confidences.append(block['confidence'])

                    extracted_text = " ".join(texts)
                    page_confidence = sum(confidences) / len(confidences) if confidences else 0.0

                # LLM 분석 결과 로드 (있는 경우)
                llm_analysis = None
                sections_analyzed = None

                if llm_analysis_performed:
                    analysis_file_path = f"output/{request_id}/pages/{page_num:03d}/analysis/llm_analysis.json"
                    if os.path.exists(analysis_file_path):
                        try:
                            with open(analysis_file_path, 'r', encoding='utf-8') as f:
                                llm_analysis = json.load(f)
                                sections_analyzed = len(llm_analysis.get('sections', []))

                                # 첫 페이지의 요약을 문서 요약으로 사용
                                if page_num == 1 and 'summary' in llm_analysis:
                                    document_summary = llm_analysis['summary']

                                # 추출된 데이터 통합
                                for section in llm_analysis.get('sections', []):
                                    if 'extracted_data' in section:
                                        extracted_data.update(section['extracted_data'])

                        except Exception as e:
                            print(f"LLM 분석 결과 로드 실패 (페이지 {page_num}): {str(e)}")

                # 페이지 결과 객체 생성
                page_integrated = PageIntegratedResult(
                    page_number=page_num,
                    ocr_confidence=page_confidence,
                    text_blocks_count=page_blocks,
                    extracted_text=extracted_text,
                    llm_analysis=llm_analysis,
                    sections_analyzed=sections_analyzed,
                    original_image_url=f"/requests/{request_id}/pages/{page_num}/original",
                    visualization_url=f"/requests/{request_id}/pages/{page_num}/visualization",
                    detailed_ocr_url=f"/requests/{request_id}/pages/{page_num}",
                    detailed_analysis_url=f"/analysis/documents/{request_id}/pages/{page_num}/analysis" if llm_analysis_performed else None
                )
                pages_results.append(page_integrated)

            # 최종 통합 결과 생성
            result = IntegratedProcessResult(
                success=True,
                request_id=request_id,
                original_filename=file.filename,
                file_type=file_extension[1:],
                file_size=file_size,
                total_pages=total_pages,
                ocr_processing_time=ocr_processing_time,
                ocr_confidence=avg_confidence,
                total_text_blocks=total_blocks,
                llm_analysis_performed=llm_analysis_performed,
                llm_processing_time=llm_processing_time if llm_analysis_performed else None,
                llm_model_used=llm_model_used,
                total_processing_time=total_processing_time,
                pages=pages_results,
                document_summary=document_summary,
                extracted_data=extracted_data if extracted_data else None,
                processing_url=f"/requests/{request_id}",
                analysis_url=f"/analysis/documents/{request_id}/analysis/summary" if llm_analysis_performed else None,
                timestamp=datetime.now().isoformat()
            )

            # 6. 통합 결과를 JSON 파일로 저장
            try:
                integrated_result_path = f"output/{request_id}/integrated_result.json"

                # Pydantic 모델을 dict로 변환
                result_dict = result.model_dump()

                # JSON 파일로 저장
                with open(integrated_result_path, 'w', encoding='utf-8') as f:
                    json.dump(result_dict, f, ensure_ascii=False, indent=2)

                print(f"통합 결과 저장 완료: {integrated_result_path}")

            except Exception as e:
                print(f"통합 결과 JSON 저장 실패: {str(e)}")
                # 저장 실패해도 API 응답은 반환

            return result

        finally:
            # 임시 파일 정리
            try:
                os.unlink(temp_file_path)
            except:
                pass

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통합 처리 중 오류 발생: {str(e)}")


@router.get("/integrated-results/{request_id}")
async def get_integrated_result(request_id: str):
    """
    저장된 통합 분석 결과 JSON 파일 조회

    - **request_id**: 처리 요청 ID (UUID)

    Returns:
        저장된 통합 분석 결과 전체 데이터
    """
    try:
        # 요청 디렉토리 존재 확인
        request_dir = f"output/{request_id}"
        if not os.path.exists(request_dir):
            raise HTTPException(status_code=404, detail="요청을 찾을 수 없습니다")

        # 통합 결과 JSON 파일 경로
        integrated_result_path = f"output/{request_id}/integrated_result.json"

        if not os.path.exists(integrated_result_path):
            raise HTTPException(status_code=404, detail="통합 분석 결과를 찾을 수 없습니다")

        # JSON 파일 로드
        with open(integrated_result_path, 'r', encoding='utf-8') as f:
            result_data = json.load(f)

        return JSONResponse({
            "success": True,
            "request_id": request_id,
            "file_path": f"/analysis/integrated-results/{request_id}",
            "data": result_data,
            "retrieved_timestamp": datetime.now().isoformat()
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통합 결과 조회 중 오류 발생: {str(e)}")


@router.get("/integrated-results/{request_id}/download")
async def download_integrated_result(request_id: str):
    """
    통합 분석 결과 JSON 파일 다운로드

    - **request_id**: 처리 요청 ID (UUID)

    Returns:
        JSON 파일을 직접 다운로드
    """
    from fastapi.responses import FileResponse

    try:
        # 요청 디렉토리 존재 확인
        request_dir = f"output/{request_id}"
        if not os.path.exists(request_dir):
            raise HTTPException(status_code=404, detail="요청을 찾을 수 없습니다")

        # 통합 결과 JSON 파일 경로
        integrated_result_path = f"output/{request_id}/integrated_result.json"

        if not os.path.exists(integrated_result_path):
            raise HTTPException(status_code=404, detail="통합 분석 결과를 찾을 수 없습니다")

        # 파일 다운로드 응답
        return FileResponse(
            path=integrated_result_path,
            filename=f"integrated_result_{request_id}.json",
            media_type="application/json"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 다운로드 중 오류 발생: {str(e)}")


@router.get("/integrated-results")
async def list_integrated_results(
    limit: int = Query(10, ge=1, le=100, description="조회할 결과 수"),
    offset: int = Query(0, ge=0, description="건너뛸 결과 수")
):
    """
    통합 분석 결과 목록 조회

    - **limit**: 조회할 결과 수 (기본값: 10, 최대: 100)
    - **offset**: 건너뛸 결과 수 (페이징용)

    Returns:
        통합 분석 결과 목록 및 요약 정보
    """
    try:
        output_dir = "output"
        if not os.path.exists(output_dir):
            return JSONResponse({
                "success": True,
                "total_count": 0,
                "results": [],
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "has_more": False
                },
                "timestamp": datetime.now().isoformat()
            })

        # 모든 요청 디렉토리 찾기
        all_requests = []
        for item in os.listdir(output_dir):
            request_path = os.path.join(output_dir, item)
            if os.path.isdir(request_path):
                integrated_result_path = os.path.join(request_path, "integrated_result.json")

                if os.path.exists(integrated_result_path):
                    try:
                        # 파일 수정 시간과 기본 정보 가져오기
                        stat = os.stat(integrated_result_path)
                        file_mtime = datetime.fromtimestamp(stat.st_mtime)

                        # JSON 파일에서 기본 정보 읽기
                        with open(integrated_result_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)

                        all_requests.append({
                            "request_id": item,
                            "original_filename": data.get("original_filename", "Unknown"),
                            "file_type": data.get("file_type", "Unknown"),
                            "total_pages": data.get("total_pages", 0),
                            "llm_analysis_performed": data.get("llm_analysis_performed", False),
                            "llm_model_used": data.get("llm_model_used"),
                            "total_processing_time": data.get("total_processing_time", 0),
                            "timestamp": data.get("timestamp"),
                            "file_modified": file_mtime.isoformat(),
                            "json_file_url": f"/analysis/integrated-results/{item}",
                            "download_url": f"/analysis/integrated-results/{item}/download"
                        })

                    except Exception as e:
                        print(f"Error reading integrated result for {item}: {str(e)}")
                        continue

        # 시간순 정렬 (최신순)
        all_requests.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        # 페이징 적용
        total_count = len(all_requests)
        paginated_results = all_requests[offset:offset + limit]
        has_more = offset + limit < total_count

        return JSONResponse({
            "success": True,
            "total_count": total_count,
            "results": paginated_results,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "has_more": has_more,
                "next_offset": offset + limit if has_more else None
            },
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"결과 목록 조회 중 오류 발생: {str(e)}")
"""
통합 OCR + LLM 분석 API 엔드포인트
"""

import os
import json
import time
import tempfile
import shutil
import cv2
from typing import Optional
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse, FileResponse

from api.models.analysis import IntegratedAnalysisConfig, IntegratedProcessResult, PageIntegratedResult
from services.llm import SectionAnalyzer
from services.file.storage import RequestStorage
from .dependencies import get_section_analyzer

router = APIRouter()


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
                pdf_output_dir = f"{output_dir}/{request_id}/pages"
                images = pdf_processor.convert_pdf_to_images(temp_file_path, pdf_output_dir)
                total_pages = len(images)

                all_results = []
                total_blocks = 0
                confidence_scores = []

                for page_num, image_path in enumerate(images, 1):
                    # OCR 실행 (이미 저장된 이미지 경로 사용)
                    result = extractor.extract_blocks(image_path)
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
        integrated_result_path = f"output/{request_id}/integrated_result.json"

        if not os.path.exists(integrated_result_path):
            raise HTTPException(status_code=404, detail="통합 분석 결과를 찾을 수 없습니다")

        with open(integrated_result_path, 'r', encoding='utf-8') as f:
            result_data = json.load(f)

        return JSONResponse({
            "success": True,
            "request_id": request_id,
            "data": result_data,
            "file_path": f"/analysis/integrated-results/{request_id}",
            "download_url": f"/analysis/integrated-results/{request_id}/download",
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
        JSON 파일 다운로드
    """
    try:
        integrated_result_path = f"output/{request_id}/integrated_result.json"

        if not os.path.exists(integrated_result_path):
            raise HTTPException(status_code=404, detail="통합 분석 결과 파일을 찾을 수 없습니다")

        return FileResponse(
            path=integrated_result_path,
            filename=f"integrated_analysis_{request_id}.json",
            media_type="application/json"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 다운로드 중 오류 발생: {str(e)}")


@router.get("/integrated-results")
async def list_integrated_results(
    page: int = 1,
    limit: int = 20,
    sort_by: str = "timestamp",
    order: str = "desc"
):
    """
    통합 분석 결과 목록 조회 (페이징 지원)

    - **page**: 페이지 번호 (1부터 시작)
    - **limit**: 페이지당 항목 수 (최대 100)
    - **sort_by**: 정렬 기준 (timestamp, filename, file_size)
    - **order**: 정렬 순서 (asc, desc)

    Returns:
        통합 분석 결과 목록과 페이징 정보
    """
    try:
        if limit > 100:
            limit = 100

        output_dir = "output"
        if not os.path.exists(output_dir):
            return JSONResponse({
                "success": True,
                "results": [],
                "pagination": {
                    "current_page": page,
                    "total_pages": 0,
                    "total_items": 0,
                    "items_per_page": limit
                }
            })

        # 통합 결과가 있는 디렉토리들 찾기
        integrated_results = []

        for item in os.listdir(output_dir):
            item_path = os.path.join(output_dir, item)
            if os.path.isdir(item_path):
                integrated_result_path = os.path.join(item_path, "integrated_result.json")
                if os.path.exists(integrated_result_path):
                    try:
                        # 파일 정보 수집
                        stat = os.stat(integrated_result_path)
                        file_size = stat.st_size
                        timestamp = datetime.fromtimestamp(stat.st_mtime)

                        # JSON 파일에서 메타데이터 로드 (선택적)
                        metadata = None
                        try:
                            with open(integrated_result_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                metadata = {
                                    "original_filename": data.get("original_filename"),
                                    "file_type": data.get("file_type"),
                                    "total_pages": data.get("total_pages"),
                                    "ocr_confidence": data.get("ocr_confidence"),
                                    "llm_analysis_performed": data.get("llm_analysis_performed"),
                                    "processing_time": data.get("total_processing_time")
                                }
                        except:
                            pass

                        integrated_results.append({
                            "request_id": item,
                            "file_size": file_size,
                            "timestamp": timestamp,
                            "metadata": metadata,
                            "json_file_url": f"/analysis/integrated-results/{item}",
                            "download_url": f"/analysis/integrated-results/{item}/download"
                        })

                    except Exception as e:
                        print(f"통합 결과 정보 수집 실패 ({item}): {str(e)}")
                        continue

        # 정렬
        reverse = (order == "desc")
        if sort_by == "timestamp":
            integrated_results.sort(key=lambda x: x["timestamp"], reverse=reverse)
        elif sort_by == "filename":
            integrated_results.sort(key=lambda x: x["metadata"]["original_filename"] if x["metadata"] else "", reverse=reverse)
        elif sort_by == "file_size":
            integrated_results.sort(key=lambda x: x["file_size"], reverse=reverse)

        # 페이징 계산
        total_items = len(integrated_results)
        total_pages = (total_items + limit - 1) // limit
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit

        # 결과 슬라이싱
        paginated_results = integrated_results[start_idx:end_idx]

        # timestamp를 문자열로 변환
        for result in paginated_results:
            result["timestamp"] = result["timestamp"].isoformat()

        return JSONResponse({
            "success": True,
            "results": paginated_results,
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_items": total_items,
                "items_per_page": limit
            },
            "query_timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통합 결과 목록 조회 중 오류 발생: {str(e)}")
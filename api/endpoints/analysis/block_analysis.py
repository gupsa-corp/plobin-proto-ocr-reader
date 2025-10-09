"""
블록별 분석 API 엔드포인트
"""

import os
import json
import re
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Body, Depends

from services.llm import SectionAnalyzer
from .dependencies import get_section_analyzer

router = APIRouter()


@router.post("/analyze-blocks/{request_id}/pages/{page_number}")
async def analyze_blocks_with_llm(
    request_id: str,
    page_number: int,
    config: Optional[Dict[str, Any]] = Body(None, description="블록별 분석 설정"),
    analyzer: SectionAnalyzer = Depends(get_section_analyzer)
):
    """
    기존 OCR 결과의 각 블록에 대해 개별 LLM 분석 수행

    - **request_id**: 기존 OCR 요청 ID
    - **page_number**: 페이지 번호
    - **config**: 블록별 분석 설정 (모델, 분석 타입 등)

    각 블록을 개별적으로 분석하여 구조화된 데이터 추출
    """
    try:
        # 기본 설정
        model = config.get("model", "boto") if config else "boto"
        analysis_type = config.get("analysis_type", "auto") if config else "auto"

        # 기존 OCR 결과 로드
        page_result_path = f"output/{request_id}/pages/{page_number:03d}/result.json"

        if not os.path.exists(page_result_path):
            raise HTTPException(status_code=404, detail="OCR 결과를 찾을 수 없습니다")

        with open(page_result_path, 'r', encoding='utf-8') as f:
            page_result = json.load(f)

        blocks = page_result.get("blocks", [])
        if not blocks:
            raise HTTPException(status_code=404, detail="분석할 블록이 없습니다")

        # 블록별 분석 결과 저장
        analyzed_blocks = []

        for block in blocks:
            block_text = block.get("text", "")
            block_id = block.get("id")

            if not block_text.strip():
                continue

            # 블록 유형 자동 감지
            detected_type = _detect_block_type(block_text, analysis_type)

            try:
                # 블록별 LLM 분석 수행
                analysis_result = await analyzer.analyze_section(
                    section_text=block_text,
                    section_type=detected_type,
                    model=model
                )

                analyzed_block = {
                    "block_id": block_id,
                    "original_text": block_text,
                    "block_type": detected_type,
                    "confidence": block.get("confidence"),
                    "bbox": block.get("bbox"),
                    "llm_analysis": {
                        "analyzed_content": analysis_result.analyzed_content,
                        "extracted_data": analysis_result.extracted_data,
                        "confidence_score": analysis_result.confidence_score,
                        "model_used": analysis_result.model_used,
                        "analysis_timestamp": analysis_result.analysis_timestamp
                    }
                }
                analyzed_blocks.append(analyzed_block)

            except Exception as e:
                # 개별 블록 분석 실패시 원본 정보만 포함
                analyzed_blocks.append({
                    "block_id": block_id,
                    "original_text": block_text,
                    "block_type": detected_type,
                    "confidence": block.get("confidence"),
                    "bbox": block.get("bbox"),
                    "llm_analysis": None,
                    "error": str(e)
                })

        # 분석 결과 저장
        analysis_dir = f"output/{request_id}/pages/{page_number:03d}/analysis"
        os.makedirs(analysis_dir, exist_ok=True)

        block_analysis_result = {
            "request_id": request_id,
            "page_number": page_number,
            "total_blocks": len(blocks),
            "analyzed_blocks": len(analyzed_blocks),
            "model_used": model,
            "analysis_type": analysis_type,
            "timestamp": datetime.now().isoformat(),
            "blocks": analyzed_blocks
        }

        analysis_file_path = f"{analysis_dir}/block_analysis.json"
        with open(analysis_file_path, 'w', encoding='utf-8') as f:
            json.dump(block_analysis_result, f, ensure_ascii=False, indent=2)

        return {
            "success": True,
            "request_id": request_id,
            "page_number": page_number,
            "total_blocks": len(blocks),
            "analyzed_blocks": len(analyzed_blocks),
            "model_used": model,
            "analysis_type": analysis_type,
            "blocks": analyzed_blocks,
            "saved_file": f"/analysis/blocks/{request_id}/pages/{page_number}",
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"블록 분석 중 오류 발생: {str(e)}")


@router.get("/analyze-blocks/{request_id}/pages/{page_number}")
async def get_block_analysis_result(
    request_id: str,
    page_number: int
):
    """저장된 블록별 분석 결과 조회"""
    try:
        analysis_file_path = f"output/{request_id}/pages/{page_number:03d}/analysis/block_analysis.json"

        if not os.path.exists(analysis_file_path):
            raise HTTPException(status_code=404, detail="블록 분석 결과를 찾을 수 없습니다")

        with open(analysis_file_path, 'r', encoding='utf-8') as f:
            analysis_result = json.load(f)

        return {
            "success": True,
            "data": analysis_result,
            "retrieved_timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"결과 조회 중 오류 발생: {str(e)}")


def _detect_block_type(text: str, analysis_type: str = "auto") -> str:
    """텍스트 내용을 기반으로 블록 유형 자동 감지"""
    if analysis_type != "auto":
        return analysis_type

    text_lower = text.lower()

    # 가격/금액 패턴
    price_patterns = [r'\d+[,\s]*(?:원|won|₩)', r'\d+[,\s]*(?:달러|\$)', r'total[:\s]*\d+', r'합계[:\s]*\d+']
    for pattern in price_patterns:
        if re.search(pattern, text_lower):
            return "price"

    # 연락처 패턴
    contact_patterns = [r'phone|tel|전화', r'\d{2,3}[-\s]\d{3,4}[-\s]\d{4}', r'email|메일']
    for pattern in contact_patterns:
        if re.search(pattern, text_lower):
            return "contact"

    # 주소 패턴
    address_patterns = [r'address|주소', r'구|동|로|길', r'seoul|busan|대구|인천']
    for pattern in address_patterns:
        if re.search(pattern, text_lower):
            return "address"

    # 메뉴/상품 패턴
    menu_patterns = [r'menu|메뉴', r'americano|latte|coffee|커피', r'cake|케이크']
    for pattern in menu_patterns:
        if re.search(pattern, text_lower):
            return "menu"

    # 제목 패턴 (첫 번째 블록이거나 짧은 텍스트)
    if len(text) < 30 and any(word in text_lower for word in ['receipt', '영수증', 'cafe', 'restaurant']):
        return "title"

    # 결제 패턴
    payment_patterns = [r'payment|결제|card|cash|현금']
    for pattern in payment_patterns:
        if re.search(pattern, text_lower):
            return "payment"

    return "general"
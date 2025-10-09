"""
문서 요약 API 엔드포인트
"""

import os
import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Body, Depends

from services.llm import SectionAnalyzer
from .dependencies import get_section_analyzer

router = APIRouter()


@router.post("/documents/{request_id}/summarize")
async def create_document_summary(
    request_id: str,
    config: Optional[Dict[str, Any]] = Body(None, description="요약 설정"),
    analyzer: SectionAnalyzer = Depends(get_section_analyzer)
):
    """
    문서 전체에 대한 종합 요약 생성

    - **request_id**: 문서 요청 ID
    - **config**: 요약 설정 (모델, 요약 타입, 세부 옵션 등)

    모든 페이지와 블록을 종합하여 문서 전체 요약 생성
    폴더 구조:
    - summary_sources/ : 요약 근거 데이터
    - summary_results/ : 최종 요약 결과
    """
    try:
        # 기본 설정
        model = config.get("model", "boto") if config else "boto"
        summary_type = config.get("summary_type", "comprehensive") if config else "comprehensive"
        include_raw_data = config.get("include_raw_data", True) if config else True

        # 문서 기본 정보 확인
        request_dir = f"output/{request_id}"
        if not os.path.exists(request_dir):
            raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")

        # 요약 디렉토리 생성
        summary_base_dir = f"{request_dir}/summary"
        summary_sources_dir = f"{summary_base_dir}/sources"
        summary_results_dir = f"{summary_base_dir}/results"

        os.makedirs(summary_sources_dir, exist_ok=True)
        os.makedirs(summary_results_dir, exist_ok=True)

        # 1. 모든 페이지의 OCR 결과 수집
        pages_dir = f"{request_dir}/pages"
        if not os.path.exists(pages_dir):
            raise HTTPException(status_code=404, detail="페이지 데이터를 찾을 수 없습니다")

        all_pages_data = []
        total_blocks = 0
        document_text_blocks = []

        # 페이지별 데이터 수집
        for page_folder in sorted(os.listdir(pages_dir)):
            if not page_folder.isdigit() and not (len(page_folder) == 3 and page_folder.isdigit()):
                continue

            page_number = int(page_folder)
            page_result_path = f"{pages_dir}/{page_folder}/result.json"

            if os.path.exists(page_result_path):
                with open(page_result_path, 'r', encoding='utf-8') as f:
                    page_data = json.load(f)

                all_pages_data.append({
                    "page_number": page_number,
                    "data": page_data
                })

                # 텍스트 블록 수집
                if "blocks" in page_data:
                    total_blocks += len(page_data["blocks"])
                    for block in page_data["blocks"]:
                        if "text" in block and block["text"].strip():
                            document_text_blocks.append({
                                "page": page_number,
                                "block_id": block.get("id"),
                                "text": block["text"],
                                "confidence": block.get("confidence", 0),
                                "type": block.get("type", "unknown"),
                                "bbox": block.get("bbox", {})
                            })

        if not all_pages_data:
            raise HTTPException(status_code=404, detail="분석할 페이지 데이터가 없습니다")

        # 2. 요약 근거 데이터 저장 (sources)
        source_data = {
            "request_id": request_id,
            "collection_timestamp": datetime.now().isoformat(),
            "total_pages": len(all_pages_data),
            "total_blocks": total_blocks,
            "pages_data": all_pages_data,
            "text_blocks": document_text_blocks,
            "summary_config": {
                "model": model,
                "summary_type": summary_type,
                "include_raw_data": include_raw_data
            }
        }

        # 요약 근거 저장
        source_file_path = f"{summary_sources_dir}/document_source_data.json"
        with open(source_file_path, 'w', encoding='utf-8') as f:
            json.dump(source_data, f, ensure_ascii=False, indent=2)

        # 3. 전체 문서 텍스트 구성
        full_document_text = ""
        page_summaries = []

        for page_info in all_pages_data:
            page_number = page_info["page_number"]
            page_blocks = page_info["data"].get("blocks", [])

            page_text = " ".join([block.get("text", "") for block in page_blocks if block.get("text", "").strip()])
            if page_text.strip():
                full_document_text += f"\n\n--- 페이지 {page_number} ---\n{page_text}"
                page_summaries.append({
                    "page": page_number,
                    "text": page_text,
                    "block_count": len(page_blocks)
                })

        # 4. LLM을 통한 문서 전체 요약 생성
        summary_prompt = _generate_summary_prompt(summary_type)

        try:
            summary_result = await analyzer.analyze_section(
                section_text=full_document_text,
                section_type="document_summary",
                analysis_prompt=summary_prompt,
                model=model
            )

            # 5. 요약 결과 데이터 구성
            summary_data = {
                "request_id": request_id,
                "summary_type": summary_type,
                "model_used": model,
                "generation_timestamp": datetime.now().isoformat(),
                "document_overview": {
                    "total_pages": len(all_pages_data),
                    "total_blocks": total_blocks,
                    "total_characters": len(full_document_text),
                    "estimated_reading_time": len(full_document_text) // 200  # 200자/분 기준
                },
                "main_summary": {
                    "title": _extract_document_title(document_text_blocks),
                    "document_type": _detect_document_type(document_text_blocks),
                    "key_information": _extract_key_information(document_text_blocks),
                    "full_summary": summary_result.analyzed_content,
                    "structured_data": summary_result.extracted_data
                },
                "page_summaries": page_summaries,
                "quality_metrics": {
                    "average_confidence": sum(block["confidence"] for block in document_text_blocks) / max(len(document_text_blocks), 1),
                    "low_confidence_blocks": len([b for b in document_text_blocks if b["confidence"] < 0.8]),
                    "empty_blocks": total_blocks - len(document_text_blocks)
                },
                "source_reference": f"summary/sources/document_source_data.json"
            }

        except Exception as e:
            # LLM 분석 실패 시 기본 요약 제공
            summary_data = {
                "request_id": request_id,
                "summary_type": summary_type,
                "model_used": model,
                "generation_timestamp": datetime.now().isoformat(),
                "document_overview": {
                    "total_pages": len(all_pages_data),
                    "total_blocks": total_blocks,
                    "total_characters": len(full_document_text)
                },
                "main_summary": {
                    "title": _extract_document_title(document_text_blocks),
                    "document_type": _detect_document_type(document_text_blocks),
                    "key_information": _extract_key_information(document_text_blocks),
                    "full_summary": "LLM 분석 실패로 인한 기본 요약 제공",
                    "structured_data": {}
                },
                "error": f"LLM 요약 생성 실패: {str(e)}",
                "source_reference": f"summary/sources/document_source_data.json"
            }

        # 6. 요약 결과 저장
        result_file_path = f"{summary_results_dir}/document_summary.json"
        with open(result_file_path, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, ensure_ascii=False, indent=2)

        # 7. 메타데이터 파일 생성
        metadata = {
            "request_id": request_id,
            "created_at": datetime.now().isoformat(),
            "summary_type": summary_type,
            "model_used": model,
            "total_pages": len(all_pages_data),
            "total_blocks": total_blocks,
            "files": {
                "source_data": "sources/document_source_data.json",
                "summary_result": "results/document_summary.json"
            },
            "api_endpoints": {
                "view_summary": f"/analysis/documents/{request_id}/summary",
                "download_sources": f"/analysis/documents/{request_id}/summary/sources",
                "download_results": f"/analysis/documents/{request_id}/summary/results"
            }
        }

        metadata_file_path = f"{summary_base_dir}/metadata.json"
        with open(metadata_file_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        return {
            "success": True,
            "request_id": request_id,
            "summary_type": summary_type,
            "model_used": model,
            "total_pages": len(all_pages_data),
            "total_blocks": total_blocks,
            "summary_overview": summary_data.get("main_summary", {}),
            "folders_created": {
                "summary_base": f"summary/",
                "sources": f"summary/sources/",
                "results": f"summary/results/"
            },
            "files_generated": [
                "summary/sources/document_source_data.json",
                "summary/results/document_summary.json",
                "summary/metadata.json"
            ],
            "access_urls": {
                "view_summary": f"/analysis/documents/{request_id}/summary",
                "download_sources": f"/analysis/documents/{request_id}/summary/sources",
                "download_results": f"/analysis/documents/{request_id}/summary/results"
            },
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"문서 요약 생성 중 오류 발생: {str(e)}")


@router.get("/documents/{request_id}/summary")
async def get_document_summary(request_id: str):
    """저장된 문서 전체 요약 조회"""
    try:
        summary_file_path = f"output/{request_id}/summary/results/document_summary.json"

        if not os.path.exists(summary_file_path):
            raise HTTPException(status_code=404, detail="문서 요약을 찾을 수 없습니다")

        with open(summary_file_path, 'r', encoding='utf-8') as f:
            summary_data = json.load(f)

        return {
            "success": True,
            "data": summary_data,
            "retrieved_timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"요약 조회 중 오류 발생: {str(e)}")


def _generate_summary_prompt(summary_type: str) -> str:
    """요약 타입에 따른 프롬프트 생성"""
    prompts = {
        "comprehensive": """
다음 문서를 종합적으로 분석하고 요약해주세요.

1. 문서 개요 및 목적
2. 주요 내용 요약 (핵심 정보 중심)
3. 중요한 수치/데이터 정리
4. 날짜, 금액, 당사자 등 핵심 정보 추출
5. 문서의 특이사항이나 주의할 점

JSON 형태로 구조화된 데이터도 함께 제공해주세요.
""",
        "brief": """
다음 문서를 간단히 요약해주세요.

1. 문서 유형 및 주제
2. 핵심 내용 (3-5줄)
3. 중요한 숫자나 날짜
4. 결론 또는 요점

간결하고 명확하게 작성해주세요.
""",
        "detailed": """
다음 문서를 상세히 분석하고 요약해주세요.

1. 문서 배경 및 맥락
2. 페이지별 상세 내용 분석
3. 각 섹션별 중요도 평가
4. 데이터 정확성 및 완성도 검토
5. 비즈니스/법적 함의 분석
6. 개선 제안사항

전문적이고 체계적으로 분석해주세요.
"""
    }
    return prompts.get(summary_type, prompts["comprehensive"])


def _extract_document_title(text_blocks: List[Dict]) -> str:
    """문서 제목 추출"""
    if not text_blocks:
        return "제목 없음"

    # 첫 번째 블록이나 가장 신뢰도 높은 블록을 제목으로 간주
    title_candidates = []

    for block in text_blocks[:3]:  # 처음 3개 블록에서 제목 찾기
        text = block.get("text", "").strip()
        if text and len(text) < 100:  # 제목은 보통 짧음
            title_candidates.append({
                "text": text,
                "confidence": block.get("confidence", 0),
                "length": len(text)
            })

    if title_candidates:
        # 신뢰도가 높고 적절한 길이인 것 선택
        best_title = max(title_candidates, key=lambda x: x["confidence"])
        return best_title["text"]

    return "제목 없음"


def _detect_document_type(text_blocks: List[Dict]) -> str:
    """문서 유형 자동 감지"""
    all_text = " ".join([block.get("text", "") for block in text_blocks]).lower()

    # 패턴 기반 문서 유형 감지
    patterns = {
        "receipt": ["receipt", "영수증", "total", "payment", "card", "cash"],
        "invoice": ["invoice", "bill", "청구서", "계산서", "세금계산서"],
        "contract": ["contract", "agreement", "계약서", "약정서", "합의서"],
        "report": ["report", "보고서", "분석", "결과", "summary"],
        "letter": ["dear", "sincerely", "편지", "안녕하세요", "감사합니다"],
        "form": ["form", "application", "신청서", "양식", "등록"]
    }

    max_matches = 0
    detected_type = "general"

    for doc_type, keywords in patterns.items():
        matches = sum(1 for keyword in keywords if keyword in all_text)
        if matches > max_matches:
            max_matches = matches
            detected_type = doc_type

    return detected_type


def _extract_key_information(text_blocks: List[Dict]) -> Dict[str, str]:
    """핵심 정보 추출"""
    key_info = {}
    all_text = " ".join([block.get("text", "") for block in text_blocks])

    # 날짜 패턴
    date_patterns = [
        r'\d{4}-\d{2}-\d{2}',
        r'\d{4}/\d{2}/\d{2}',
        r'\d{2}/\d{2}/\d{4}'
    ]
    for pattern in date_patterns:
        match = re.search(pattern, all_text)
        if match:
            key_info["date"] = match.group()
            break

    # 금액 패턴
    money_patterns = [
        r'[\d,]+\s*원',
        r'[\d,]+\s*won',
        r'\$[\d,]+',
        r'total[:\s]*[\d,]+'
    ]
    for pattern in money_patterns:
        match = re.search(pattern, all_text, re.IGNORECASE)
        if match:
            key_info["amount"] = match.group()
            break

    # 전화번호 패턴
    phone_pattern = r'\d{2,3}-\d{3,4}-\d{4}'
    phone_match = re.search(phone_pattern, all_text)
    if phone_match:
        key_info["phone"] = phone_match.group()

    # 이메일 패턴
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    email_match = re.search(email_pattern, all_text)
    if email_match:
        key_info["email"] = email_match.group()

    return key_info
#!/usr/bin/env python3
"""
Pages navigation API endpoints
"""

from fastapi import APIRouter, HTTPException
from pathlib import Path
from typing import Dict, Any, List
import json

from services.file.storage import RequestStorage
from services.file.request_manager import validate_request_id

router = APIRouter()

# 전역 저장소 인스턴스
request_storage = None


def set_dependencies(output_dir: str):
    """의존성 설정"""
    global request_storage
    request_storage = RequestStorage(output_dir)


@router.get("/requests/{request_id}/pages", summary="요청의 모든 페이지 목록 조회")
async def get_all_pages(request_id: str) -> Dict[str, Any]:
    """
    요청의 모든 페이지 목록과 기본 정보 조회

    Args:
        request_id: 요청 ID

    Returns:
        페이지 목록과 메타데이터
    """
    if not validate_request_id(request_id):
        raise HTTPException(status_code=400, detail="유효하지 않은 요청 ID")

    try:
        pages_summary = request_storage.get_all_pages_summary(request_id)

        # 메타데이터 조회
        request_dir = request_storage.base_output_dir / request_id
        metadata_file = request_dir / "metadata.json"

        metadata = {}
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

        return {
            "request_id": request_id,
            "total_pages": len(pages_summary),
            "original_filename": metadata.get("original_filename", ""),
            "file_type": metadata.get("file_type", ""),
            "created_at": metadata.get("created_at", ""),
            "pages": pages_summary
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"페이지 목록 조회 중 오류: {str(e)}")


@router.get("/requests/{request_id}/navigation", summary="페이지 네비게이션 메타데이터")
async def get_navigation_info(request_id: str) -> Dict[str, Any]:
    """
    페이지 네비게이션을 위한 메타데이터 조회

    Args:
        request_id: 요청 ID

    Returns:
        네비게이션 메타데이터
    """
    if not validate_request_id(request_id):
        raise HTTPException(status_code=400, detail="유효하지 않은 요청 ID")

    try:
        pages_summary = request_storage.get_all_pages_summary(request_id)

        # 요청 메타데이터 조회
        request_dir = request_storage.base_output_dir / request_id
        metadata_file = request_dir / "metadata.json"
        summary_file = request_dir / "summary.json"

        metadata = {}
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

        summary = {}
        if summary_file.exists():
            with open(summary_file, 'r', encoding='utf-8') as f:
                summary = json.load(f)

        # 전체 통계 계산
        total_blocks = sum(page.get("total_blocks", 0) for page in pages_summary)
        avg_confidence = 0.0
        if pages_summary:
            confidences = [page.get("average_confidence", 0) for page in pages_summary]
            avg_confidence = sum(confidences) / len(confidences)

        return {
            "request_id": request_id,
            "total_pages": len(pages_summary),
            "total_blocks": total_blocks,
            "average_confidence": avg_confidence,
            "processing_status": metadata.get("processing_status", "unknown"),
            "file_type": metadata.get("file_type", ""),
            "file_size": metadata.get("file_size", 0),
            "created_at": metadata.get("created_at", ""),
            "completed_at": metadata.get("completed_at", ""),
            "current_capabilities": {
                "can_edit_blocks": True,
                "can_export": True,
                "can_regenerate_visualization": True,
                "has_original_images": any(page.get("has_original", False) for page in pages_summary),
                "has_visualizations": any(page.get("has_visualization", False) for page in pages_summary)
            }
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"네비게이션 정보 조회 중 오류: {str(e)}")


@router.get("/requests/{request_id}/pages/{page_number}/summary", summary="특정 페이지 요약 정보")
async def get_page_summary(request_id: str, page_number: int) -> Dict[str, Any]:
    """
    특정 페이지의 요약 정보 조회

    Args:
        request_id: 요청 ID
        page_number: 페이지 번호

    Returns:
        페이지 요약 정보
    """
    if not validate_request_id(request_id):
        raise HTTPException(status_code=400, detail="유효하지 않은 요청 ID")

    try:
        page_summary = request_storage.get_page_summary(request_id, page_number)

        if not page_summary:
            raise HTTPException(status_code=404, detail="페이지를 찾을 수 없습니다")

        # 네비게이션 정보 추가
        all_pages = request_storage.get_all_pages_summary(request_id)
        total_pages = len(all_pages)

        page_summary["navigation"] = {
            "current_page": page_number,
            "total_pages": total_pages,
            "prev_page": page_number - 1 if page_number > 1 else None,
            "next_page": page_number + 1 if page_number < total_pages else None,
            "is_first": page_number == 1,
            "is_last": page_number == total_pages
        }

        return page_summary

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"페이지 요약 조회 중 오류: {str(e)}")


@router.get("/requests/{request_id}/pages/{page_number}/navigation", summary="페이지별 네비게이션 정보")
async def get_page_navigation(request_id: str, page_number: int) -> Dict[str, Any]:
    """
    특정 페이지의 네비게이션 정보 조회

    Args:
        request_id: 요청 ID
        page_number: 페이지 번호

    Returns:
        페이지 네비게이션 정보
    """
    if not validate_request_id(request_id):
        raise HTTPException(status_code=400, detail="유효하지 않은 요청 ID")

    try:
        # 페이지 존재 확인
        page_summary = request_storage.get_page_summary(request_id, page_number)
        if not page_summary:
            raise HTTPException(status_code=404, detail="페이지를 찾을 수 없습니다")

        # 전체 페이지 정보
        all_pages = request_storage.get_all_pages_summary(request_id)
        total_pages = len(all_pages)

        # 이전/다음 페이지 정보
        prev_page_info = None
        next_page_info = None

        if page_number > 1:
            prev_page_info = {
                "page_number": page_number - 1,
                "total_blocks": all_pages[page_number - 2].get("total_blocks", 0),
                "thumbnail_url": all_pages[page_number - 2].get("thumbnail_url")
            }

        if page_number < total_pages:
            next_page_info = {
                "page_number": page_number + 1,
                "total_blocks": all_pages[page_number].get("total_blocks", 0),
                "thumbnail_url": all_pages[page_number].get("thumbnail_url")
            }

        return {
            "request_id": request_id,
            "current_page": page_number,
            "total_pages": total_pages,
            "is_first": page_number == 1,
            "is_last": page_number == total_pages,
            "prev_page": prev_page_info,
            "next_page": next_page_info,
            "current_page_info": {
                "total_blocks": page_summary.get("total_blocks", 0),
                "average_confidence": page_summary.get("average_confidence", 0.0),
                "has_original": page_summary.get("has_original", False),
                "has_visualization": page_summary.get("has_visualization", False)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"페이지 네비게이션 조회 중 오류: {str(e)}")


__all__ = ['router', 'set_dependencies']
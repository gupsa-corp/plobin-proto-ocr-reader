"""
Page content endpoints - page-level data and content summaries
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

from .dependencies import get_request_storage
from services.file.request_manager import validate_request_id

router = APIRouter()


@router.get("/requests/{request_id}/pages/{page_number}", summary="UUID 요청의 페이지별 OCR 결과 조회")
async def get_page_result(
    request_id: str,
    page_number: int,
    request_storage = Depends(get_request_storage)
) -> Dict[str, Any]:
    """
    특정 UUID 요청의 페이지별 OCR 결과 조회

    - 페이지별 블록 데이터 포함
    - 네비게이션 정보 자동 생성
    - 원본/시각화 이미지 링크 제공
    """
    if not validate_request_id(request_id):
        raise HTTPException(status_code=400, detail="유효하지 않은 요청 ID")

    try:
        page_data = request_storage.get_page_result(request_id, page_number)

        # 네비게이션 정보 추가
        all_pages = request_storage.get_all_pages_summary(request_id)
        total_pages = len(all_pages)

        page_data["navigation"] = {
            "current_page": page_number,
            "total_pages": total_pages,
            "prev_page": page_number - 1 if page_number > 1 else None,
            "next_page": page_number + 1 if page_number < total_pages else None,
            "is_first": page_number == 1,
            "is_last": page_number == total_pages,
            "has_thumbnail": f"/requests/{request_id}/pages/{page_number}/visualization"
        }

        return page_data

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="페이지를 찾을 수 없습니다")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"페이지 결과 조회 중 오류: {str(e)}")


@router.get("/requests/{request_id}/pages/{page_number}/content-summary", summary="페이지 콘텐츠 요약 조회")
async def get_page_content_summary(
    request_id: str,
    page_number: int,
    request_storage = Depends(get_request_storage)
) -> Dict[str, Any]:
    """페이지의 콘텐츠 요약 정보를 조회합니다"""
    if not validate_request_id(request_id):
        raise HTTPException(status_code=400, detail="유효하지 않은 요청 ID")

    try:
        page_data = request_storage.get_page_result(request_id, page_number)
        content_summary = page_data.get('content_summary', {})

        return {
            "request_id": request_id,
            "page_number": page_number,
            "content_summary": content_summary
        }

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="페이지를 찾을 수 없습니다")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"콘텐츠 요약 조회 중 오류: {str(e)}")
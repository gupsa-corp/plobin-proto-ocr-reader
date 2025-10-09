"""
Request queries endpoints - listing and retrieving request information
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, Any, Optional

from .dependencies import get_request_storage
from services.file.request_manager import validate_request_id, extract_timestamp_from_uuid
from services.file.directories import list_request_directories, list_page_directories

router = APIRouter()


@router.get("/requests", summary="UUID v7 요청 목록 조회 (페이지네이션 지원)")
async def list_requests(
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수 (1-100)"),
    search: Optional[str] = Query(None, description="파일명 검색어"),
    file_type: Optional[str] = Query(None, description="파일 타입 필터 (pdf, jpg, png 등)"),
    request_storage = Depends(get_request_storage)
) -> Dict[str, Any]:
    """
    UUID v7 요청 목록을 페이지네이션과 검색 기능과 함께 조회

    - UUID v7의 자연 정렬 특성을 활용한 시간순 정렬
    - 페이지네이션 지원 (page, limit 파라미터)
    - 파일명 검색 기능 (search 파라미터)
    - 파일 타입 필터링 (file_type 파라미터)
    - 최신 요청부터 내림차순 정렬
    """
    try:
        request_ids = list_request_directories(str(request_storage.base_output_dir))

        # UUID v7의 자연 정렬 특성 활용 (시간순 정렬)
        request_ids.sort(reverse=True)  # 최신 순으로 정렬

        requests_info = []
        for request_id in request_ids:
            try:
                metadata = request_storage.get_request_metadata(request_id)
                # UUID v7에서 타임스탬프 추출 (primary source)
                extracted_timestamp = extract_timestamp_from_uuid(request_id)
                # 메타데이터의 created_at을 fallback으로 사용
                created_at = extracted_timestamp.isoformat() if extracted_timestamp else metadata.get('created_at')

                # 파일명과 타입 정보 가져오기
                original_filename = metadata.get('original_filename', '')
                file_type_meta = metadata.get('file_type', '')

                # 검색 필터링
                if search and search.lower() not in original_filename.lower():
                    continue

                # 파일 타입 필터링
                if file_type and file_type.lower() != file_type_meta.lower():
                    continue

                requests_info.append({
                    "request_id": request_id,
                    "original_filename": original_filename,
                    "file_type": file_type_meta,
                    "total_pages": metadata.get('total_pages', 1),
                    "status": metadata.get('processing_status'),
                    "created_at": created_at,
                })
            except Exception:
                continue

        # 전체 개수 (필터링 후)
        total_requests = len(requests_info)

        # 페이지네이션 적용
        start = (page - 1) * limit
        end = start + limit
        paginated_requests = requests_info[start:end]

        return {
            "requests": paginated_requests,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_requests,
                "total_pages": (total_requests + limit - 1) // limit,
                "has_next": end < total_requests,
                "has_prev": page > 1
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"요청 목록 조회 중 오류: {str(e)}")


@router.get("/requests/{request_id}", summary="UUID v7 요청 상세 정보 조회")
async def get_request_info(
    request_id: str,
    request_storage = Depends(get_request_storage)
) -> Dict[str, Any]:
    """
    특정 UUID v7 요청의 상세 정보 조회

    - UUID v7에서 타임스탬프 자동 추출
    - 모든 페이지 요약 정보 포함
    - 처리 상태 및 메타데이터 제공
    """
    if not validate_request_id(request_id):
        raise HTTPException(status_code=400, detail="유효하지 않은 요청 ID")

    try:
        metadata = request_storage.get_request_metadata(request_id)

        # 페이지 정보 수집
        page_numbers = list_page_directories(str(request_storage.base_output_dir), request_id)
        pages_info = []

        for page_num in page_numbers:
            try:
                page_data = request_storage.get_page_result(request_id, page_num)
                pages_info.append({
                    "page_number": page_num,
                    "total_blocks": page_data.get('total_blocks', 0),
                    "average_confidence": page_data.get('average_confidence', 0),
                    "processing_time": page_data.get('processing_time', 0)
                })
            except Exception:
                continue

        # UUID v7에서 타임스탬프 추출하여 통합 응답 구조 생성
        extracted_timestamp = extract_timestamp_from_uuid(request_id)
        created_at = extracted_timestamp.isoformat() if extracted_timestamp else metadata.get('created_at')

        return {
            "request_id": request_id,
            "original_filename": metadata.get('original_filename'),
            "file_type": metadata.get('file_type'),
            "file_size": metadata.get('file_size'),
            "status": metadata.get('processing_status'),
            "created_at": created_at,
            "completed_at": metadata.get('completed_at'),
            "total_pages": len(pages_info),
            "total_processing_time": metadata.get('total_processing_time'),
            "pages": pages_info
        }

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="요청을 찾을 수 없습니다")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"요청 정보 조회 중 오류: {str(e)}")
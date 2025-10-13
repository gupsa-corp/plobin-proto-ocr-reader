"""
Search endpoints - full-text search across blocks
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, Any, Optional

from .dependencies import get_request_storage
from services.file.request_manager import validate_request_id
from services.file.directories import list_request_directories, list_page_directories

router = APIRouter()


@router.get("/search/blocks", summary="전체 블록 텍스트 검색")
async def search_blocks(
    q: str = Query(..., min_length=2, description="검색어 (최소 2자)"),
    request_id: Optional[str] = Query(None, description="특정 요청 내에서만 검색"),
    limit: int = Query(50, ge=1, le=200, description="최대 결과 수"),
    request_storage = Depends(get_request_storage)
) -> Dict[str, Any]:
    """
    모든 블록의 텍스트에서 검색합니다

    - 전체 요청에서 검색하거나 특정 요청 내에서만 검색 가능
    - 대소문자 구분 없이 검색
    - 검색어가 포함된 블록의 상세 정보 반환
    """
    try:
        results = []
        search_term = q.lower()

        # 검색 대상 요청 목록 결정
        if request_id:
            if not validate_request_id(request_id):
                raise HTTPException(status_code=400, detail="유효하지 않은 요청 ID")
            request_ids = [request_id]
        else:
            request_ids = list_request_directories(str(request_storage.base_output_dir))

        # 각 요청의 모든 페이지에서 검색
        for rid in request_ids:
            try:
                page_numbers = list_page_directories(str(request_storage.base_output_dir), rid)

                for page_num in page_numbers:
                    try:
                        # 페이지 결과 로드
                        page_data = request_storage.get_page_result(rid, page_num)
                        blocks = page_data.get('blocks', [])

                        for i, block in enumerate(blocks):
                            block_text = block.get('text', '').lower()

                            if search_term in block_text:
                                # 검색어 하이라이트
                                original_text = block.get('text', '')
                                highlighted_text = original_text.replace(
                                    q, f"**{q}**"
                                ) if q in original_text else original_text

                                results.append({
                                    "request_id": rid,
                                    "page_number": page_num,
                                    "block_index": i + 1,
                                    "text": original_text,
                                    "highlighted_text": highlighted_text,
                                    "confidence": block.get('confidence', 0),
                                    "block_type": block.get('block_type', 'text'),
                                    "bbox": block.get('bbox', {}),
                                    "match_position": block_text.find(search_term)
                                })

                                # 제한 수에 도달하면 중단
                                if len(results) >= limit:
                                    break

                    except Exception:
                        continue

                    if len(results) >= limit:
                        break

            except Exception:
                continue

            if len(results) >= limit:
                break

        # 신뢰도 순으로 정렬
        results.sort(key=lambda x: x['confidence'], reverse=True)

        return {
            "query": q,
            "total_results": len(results),
            "limit": limit,
            "results": results[:limit]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검색 중 오류 발생: {str(e)}")
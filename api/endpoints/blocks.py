#!/usr/bin/env python3
"""
Block management API endpoints
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from services.file.storage import RequestStorage
from services.block.editor import BlockEditor
from services.file.request_manager import validate_request_id

router = APIRouter()

# 전역 인스턴스
request_storage = None
block_editor = None


def set_dependencies(output_dir: str):
    """의존성 설정"""
    global request_storage, block_editor
    request_storage = RequestStorage(output_dir)
    block_editor = BlockEditor(request_storage)


# Pydantic 모델 정의
class BlockUpdate(BaseModel):
    text: Optional[str] = None
    confidence: Optional[float] = None
    bbox: Optional[List[List[float]]] = None
    block_type: Optional[str] = None


class BlockCreate(BaseModel):
    text: str
    bbox: List[List[float]]
    confidence: Optional[float] = 1.0
    block_type: Optional[str] = "other"


@router.get("/requests/{request_id}/pages/{page_number}/blocks", summary="UUID 요청 페이지의 블록 필터링 조회")
async def get_blocks_filtered(
    request_id: str,
    page_number: int,
    block_type: Optional[str] = None,
    confidence_min: Optional[float] = None,
    start: int = 0,
    limit: int = 100
) -> Dict[str, Any]:
    """
    UUID 요청의 특정 페이지에서 블록 목록을 필터링하여 조회

    Args:
        request_id: UUID v7 요청 ID
        page_number: 페이지 번호 (1부터 시작)
        block_type: 블록 타입 필터 (title, paragraph, table, list, other)
        confidence_min: 최소 신뢰도 (0.0-1.0)
        start: 시작 인덱스 (페이지네이션용)
        limit: 최대 반환 개수

    Returns:
        필터링된 블록 목록, 통계 정보, 페이지네이션 메타데이터
    """
    if not validate_request_id(request_id):
        raise HTTPException(status_code=400, detail="유효하지 않은 요청 ID")

    if confidence_min is not None and (confidence_min < 0 or confidence_min > 1):
        raise HTTPException(status_code=400, detail="신뢰도는 0.0과 1.0 사이여야 합니다")

    valid_types = ['title', 'paragraph', 'table', 'list', 'other']
    if block_type and block_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"유효하지 않은 블록 타입. 가능한 값: {valid_types}")

    try:
        result = block_editor.get_blocks_filtered(
            request_id, page_number, block_type, confidence_min, start, limit
        )

        return {
            "request_id": request_id,
            "page_number": page_number,
            "filters": {
                "block_type": block_type,
                "confidence_min": confidence_min
            },
            "pagination": {
                "start": start,
                "limit": limit,
                "has_more": result.get("has_more", False)
            },
            "statistics": {
                "total_blocks": result.get("total", 0),
                "filtered_blocks": result.get("filtered", 0),
                "returned_blocks": len(result.get("blocks", []))
            },
            "blocks": result.get("blocks", [])
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"블록 목록 조회 중 오류: {str(e)}")


@router.get("/requests/{request_id}/pages/{page_number}/blocks/{block_id}", summary="UUID 요청의 개별 블록 상세 조회")
async def get_block_details(request_id: str, page_number: int, block_id: int) -> Dict[str, Any]:
    """
    UUID 요청의 특정 페이지에서 개별 블록 상세 정보 조회

    Args:
        request_id: UUID v7 요청 ID
        page_number: 페이지 번호 (1부터 시작)
        block_id: 블록 ID (1부터 시작)

    Returns:
        블록 상세 정보 (텍스트, 신뢰도, 바운딩 박스, 타입)
    """
    if not validate_request_id(request_id):
        raise HTTPException(status_code=400, detail="유효하지 않은 요청 ID")

    try:
        block = block_editor.get_block(request_id, page_number, block_id)

        if not block:
            raise HTTPException(status_code=404, detail="블록을 찾을 수 없습니다")

        return {
            "request_id": request_id,
            "page_number": page_number,
            "block": block
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"블록 조회 중 오류: {str(e)}")


@router.put("/requests/{request_id}/pages/{page_number}/blocks/{block_id}", summary="UUID 요청의 블록 정보 수정")
async def update_block(
    request_id: str,
    page_number: int,
    block_id: int,
    block_update: BlockUpdate
) -> Dict[str, Any]:
    """
    UUID 요청의 특정 블록 정보 수정 (텍스트, 신뢰도, 바운딩 박스, 타입)

    Args:
        request_id: UUID v7 요청 ID
        page_number: 페이지 번호
        block_id: 블록 ID (1부터 시작)
        block_update: 수정할 블록 정보

    Returns:
        수정 결과 및 업데이트된 블록 정보
    """
    if not validate_request_id(request_id):
        raise HTTPException(status_code=400, detail="유효하지 않은 요청 ID")

    try:
        # 수정할 데이터 준비
        updates = {}
        if block_update.text is not None:
            updates['text'] = block_update.text
        if block_update.confidence is not None:
            if block_update.confidence < 0 or block_update.confidence > 1:
                raise HTTPException(status_code=400, detail="신뢰도는 0.0과 1.0 사이여야 합니다")
            updates['confidence'] = block_update.confidence
        if block_update.bbox is not None:
            updates['bbox'] = block_update.bbox
        if block_update.block_type is not None:
            valid_types = ['title', 'paragraph', 'table', 'list', 'other']
            if block_update.block_type not in valid_types:
                raise HTTPException(status_code=400, detail=f"유효하지 않은 블록 타입. 가능한 값: {valid_types}")
            updates['block_type'] = block_update.block_type

        if not updates:
            raise HTTPException(status_code=400, detail="수정할 데이터가 없습니다")

        # 업데이트 수행
        result = block_editor.update_block(request_id, page_number, block_id, updates)

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "업데이트 실패"))

        return {
            "request_id": request_id,
            "page_number": page_number,
            "block_id": block_id,
            "success": True,
            "updated_fields": list(updates.keys()),
            "updated_block": result.get("updated_block"),
            "regenerated_visualization": result.get("regenerated_visualization", False)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"블록 수정 중 오류: {str(e)}")


@router.delete("/requests/{request_id}/pages/{page_number}/blocks/{block_id}", summary="블록 삭제")
async def delete_block(request_id: str, page_number: int, block_id: int) -> Dict[str, Any]:
    """
    블록 삭제

    Args:
        request_id: 요청 ID
        page_number: 페이지 번호
        block_id: 블록 ID (1부터 시작)

    Returns:
        삭제 결과
    """
    if not validate_request_id(request_id):
        raise HTTPException(status_code=400, detail="유효하지 않은 요청 ID")

    try:
        result = block_editor.delete_block(request_id, page_number, block_id)

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "삭제 실패"))

        return {
            "request_id": request_id,
            "page_number": page_number,
            "deleted_block_id": block_id,
            "success": True,
            "regenerated_visualization": result.get("regenerated_visualization", False)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"블록 삭제 중 오류: {str(e)}")


@router.post("/requests/{request_id}/pages/{page_number}/blocks", summary="새 블록 추가")
async def create_block(
    request_id: str,
    page_number: int,
    block_create: BlockCreate
) -> Dict[str, Any]:
    """
    새 블록 추가

    Args:
        request_id: 요청 ID
        page_number: 페이지 번호
        block_create: 새 블록 정보

    Returns:
        추가 결과 및 새 블록 정보
    """
    if not validate_request_id(request_id):
        raise HTTPException(status_code=400, detail="유효하지 않은 요청 ID")

    try:
        # 유효성 검사
        if block_create.confidence < 0 or block_create.confidence > 1:
            raise HTTPException(status_code=400, detail="신뢰도는 0.0과 1.0 사이여야 합니다")

        valid_types = ['title', 'paragraph', 'table', 'list', 'other']
        if block_create.block_type not in valid_types:
            raise HTTPException(status_code=400, detail=f"유효하지 않은 블록 타입. 가능한 값: {valid_types}")

        # 블록 데이터 준비
        block_data = {
            'text': block_create.text,
            'bbox': block_create.bbox,
            'confidence': block_create.confidence,
            'block_type': block_create.block_type
        }

        # 블록 추가
        result = block_editor.add_block(request_id, page_number, block_data)

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "추가 실패"))

        return {
            "request_id": request_id,
            "page_number": page_number,
            "success": True,
            "new_block_id": result.get("new_block_id"),
            "new_block": result.get("new_block"),
            "regenerated_visualization": result.get("regenerated_visualization", False)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"블록 추가 중 오류: {str(e)}")


@router.get("/requests/{request_id}/pages/{page_number}/blocks/stats", summary="페이지 블록 통계")
async def get_blocks_statistics(request_id: str, page_number: int) -> Dict[str, Any]:
    """
    페이지의 블록 통계 정보 조회

    Args:
        request_id: 요청 ID
        page_number: 페이지 번호

    Returns:
        블록 통계 정보
    """
    if not validate_request_id(request_id):
        raise HTTPException(status_code=400, detail="유효하지 않은 요청 ID")

    try:
        # 모든 블록 조회
        all_blocks = block_editor.get_blocks_filtered(request_id, page_number)
        blocks = all_blocks.get("blocks", [])

        if not blocks:
            return {
                "request_id": request_id,
                "page_number": page_number,
                "total_blocks": 0,
                "statistics": {}
            }

        # 통계 계산
        total_blocks = len(blocks)

        # 타입별 통계
        type_counts = {}
        confidence_sum = 0
        confidence_distribution = {"high": 0, "medium": 0, "low": 0}

        for block in blocks:
            # 타입별 카운트
            block_type = block.get('block_type', 'other')
            type_counts[block_type] = type_counts.get(block_type, 0) + 1

            # 신뢰도 통계
            confidence = block.get('confidence', 0)
            confidence_sum += confidence

            if confidence >= 0.9:
                confidence_distribution["high"] += 1
            elif confidence >= 0.7:
                confidence_distribution["medium"] += 1
            else:
                confidence_distribution["low"] += 1

        average_confidence = confidence_sum / total_blocks

        return {
            "request_id": request_id,
            "page_number": page_number,
            "total_blocks": total_blocks,
            "statistics": {
                "average_confidence": round(average_confidence, 4),
                "confidence_distribution": confidence_distribution,
                "type_distribution": type_counts,
                "confidence_quality": {
                    "high_quality": confidence_distribution["high"],
                    "medium_quality": confidence_distribution["medium"],
                    "low_quality": confidence_distribution["low"],
                    "high_quality_percentage": round((confidence_distribution["high"] / total_blocks) * 100, 2)
                }
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"블록 통계 조회 중 오류: {str(e)}")


@router.post("/requests/{request_id}/pages/{page_number}/regenerate-visualization", summary="시각화 재생성")
async def regenerate_page_visualization(request_id: str, page_number: int) -> Dict[str, Any]:
    """
    페이지 시각화 재생성

    Args:
        request_id: 요청 ID
        page_number: 페이지 번호

    Returns:
        재생성 결과
    """
    if not validate_request_id(request_id):
        raise HTTPException(status_code=400, detail="유효하지 않은 요청 ID")

    try:
        success = block_editor.regenerate_visualization(request_id, page_number)

        if not success:
            raise HTTPException(status_code=400, detail="시각화 재생성 실패")

        return {
            "request_id": request_id,
            "page_number": page_number,
            "success": True,
            "visualization_url": f"/requests/{request_id}/pages/{page_number}/visualization"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시각화 재생성 중 오류: {str(e)}")


__all__ = ['router', 'set_dependencies', 'BlockUpdate', 'BlockCreate']
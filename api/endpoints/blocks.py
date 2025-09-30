from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from api.models.schemas import BlockDetail, BlockStats
from api.utils.file_storage import validate_filename, load_json_file, get_file_info
from api.utils.block_processing import filter_blocks, calculate_block_stats, find_blocks_by_position

router = APIRouter()

@router.get("/output/{filename}/blocks/stats", response_model=BlockStats)
async def get_block_stats(filename: str):
    """블록 통계"""
    if not validate_filename(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")

    try:
        content = load_json_file(filename)
        blocks = content.get('blocks', [])
        return calculate_block_stats(blocks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get block stats: {str(e)}")

@router.get("/output/{filename}/blocks/by_position")
async def get_blocks_by_position(
    filename: str,
    x: int = Query(..., description="X 좌표"),
    y: int = Query(..., description="Y 좌표"),
    tolerance: int = Query(10, description="허용 오차 (픽셀)")
):
    """좌표 기반 블록 검색"""
    if not validate_filename(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")

    try:
        content = load_json_file(filename)
        blocks = content.get('blocks', [])
        found_blocks = find_blocks_by_position(blocks, x, y, tolerance)

        return {
            "search_position": {"x": x, "y": y, "tolerance": tolerance},
            "found_blocks": len(found_blocks),
            "blocks": found_blocks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search blocks: {str(e)}")

@router.get("/output/{filename}/blocks/{block_id}", response_model=BlockDetail)
async def get_block_detail(filename: str, block_id: int):
    """특정 블록 조회"""
    if not validate_filename(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")

    try:
        content = load_json_file(filename)
        blocks = content.get('blocks', [])

        if block_id < 0 or block_id >= len(blocks):
            raise HTTPException(status_code=404, detail="Block not found")

        block = blocks[block_id]
        file_info = get_file_info(filename)

        return BlockDetail(
            block_id=block_id,
            text=block.get('text', ''),
            confidence=block.get('confidence', 0.0),
            bbox=block.get('bbox_points', block.get('bbox', [])),
            block_type=block.get('block_type', block.get('type', 'unknown')),
            file_info=file_info
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get block: {str(e)}")

@router.get("/output/{filename}/blocks")
async def get_filtered_blocks(
    filename: str,
    confidence_min: Optional[float] = Query(None, description="최소 신뢰도"),
    confidence_max: Optional[float] = Query(None, description="최대 신뢰도"),
    text_contains: Optional[str] = Query(None, description="텍스트 포함"),
    block_type: Optional[str] = Query(None, description="블록 타입"),
    start: Optional[int] = Query(0, description="시작 인덱스"),
    end: Optional[int] = Query(None, description="종료 인덱스")
):
    """블록 필터링 및 범위 조회"""
    if not validate_filename(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")

    try:
        content = load_json_file(filename)
        blocks = content.get('blocks', [])

        # 필터링
        filtered_blocks = filter_blocks(
            blocks, confidence_min, confidence_max, text_contains, block_type
        )

        # 범위 선택
        if end is None:
            end = len(filtered_blocks)
        range_blocks = filtered_blocks[start:end]

        return {
            "total_blocks": len(blocks),
            "filtered_blocks": len(filtered_blocks),
            "returned_blocks": len(range_blocks),
            "range": {"start": start, "end": min(end, len(filtered_blocks))},
            "filters": {
                "confidence_min": confidence_min,
                "confidence_max": confidence_max,
                "text_contains": text_contains,
                "block_type": block_type
            },
            "blocks": range_blocks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get blocks: {str(e)}")
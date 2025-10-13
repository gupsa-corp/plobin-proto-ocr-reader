"""
Block access endpoints - blocks, images, and file downloads
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from typing import Dict, Any

from .dependencies import get_request_storage
from services.file.request_manager import validate_request_id

router = APIRouter()


@router.get("/requests/{request_id}/pages/{page_number}/blocks/{block_id}", summary="특정 블록 데이터 조회")
async def get_block_data(
    request_id: str,
    page_number: int,
    block_id: int,
    request_storage = Depends(get_request_storage)
) -> Dict[str, Any]:
    """특정 요청의 특정 페이지의 특정 블록 데이터 조회"""
    if not validate_request_id(request_id):
        raise HTTPException(status_code=400, detail="유효하지 않은 요청 ID")

    try:
        block_data = request_storage.get_block_data(request_id, page_number, block_id)
        return block_data

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="블록을 찾을 수 없습니다")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"블록 데이터 조회 중 오류: {str(e)}")


@router.get("/requests/{request_id}/pages/{page_number}/visualization", summary="페이지 시각화 이미지 다운로드")
async def download_page_visualization(
    request_id: str,
    page_number: int,
    request_storage = Depends(get_request_storage)
):
    """특정 페이지의 시각화 이미지 다운로드"""
    if not validate_request_id(request_id):
        raise HTTPException(status_code=400, detail="유효하지 않은 요청 ID")

    try:
        visualization_path = request_storage.base_output_dir / request_id / "pages" / f"{page_number:03d}" / "visualization.png"

        if not visualization_path.exists():
            raise HTTPException(status_code=404, detail="시각화 파일을 찾을 수 없습니다")

        return FileResponse(
            path=str(visualization_path),
            media_type="image/png",
            filename=f"{request_id}_page_{page_number}_visualization.png"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시각화 다운로드 중 오류: {str(e)}")


@router.get("/requests/{request_id}/pages/{page_number}/original", summary="페이지 원본 이미지 다운로드")
async def get_page_original_image(
    request_id: str,
    page_number: int,
    request_storage = Depends(get_request_storage)
):
    """페이지의 원본 이미지를 다운로드"""
    if not validate_request_id(request_id):
        raise HTTPException(status_code=400, detail="유효하지 않은 요청 ID")

    try:
        # 원본 이미지 파일 경로
        original_file = request_storage.base_output_dir / request_id / "pages" / f"{page_number:03d}" / "original.png"

        if not original_file.exists():
            raise HTTPException(status_code=404, detail="원본 이미지를 찾을 수 없습니다")

        return FileResponse(
            path=str(original_file),
            media_type="image/png",
            filename=f"page_{page_number:03d}_original.png"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"원본 이미지 다운로드 중 오류: {str(e)}")


@router.get("/requests/{request_id}/pages/{page_number}/blocks/{block_id}/image", summary="블록 이미지 다운로드")
async def get_block_image(
    request_id: str,
    page_number: int,
    block_id: int,
    request_storage = Depends(get_request_storage)
):
    """개별 블록의 크롭된 이미지를 다운로드"""
    if not validate_request_id(request_id):
        raise HTTPException(status_code=400, detail="유효하지 않은 요청 ID")

    try:
        # 블록 이미지 파일 경로
        block_image_file = request_storage.base_output_dir / request_id / "pages" / f"{page_number:03d}" / "blocks" / f"block_{block_id:03d}.png"

        if not block_image_file.exists():
            raise HTTPException(status_code=404, detail="블록 이미지를 찾을 수 없습니다")

        return FileResponse(
            path=str(block_image_file),
            media_type="image/png",
            filename=f"page_{page_number:03d}_block_{block_id:03d}.png"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"블록 이미지 다운로드 중 오류: {str(e)}")
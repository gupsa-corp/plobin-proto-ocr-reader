"""
Section access endpoints - section data and visualization retrieval
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
from typing import Dict, Any, List

from .dependencies import get_request_storage

router = APIRouter()


@router.get("/requests/{request_id}/pages/{page_number}/sections",
            summary="페이지의 모든 섹션 목록 조회")
async def get_page_sections(
    request_id: str,
    page_number: int,
    request_storage = Depends(get_request_storage)
) -> List[Dict[str, Any]]:
    """
    페이지의 모든 섹션 목록 조회

    Returns:
        섹션 데이터 리스트 (section_id, section_type, bbox, block_count 등)
    """
    from services.file.request_manager import validate_request_id

    try:
        # UUID 형식 검증
        if not validate_request_id(request_id):
            raise HTTPException(status_code=400, detail="유효하지 않은 요청 ID 형식")

        # 섹션 목록 조회
        sections = request_storage.get_sections_list(request_id, page_number)

        if not sections:
            # 페이지 존재 확인
            request_dir = Path(request_storage.base_output_dir) / request_id
            page_dir = request_dir / "pages" / f"{page_number:03d}"

            if not page_dir.exists():
                raise HTTPException(status_code=404, detail="페이지를 찾을 수 없습니다")

            # 페이지는 있지만 섹션이 없는 경우 (create_sections=False로 처리됨)
            return []

        return sections

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"섹션 목록 조회 중 오류: {str(e)}")


@router.get("/requests/{request_id}/pages/{page_number}/sections/{section_id}",
            summary="특정 섹션 데이터 조회")
async def get_section_data(
    request_id: str,
    page_number: int,
    section_id: int,
    request_storage = Depends(get_request_storage)
) -> Dict[str, Any]:
    """
    특정 섹션의 상세 데이터 조회

    Returns:
        섹션 메타데이터 (section_id, section_type, bbox, blocks, text_content 등)
    """
    from services.file.request_manager import validate_request_id

    try:
        # UUID 형식 검증
        if not validate_request_id(request_id):
            raise HTTPException(status_code=400, detail="유효하지 않은 요청 ID 형식")

        # 섹션 ID 검증
        if section_id < 1:
            raise HTTPException(status_code=400, detail="섹션 ID는 1 이상이어야 합니다")

        # 섹션 데이터 조회
        try:
            section_data = request_storage.get_section_data(request_id, page_number, section_id)
            return section_data
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="섹션을 찾을 수 없습니다")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"섹션 데이터 조회 중 오류: {str(e)}")


@router.get("/requests/{request_id}/pages/{page_number}/sections/{section_id}/image",
            summary="섹션 크롭 이미지 다운로드")
async def get_section_image(
    request_id: str,
    page_number: int,
    section_id: int,
    request_storage = Depends(get_request_storage)
) -> FileResponse:
    """
    특정 섹션의 크롭 이미지 다운로드

    Returns:
        섹션 크롭 이미지 (PNG 형식)
    """
    from services.file.request_manager import validate_request_id

    try:
        # UUID 형식 검증
        if not validate_request_id(request_id):
            raise HTTPException(status_code=400, detail="유효하지 않은 요청 ID 형식")

        # 섹션 ID 검증
        if section_id < 1:
            raise HTTPException(status_code=400, detail="섹션 ID는 1 이상이어야 합니다")

        # 섹션 이미지 파일 경로
        request_dir = Path(request_storage.base_output_dir) / request_id
        sections_dir = request_dir / "pages" / f"{page_number:03d}" / "sections"
        section_image = sections_dir / f"section_{section_id:03d}.png"

        if not section_image.exists():
            raise HTTPException(status_code=404, detail="섹션 이미지를 찾을 수 없습니다")

        # 파일 응답
        return FileResponse(
            path=str(section_image),
            media_type="image/png",
            filename=f"section_{section_id:03d}.png"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"섹션 이미지 다운로드 중 오류: {str(e)}")


@router.get("/requests/{request_id}/pages/{page_number}/sections-visualization",
            summary="페이지 전체 섹션 시각화 다운로드")
async def get_sections_visualization(
    request_id: str,
    page_number: int,
    request_storage = Depends(get_request_storage)
) -> FileResponse:
    """
    페이지의 전체 섹션 시각화 이미지 다운로드

    Returns:
        섹션 바운딩 박스가 그려진 시각화 이미지 (PNG 형식)
    """
    from services.file.request_manager import validate_request_id

    try:
        # UUID 형식 검증
        if not validate_request_id(request_id):
            raise HTTPException(status_code=400, detail="유효하지 않은 요청 ID 형식")

        # 섹션 시각화 파일 경로
        request_dir = Path(request_storage.base_output_dir) / request_id
        page_dir = request_dir / "pages" / f"{page_number:03d}"
        visualization_file = page_dir / "sections_visualization.png"

        if not visualization_file.exists():
            raise HTTPException(status_code=404, detail="섹션 시각화를 찾을 수 없습니다. create_sections 파라미터가 활성화되어 있는지 확인하세요.")

        # 파일 응답
        return FileResponse(
            path=str(visualization_file),
            media_type="image/png",
            filename=f"sections_visualization_page_{page_number}.png"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"섹션 시각화 다운로드 중 오류: {str(e)}")

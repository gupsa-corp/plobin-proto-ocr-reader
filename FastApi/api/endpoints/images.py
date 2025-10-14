#!/usr/bin/env python3
"""
Image processing API endpoints
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse, StreamingResponse
from PIL import Image, ImageOps
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import io
import os
import mimetypes
import tempfile
import shutil
from datetime import datetime

from services.file.storage import RequestStorage
from services.file.request_manager import validate_request_id

router = APIRouter()

# 전역 저장소 인스턴스
request_storage = None

def set_dependencies(output_dir: str):
    """의존성 설정"""
    global request_storage
    request_storage = RequestStorage(output_dir)


@router.get("/requests/{request_id}/pages/{page_number}/image-metadata", summary="이미지 메타데이터 조회")
async def get_image_metadata(request_id: str, page_number: int) -> Dict[str, Any]:
    """
    페이지 원본 이미지의 메타데이터 조회

    Args:
        request_id: UUID v7 요청 ID
        page_number: 페이지 번호 (1부터 시작)

    Returns:
        이미지 메타데이터 (크기, 포맷, 색상 모드 등)
    """
    if not validate_request_id(request_id):
        raise HTTPException(status_code=400, detail="유효하지 않은 요청 ID")

    try:
        # 원본 이미지 파일 경로
        original_file = Path(request_storage.base_output_dir) / request_id / "pages" / f"{page_number:03d}" / "original.png"

        if not original_file.exists():
            raise HTTPException(status_code=404, detail="원본 이미지를 찾을 수 없습니다")

        # PIL로 이미지 메타데이터 추출
        with Image.open(original_file) as img:
            metadata = {
                "request_id": request_id,
                "page_number": page_number,
                "filename": original_file.name,
                "format": img.format,
                "mode": img.mode,
                "size": {
                    "width": img.width,
                    "height": img.height
                },
                "has_transparency": img.mode in ('RGBA', 'LA') or 'transparency' in img.info,
                "dpi": img.info.get('dpi', (72, 72)),
                "file_size": original_file.stat().st_size,
                "file_size_mb": round(original_file.stat().st_size / (1024 * 1024), 2),
                "created_at": datetime.fromtimestamp(original_file.stat().st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(original_file.stat().st_mtime).isoformat()
            }

            # EXIF 데이터가 있으면 추가
            if hasattr(img, '_getexif') and img._getexif():
                exif_data = img._getexif()
                metadata["exif"] = {str(k): str(v) for k, v in exif_data.items() if k and v}

            return metadata

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"메타데이터 조회 중 오류: {str(e)}")


@router.get("/requests/{request_id}/pages/{page_number}/thumbnail", summary="이미지 썸네일 생성")
async def get_image_thumbnail(
    request_id: str,
    page_number: int,
    size: Optional[int] = Query(200, description="썸네일 크기 (정사각형, 기본 200px)"),
    quality: Optional[int] = Query(85, description="JPEG 품질 (1-100, 기본 85)")
):
    """
    페이지 원본 이미지의 썸네일 생성 및 반환

    Args:
        request_id: UUID v7 요청 ID
        page_number: 페이지 번호 (1부터 시작)
        size: 썸네일 크기 (최대 변 길이)
        quality: JPEG 품질

    Returns:
        썸네일 이미지 (JPEG 형식)
    """
    if not validate_request_id(request_id):
        raise HTTPException(status_code=400, detail="유효하지 않은 요청 ID")

    if size < 50 or size > 1000:
        raise HTTPException(status_code=400, detail="썸네일 크기는 50-1000px 사이여야 합니다")

    if quality < 1 or quality > 100:
        raise HTTPException(status_code=400, detail="품질은 1-100 사이여야 합니다")

    try:
        # 원본 이미지 파일 경로
        original_file = Path(request_storage.base_output_dir) / request_id / "pages" / f"{page_number:03d}" / "original.png"

        if not original_file.exists():
            raise HTTPException(status_code=404, detail="원본 이미지를 찾을 수 없습니다")

        # 썸네일 생성
        with Image.open(original_file) as img:
            # RGB 모드로 변환 (JPEG 저장을 위해)
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # 썸네일 생성 (비율 유지하면서 크기 조정)
            img.thumbnail((size, size), Image.Resampling.LANCZOS)

            # 메모리에 JPEG로 저장
            img_io = io.BytesIO()
            img.save(img_io, format='JPEG', quality=quality, optimize=True)
            img_io.seek(0)

            return StreamingResponse(
                io.BytesIO(img_io.read()),
                media_type="image/jpeg",
                headers={
                    "Content-Disposition": f"inline; filename=page_{page_number:03d}_thumbnail.jpg",
                    "Cache-Control": "public, max-age=3600"
                }
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"썸네일 생성 중 오류: {str(e)}")


@router.post("/convert-image", summary="이미지 형식 변환")
async def convert_image(
    file: UploadFile = File(...),
    target_format: str = Query(..., description="변환할 형식 (jpeg, png, webp, bmp, tiff)"),
    quality: Optional[int] = Query(90, description="JPEG/WebP 품질 (1-100)"),
    resize_width: Optional[int] = Query(None, description="리사이즈 너비 (선택사항)"),
    resize_height: Optional[int] = Query(None, description="리사이즈 높이 (선택사항)")
):
    """
    업로드된 이미지를 다른 형식으로 변환

    Args:
        file: 변환할 이미지 파일
        target_format: 변환할 형식
        quality: 압축 품질
        resize_width: 리사이즈 너비 (선택)
        resize_height: 리사이즈 높이 (선택)

    Returns:
        변환된 이미지 파일
    """
    # 지원되는 형식 확인
    supported_formats = ['jpeg', 'png', 'webp', 'bmp', 'tiff']
    if target_format.lower() not in supported_formats:
        raise HTTPException(status_code=400, detail=f"지원되지 않는 형식: {target_format}")

    # 파일 타입 확인
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="이미지 파일만 업로드 가능합니다")

    try:
        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_path = tmp_file.name

        try:
            # 이미지 열기 및 변환
            with Image.open(tmp_path) as img:
                # 리사이즈 처리
                if resize_width or resize_height:
                    if resize_width and resize_height:
                        img = img.resize((resize_width, resize_height), Image.Resampling.LANCZOS)
                    elif resize_width:
                        # 비율 유지하면서 너비 기준 리사이즈
                        ratio = resize_width / img.width
                        new_height = int(img.height * ratio)
                        img = img.resize((resize_width, new_height), Image.Resampling.LANCZOS)
                    elif resize_height:
                        # 비율 유지하면서 높이 기준 리사이즈
                        ratio = resize_height / img.height
                        new_width = int(img.width * ratio)
                        img = img.resize((new_width, resize_height), Image.Resampling.LANCZOS)

                # 형식별 처리
                img_io = io.BytesIO()

                if target_format.lower() == 'jpeg':
                    # JPEG: RGB 모드 필요
                    if img.mode in ('RGBA', 'LA'):
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                        img = background
                    elif img.mode != 'RGB':
                        img = img.convert('RGB')
                    img.save(img_io, format='JPEG', quality=quality, optimize=True)
                    media_type = "image/jpeg"
                    ext = "jpg"

                elif target_format.lower() == 'png':
                    img.save(img_io, format='PNG', optimize=True)
                    media_type = "image/png"
                    ext = "png"

                elif target_format.lower() == 'webp':
                    img.save(img_io, format='WebP', quality=quality, optimize=True)
                    media_type = "image/webp"
                    ext = "webp"

                elif target_format.lower() == 'bmp':
                    img.save(img_io, format='BMP')
                    media_type = "image/bmp"
                    ext = "bmp"

                elif target_format.lower() == 'tiff':
                    img.save(img_io, format='TIFF', quality=quality)
                    media_type = "image/tiff"
                    ext = "tiff"

                img_io.seek(0)

                # 원본 파일명에서 확장자 변경
                original_name = Path(file.filename).stem
                new_filename = f"{original_name}_converted.{ext}"

                return StreamingResponse(
                    io.BytesIO(img_io.read()),
                    media_type=media_type,
                    headers={
                        "Content-Disposition": f"attachment; filename={new_filename}",
                        "Content-Length": str(len(img_io.getvalue()))
                    }
                )

        finally:
            # 임시 파일 정리
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이미지 변환 중 오류: {str(e)}")


@router.get("/requests/{request_id}/pages/{page_number}/proxy", summary="이미지 프록시")
async def proxy_image(
    request_id: str,
    page_number: int,
    image_type: str = Query(..., description="이미지 타입 (original, visualization, block/{block_id})"),
    format: Optional[str] = Query(None, description="변환할 형식 (jpeg, png, webp)"),
    quality: Optional[int] = Query(85, description="압축 품질 (1-100)"),
    max_width: Optional[int] = Query(None, description="최대 너비 제한"),
    max_height: Optional[int] = Query(None, description="최대 높이 제한")
):
    """
    요청의 이미지를 프록시하여 제공 (선택적 변환/리사이즈 포함)

    Args:
        request_id: UUID v7 요청 ID
        page_number: 페이지 번호
        image_type: 이미지 타입 (original, visualization, block/{block_id})
        format: 변환할 형식 (선택)
        quality: 압축 품질
        max_width: 최대 너비
        max_height: 최대 높이

    Returns:
        이미지 파일 (원본 또는 변환된 형태)
    """
    if not validate_request_id(request_id):
        raise HTTPException(status_code=400, detail="유효하지 않은 요청 ID")

    try:
        # 이미지 파일 경로 결정
        base_path = Path(request_storage.base_output_dir) / request_id / "pages" / f"{page_number:03d}"

        if image_type == "original":
            image_path = base_path / "original.png"
        elif image_type == "visualization":
            image_path = base_path / "visualization.png"
        elif image_type.startswith("block/"):
            block_id = image_type.split("/")[1]
            try:
                block_num = int(block_id)
                image_path = base_path / "blocks" / f"block_{block_num:03d}.png"
            except ValueError:
                raise HTTPException(status_code=400, detail="유효하지 않은 블록 ID")
        else:
            raise HTTPException(status_code=400, detail="유효하지 않은 이미지 타입")

        if not image_path.exists():
            raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다")

        # 변환이나 리사이즈가 필요 없으면 원본 파일 반환
        if not format and not max_width and not max_height:
            return FileResponse(
                path=str(image_path),
                media_type="image/png",
                filename=image_path.name,
                headers={"Cache-Control": "public, max-age=3600"}
            )

        # 이미지 처리 필요
        with Image.open(image_path) as img:
            # 리사이즈 처리
            if max_width or max_height:
                current_width, current_height = img.size

                if max_width and current_width > max_width:
                    ratio = max_width / current_width
                    new_height = int(current_height * ratio)
                    img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

                if max_height and img.height > max_height:
                    ratio = max_height / img.height
                    new_width = int(img.width * ratio)
                    img = img.resize((new_width, max_height), Image.Resampling.LANCZOS)

            # 형식 변환
            img_io = io.BytesIO()

            if format and format.lower() == 'jpeg':
                if img.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                img.save(img_io, format='JPEG', quality=quality, optimize=True)
                media_type = "image/jpeg"
                ext = "jpg"
            elif format and format.lower() == 'webp':
                img.save(img_io, format='WebP', quality=quality, optimize=True)
                media_type = "image/webp"
                ext = "webp"
            else:
                # PNG (기본값)
                img.save(img_io, format='PNG', optimize=True)
                media_type = "image/png"
                ext = "png"

            img_io.seek(0)

            return StreamingResponse(
                io.BytesIO(img_io.read()),
                media_type=media_type,
                headers={
                    "Content-Disposition": f"inline; filename={image_path.stem}_proxy.{ext}",
                    "Cache-Control": "public, max-age=3600"
                }
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이미지 프록시 중 오류: {str(e)}")


@router.get("/requests/{request_id}/pages/{page_number}/crop", summary="이미지 영역 크롭")
async def crop_image_region(
    request_id: str,
    page_number: int,
    x: int = Query(..., description="크롭 시작 X 좌표"),
    y: int = Query(..., description="크롭 시작 Y 좌표"),
    width: int = Query(..., description="크롭 너비"),
    height: int = Query(..., description="크롭 높이"),
    padding: Optional[int] = Query(5, description="크롭 영역 패딩 (픽셀)"),
    quality: Optional[int] = Query(85, description="JPEG 품질 (1-100)")
):
    """
    원본 이미지에서 지정된 bbox 좌표 영역을 크롭하여 반환

    Args:
        request_id: UUID v7 요청 ID
        page_number: 페이지 번호 (1부터 시작)
        x: 크롭 시작 X 좌표
        y: 크롭 시작 Y 좌표
        width: 크롭 너비
        height: 크롭 높이
        padding: 크롭 영역 주변 패딩 (기본 5px)
        quality: JPEG 품질

    Returns:
        크롭된 이미지 (JPEG 형식)
    """
    if not validate_request_id(request_id):
        raise HTTPException(status_code=400, detail="유효하지 않은 요청 ID")

    try:
        # 원본 이미지 파일 경로
        original_file = Path(request_storage.base_output_dir) / request_id / "pages" / f"{page_number:03d}" / "original.png"

        if not original_file.exists():
            raise HTTPException(status_code=404, detail="원본 이미지를 찾을 수 없습니다")

        # 이미지 열기 및 크롭
        with Image.open(original_file) as img:
            # 패딩 적용한 크롭 영역 계산
            crop_x1 = max(0, x - padding)
            crop_y1 = max(0, y - padding)
            crop_x2 = min(img.width, x + width + padding)
            crop_y2 = min(img.height, y + height + padding)

            # 크롭
            cropped = img.crop((crop_x1, crop_y1, crop_x2, crop_y2))

            # RGB 모드로 변환 (JPEG 저장을 위해)
            if cropped.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', cropped.size, (255, 255, 255))
                background.paste(cropped, mask=cropped.split()[-1] if cropped.mode == 'RGBA' else None)
                cropped = background
            elif cropped.mode != 'RGB':
                cropped = cropped.convert('RGB')

            # 메모리에 JPEG로 저장
            img_io = io.BytesIO()
            cropped.save(img_io, format='JPEG', quality=quality, optimize=True)
            img_io.seek(0)

            return StreamingResponse(
                io.BytesIO(img_io.read()),
                media_type="image/jpeg",
                headers={
                    "Content-Disposition": f"inline; filename=page_{page_number:03d}_crop_{x}_{y}.jpg",
                    "Cache-Control": "public, max-age=3600"
                }
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이미지 크롭 중 오류: {str(e)}")


__all__ = ['router', 'set_dependencies']
#!/usr/bin/env python3
"""
Request-based API endpoints for OCR processing
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from pathlib import Path
from typing import Dict, Any, List, Optional
import os

from services.file.storage import RequestStorage
from services.file.request_manager import validate_request_id, extract_timestamp_from_uuid
from services.file.directories import list_request_directories, list_page_directories

router = APIRouter()

# 전역 저장소 인스턴스
request_storage = None
extractor = None
pdf_processor = None


def set_dependencies(output_dir: str):
    """의존성 설정"""
    global request_storage
    request_storage = RequestStorage(output_dir)


def set_processing_dependencies(doc_extractor, pdf_proc):
    """처리 관련 의존성 설정"""
    global extractor, pdf_processor
    extractor = doc_extractor
    pdf_processor = pdf_proc


@router.post("/process-request", summary="새로운 요청 기반 문서 처리")
async def process_request(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    merge_blocks: Optional[bool] = Form(True),
    merge_threshold: Optional[int] = Form(30)
) -> Dict[str, Any]:
    """
    새로운 요청 기반 문서 처리

    파일을 업로드하고 UUID 기반 요청으로 처리합니다.
    """
    import tempfile
    import shutil
    import time
    from datetime import datetime

    start_time = time.time()

    try:
        # 파일 정보 수집
        file_content = await file.read()
        file_size = len(file_content)
        file_type = file.filename.split('.')[-1].lower() if '.' in file.filename else 'unknown'

        # 지원되는 파일 타입 확인
        supported_image_types = ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'webp']
        supported_doc_types = ['pdf']

        if file_type not in supported_image_types + supported_doc_types:
            raise HTTPException(status_code=400, detail=f"지원되지 않는 파일 타입: {file_type}")

        # 요청 생성
        request_id = request_storage.create_request(
            original_filename=file.filename,
            file_type=file_type,
            file_size=file_size,
            total_pages=1  # PDF의 경우 실제 처리에서 업데이트
        )

        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_type}") as tmp_file:
            tmp_file.write(file_content)
            tmp_path = tmp_file.name

        try:
            if file_type in supported_image_types:
                # 이미지 처리
                await process_image_request(request_id, tmp_path, file.filename,
                                          merge_blocks, merge_threshold, start_time)
                total_pages = 1

            elif file_type == 'pdf':
                # PDF 처리
                total_pages = await process_pdf_request(request_id, tmp_path, file.filename,
                                                      merge_blocks, merge_threshold, start_time)

            # 메타데이터 업데이트
            metadata = request_storage.get_request_metadata(request_id)
            metadata['total_pages'] = total_pages
            metadata_file = Path(request_storage.base_output_dir) / request_id / 'metadata.json'
            from services.file.metadata import save_metadata
            save_metadata(metadata, metadata_file)

            # 요청 완료 처리
            processing_time = time.time() - start_time
            request_storage.complete_request(request_id, {
                'completed_at': datetime.now().isoformat(),
                'description': description,
                'status': 'completed',
                'total_processing_time': round(processing_time, 3),
                'total_pages': total_pages
            })

            return {
                "request_id": request_id,
                "status": "completed",
                "original_filename": file.filename,
                "file_type": file_type,
                "file_size": file_size,
                "total_pages": total_pages,
                "processing_time": round(processing_time, 3),
                "processing_url": f"/requests/{request_id}"
            }

        finally:
            # 임시 파일 정리
            if Path(tmp_path).exists():
                Path(tmp_path).unlink()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"처리 중 오류 발생: {str(e)}")


async def process_image_request(request_id: str, image_path: str, original_filename: str,
                               merge_blocks: bool, merge_threshold: int, start_time: float) -> None:
    """이미지 요청 처리"""
    try:
        import time

        # OCR 처리
        result = extractor.extract_blocks(image_path, merge_blocks=merge_blocks, merge_threshold=merge_threshold)
        blocks = result.get('blocks', [])

        # 블록 데이터 변환
        processed_blocks = []
        for i, block in enumerate(blocks):
            processed_blocks.append({
                'text': block['text'],
                'confidence': block['confidence'],
                'bbox': block['bbox_points'],
                'block_type': block['type']
            })

        # 시각화 이미지 생성
        visualization_data = None
        if blocks and 'visualization_path' in result:
            with open(result['visualization_path'], 'rb') as f:
                visualization_data = f.read()

        # 원본 이미지 데이터 읽기
        original_image_data = None
        try:
            with open(image_path, 'rb') as f:
                original_image_data = f.read()
        except Exception:
            original_image_data = None

        # 처리 시간 계산
        processing_time = time.time() - start_time

        # 결과 저장
        request_storage.save_page_result(
            request_id=request_id,
            page_number=1,
            blocks=processed_blocks,
            processing_time=processing_time,
            visualization_data=visualization_data,
            original_image_data=original_image_data
        )

    except Exception as e:
        raise Exception(f"이미지 처리 중 오류: {str(e)}")


async def process_pdf_request(request_id: str, pdf_path: str, original_filename: str,
                             merge_blocks: bool, merge_threshold: int, start_time: float) -> int:
    """PDF 요청 처리"""
    try:
        import time

        # PDF를 이미지로 변환
        image_paths = pdf_processor.convert_pdf_to_images(pdf_path, '/tmp')
        total_pages = len(image_paths)

        for page_num, image_path in enumerate(image_paths, 1):
            page_start_time = time.time()

            # 각 페이지 OCR 처리
            result = extractor.extract_blocks(image_path, merge_blocks=merge_blocks, merge_threshold=merge_threshold)
            blocks = result.get('blocks', [])

            # 블록 데이터 변환
            processed_blocks = []
            for i, block in enumerate(blocks):
                processed_blocks.append({
                    'text': block['text'],
                    'confidence': block['confidence'],
                    'bbox': block['bbox_points'],
                    'block_type': block['type']
                })

            # 시각화 이미지 생성
            visualization_data = None
            if blocks and 'visualization_path' in result:
                with open(result['visualization_path'], 'rb') as f:
                    visualization_data = f.read()

            # 원본 페이지 이미지 데이터 읽기
            original_image_data = None
            try:
                with open(image_path, 'rb') as f:
                    original_image_data = f.read()
            except Exception:
                original_image_data = None

            # 페이지 처리 시간 계산
            page_processing_time = time.time() - page_start_time

            # 페이지 결과 저장
            request_storage.save_page_result(
                request_id=request_id,
                page_number=page_num,
                blocks=processed_blocks,
                processing_time=page_processing_time,
                visualization_data=visualization_data,
                original_image_data=original_image_data
            )

            # 임시 이미지 파일 정리
            if Path(image_path).exists():
                Path(image_path).unlink()

        return total_pages

    except Exception as e:
        raise Exception(f"PDF 처리 중 오류: {str(e)}")


@router.get("/requests", summary="모든 요청 목록 조회")
async def list_requests() -> Dict[str, Any]:
    """모든 요청 목록을 시간순으로 조회"""
    try:
        request_ids = list_request_directories(str(request_storage.base_output_dir))

        requests_info = []
        for request_id in request_ids:
            try:
                metadata = request_storage.get_request_metadata(request_id)
                timestamp = extract_timestamp_from_uuid(request_id)

                requests_info.append({
                    "request_id": request_id,
                    "original_filename": metadata.get('original_filename'),
                    "file_type": metadata.get('file_type'),
                    "total_pages": metadata.get('total_pages', 1),
                    "status": metadata.get('processing_status'),
                    "created_at": metadata.get('created_at'),
                    "timestamp": timestamp.isoformat() if timestamp else None
                })
            except Exception:
                continue

        return {
            "total_requests": len(requests_info),
            "requests": requests_info
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"요청 목록 조회 중 오류: {str(e)}")


@router.get("/requests/{request_id}", summary="특정 요청 정보 조회")
async def get_request_info(request_id: str) -> Dict[str, Any]:
    """특정 요청의 상세 정보 조회"""
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

        return {
            "request_id": request_id,
            "metadata": metadata,
            "total_pages": len(pages_info),
            "pages": pages_info
        }

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="요청을 찾을 수 없습니다")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"요청 정보 조회 중 오류: {str(e)}")


@router.get("/requests/{request_id}/pages/{page_number}", summary="특정 페이지 결과 조회")
async def get_page_result(request_id: str, page_number: int) -> Dict[str, Any]:
    """특정 요청의 특정 페이지 결과 조회"""
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


@router.get("/requests/{request_id}/pages/{page_number}/blocks/{block_id}", summary="특정 블록 데이터 조회")
async def get_block_data(request_id: str, page_number: int, block_id: int) -> Dict[str, Any]:
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
async def download_page_visualization(request_id: str, page_number: int):
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


@router.delete("/requests/{request_id}", summary="요청 삭제")
async def delete_request(request_id: str) -> Dict[str, Any]:
    """특정 요청과 관련된 모든 데이터 삭제"""
    if not validate_request_id(request_id):
        raise HTTPException(status_code=400, detail="유효하지 않은 요청 ID")

    try:
        request_dir = request_storage.base_output_dir / request_id

        if not request_dir.exists():
            raise HTTPException(status_code=404, detail="요청을 찾을 수 없습니다")

        # 디렉토리 전체 삭제
        import shutil
        shutil.rmtree(request_dir)

        return {
            "request_id": request_id,
            "status": "deleted",
            "message": "요청이 성공적으로 삭제되었습니다"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"요청 삭제 중 오류: {str(e)}")


@router.get("/requests/{request_id}/pages/{page_number}/original", summary="페이지 원본 이미지 다운로드")
async def get_page_original_image(request_id: str, page_number: int):
    """페이지의 원본 이미지를 다운로드"""
    if not validate_request_id(request_id):
        raise HTTPException(status_code=400, detail="유효하지 않은 요청 ID")

    try:
        from fastapi.responses import FileResponse

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
async def get_block_image(request_id: str, page_number: int, block_id: int):
    """개별 블록의 크롭된 이미지를 다운로드"""
    if not validate_request_id(request_id):
        raise HTTPException(status_code=400, detail="유효하지 않은 요청 ID")

    try:
        from fastapi.responses import FileResponse

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
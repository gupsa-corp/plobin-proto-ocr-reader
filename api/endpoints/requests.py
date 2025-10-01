#!/usr/bin/env python3
"""
Request-based API endpoints for OCR processing
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
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


@router.post("/process-request", summary="UUID 기반 문서 처리 요청 생성")
async def process_request(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    merge_blocks: Optional[bool] = Form(True),
    merge_threshold: Optional[int] = Form(30)
) -> Dict[str, Any]:
    """
    UUID v7 기반 문서 처리 요청 생성

    - 파일 업로드 및 시간 기반 UUID v7 생성
    - 이미지/PDF 파일의 OCR 처리
    - 계층적 디렉토리 구조로 결과 저장
    - 블록별 개별 접근 가능한 구조 생성
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
        if blocks:
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as viz_tmp:
                viz_path = viz_tmp.name

            try:
                # 시각화 생성
                extractor.visualize_blocks(image_path, result, viz_path)

                # 시각화 파일 읽기
                if Path(viz_path).exists():
                    with open(viz_path, 'rb') as f:
                        visualization_data = f.read()

            except Exception as e:
                print(f"시각화 생성 실패: {e}")
                visualization_data = None
            finally:
                # 임시 시각화 파일 정리
                if Path(viz_path).exists():
                    Path(viz_path).unlink()

        # 원본 이미지 데이터 읽기
        original_image_data = None
        try:
            with open(image_path, 'rb') as f:
                original_image_data = f.read()
        except Exception:
            original_image_data = None

        # 처리 시간 계산
        processing_time = time.time() - start_time

        # 콘텐츠 요약 생성
        from services.analysis import ContentSummarizer
        summarizer = ContentSummarizer()
        content_summary = summarizer.create_comprehensive_summary(processed_blocks)

        # 결과 저장
        request_storage.save_page_result(
            request_id=request_id,
            page_number=1,
            blocks=processed_blocks,
            processing_time=processing_time,
            visualization_data=visualization_data,
            original_image_data=original_image_data,
            content_summary=content_summary
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
            if blocks:
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as viz_tmp:
                    viz_path = viz_tmp.name

                try:
                    # 시각화 생성
                    extractor.visualize_blocks(image_path, result, viz_path)

                    # 시각화 파일 읽기
                    if Path(viz_path).exists():
                        with open(viz_path, 'rb') as f:
                            visualization_data = f.read()

                except Exception as e:
                    print(f"페이지 {page_num} 시각화 생성 실패: {e}")
                    visualization_data = None
                finally:
                    # 임시 시각화 파일 정리
                    if Path(viz_path).exists():
                        Path(viz_path).unlink()

            # 원본 페이지 이미지 데이터 읽기
            original_image_data = None
            try:
                with open(image_path, 'rb') as f:
                    original_image_data = f.read()
            except Exception:
                original_image_data = None

            # 페이지 처리 시간 계산
            page_processing_time = time.time() - page_start_time

            # 콘텐츠 요약 생성
            from services.analysis import ContentSummarizer
            summarizer = ContentSummarizer()
            content_summary = summarizer.create_comprehensive_summary(processed_blocks)

            # 페이지 결과 저장
            request_storage.save_page_result(
                request_id=request_id,
                page_number=page_num,
                blocks=processed_blocks,
                processing_time=page_processing_time,
                visualization_data=visualization_data,
                original_image_data=original_image_data,
                content_summary=content_summary
            )

            # 임시 이미지 파일 정리
            if Path(image_path).exists():
                Path(image_path).unlink()

        return total_pages

    except Exception as e:
        raise Exception(f"PDF 처리 중 오류: {str(e)}")


@router.get("/requests", summary="UUID v7 요청 목록 조회 (페이지네이션 지원)")
async def list_requests(
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수 (1-100)"),
    search: Optional[str] = Query(None, description="파일명 검색어"),
    file_type: Optional[str] = Query(None, description="파일 타입 필터 (pdf, jpg, png 등)")
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
async def get_request_info(request_id: str) -> Dict[str, Any]:
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


@router.get("/requests/{request_id}/pages/{page_number}", summary="UUID 요청의 페이지별 OCR 결과 조회")
async def get_page_result(request_id: str, page_number: int) -> Dict[str, Any]:
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


@router.delete("/requests/{request_id}", summary="UUID 요청 및 관련 데이터 완전 삭제")
async def delete_request(request_id: str) -> Dict[str, Any]:
    """
    특정 UUID 요청과 관련된 모든 데이터 완전 삭제

    - 요청 디렉토리 전체 삭제 (페이지, 블록, 이미지 포함)
    - 복구 불가능한 완전 삭제
    - UUID 유효성 검증 후 실행
    """
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


@router.get("/requests/{request_id}/pages/{page_number}/content-summary", summary="페이지 콘텐츠 요약 조회")
async def get_page_content_summary(request_id: str, page_number: int) -> Dict[str, Any]:
    """페이지의 콘텐츠 요약 정보를 조회합니다"""
    try:
        if not validate_request_id(request_id):
            raise HTTPException(status_code=400, detail="잘못된 요청 ID 형식")

        # 요약 파일 경로
        summary_file = Path(request_storage.base_output_dir) / request_id / "pages" / f"{page_number:03d}" / "content_summary.json"

        if not summary_file.exists():
            raise HTTPException(status_code=404, detail="콘텐츠 요약을 찾을 수 없습니다")

        # 요약 데이터 로드
        from services.file.metadata import load_metadata
        summary_data = load_metadata(summary_file)

        return {
            "request_id": request_id,
            "page_number": page_number,
            "content_summary": summary_data,
            "summary_created_at": summary_data.get('page_summary', {}).get('analyzed_at'),
            "summary_file_path": str(summary_file)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"요약 조회 중 오류: {str(e)}")


@router.post("/requests/{request_id}/pages/{page_number}/regenerate-visualization", summary="페이지 시각화 재생성")
async def regenerate_page_visualization(request_id: str, page_number: int) -> Dict[str, Any]:
    """페이지 시각화 이미지를 재생성합니다"""
    try:
        if not validate_request_id(request_id):
            raise HTTPException(status_code=400, detail="잘못된 요청 ID 형식")

        # 페이지 디렉토리 확인
        page_dir = Path(request_storage.base_output_dir) / request_id / "pages" / f"{page_number:03d}"

        if not page_dir.exists():
            raise HTTPException(status_code=404, detail="페이지를 찾을 수 없습니다")

        # 필요한 파일들 확인
        result_file = page_dir / "result.json"
        original_file = page_dir / "original.png"

        if not result_file.exists():
            raise HTTPException(status_code=404, detail="페이지 결과 파일을 찾을 수 없습니다")

        if not original_file.exists():
            raise HTTPException(status_code=404, detail="원본 이미지를 찾을 수 없습니다")

        # 결과 데이터 로드
        from services.file.metadata import load_metadata
        result_data = load_metadata(result_file)
        blocks = result_data.get('blocks', [])

        # 시각화 생성
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as viz_tmp:
            viz_path = viz_tmp.name

        try:
            # OCR 결과 형태로 변환 (시각화 함수가 기대하는 형식으로)
            converted_blocks = []
            for block in blocks:
                bbox_data = block.get('bbox', {})

                # bbox 형식 확인 및 변환
                if isinstance(bbox_data, list) and len(bbox_data) >= 4:
                    # 좌표 배열 형식: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                    x_coords = [point[0] for point in bbox_data]
                    y_coords = [point[1] for point in bbox_data]
                    x_min, x_max = min(x_coords), max(x_coords)
                    y_min, y_max = min(y_coords), max(y_coords)

                    bbox_converted = {
                        'x_min': x_min,
                        'y_min': y_min,
                        'width': x_max - x_min,
                        'height': y_max - y_min,
                        'x_max': x_max,
                        'y_max': y_max
                    }
                elif isinstance(bbox_data, dict) and 'x_min' in bbox_data:
                    # 이미 객체 형식: {x_min, y_min, x_max, y_max, width, height}
                    bbox_converted = {
                        'x_min': bbox_data.get('x_min', 0),
                        'y_min': bbox_data.get('y_min', 0),
                        'width': bbox_data.get('width', bbox_data.get('x_max', 0) - bbox_data.get('x_min', 0)),
                        'height': bbox_data.get('height', bbox_data.get('y_max', 0) - bbox_data.get('y_min', 0)),
                        'x_max': bbox_data.get('x_max', bbox_data.get('x_min', 0) + bbox_data.get('width', 0)),
                        'y_max': bbox_data.get('y_max', bbox_data.get('y_min', 0) + bbox_data.get('height', 0))
                    }
                else:
                    # 유효하지 않은 bbox 데이터는 건너뛰기
                    continue

                converted_block = {
                    'text': block.get('text', ''),
                    'confidence': block.get('confidence', 0.0),
                    'type': block.get('block_type', block.get('type', 'other')),  # block_type 또는 type
                    'bbox': bbox_converted
                }
                converted_blocks.append(converted_block)

            ocr_result = {'blocks': converted_blocks}

            # 시각화 생성
            if extractor:
                extractor.visualize_blocks(str(original_file), ocr_result, viz_path)
            else:
                raise Exception("OCR 추출기가 초기화되지 않았습니다")

            # 시각화 파일이 생성되었는지 확인
            if Path(viz_path).exists():
                # 기존 시각화 파일을 새 것으로 교체
                visualization_file = page_dir / "visualization.png"
                import shutil
                shutil.move(viz_path, visualization_file)

                return {
                    "request_id": request_id,
                    "page_number": page_number,
                    "status": "success",
                    "message": "시각화가 성공적으로 재생성되었습니다",
                    "visualization_file": str(visualization_file),
                    "file_size": visualization_file.stat().st_size
                }
            else:
                raise Exception("시각화 파일이 생성되지 않았습니다")

        except Exception as e:
            # 임시 파일 정리
            if Path(viz_path).exists():
                Path(viz_path).unlink()
            raise Exception(f"시각화 생성 실패: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시각화 재생성 중 오류: {str(e)}")


@router.get("/requests/{request_id}/pages/{page_number}/metadata", summary="페이지 이미지 메타데이터 조회")
async def get_page_metadata(request_id: str, page_number: int) -> Dict[str, Any]:
    """
    페이지 이미지의 메타데이터 정보 조회

    이미지 뷰어 구현에 필요한 기본 정보들을 제공합니다:
    - 이미지 크기 (width, height)
    - 파일 크기
    - 이미지 포맷
    """
    if not validate_request_id(request_id):
        raise HTTPException(status_code=400, detail="유효하지 않은 요청 ID")

    try:
        # 원본 이미지 파일 경로
        original_file = request_storage.base_output_dir / request_id / "pages" / f"{page_number:03d}" / "original.png"

        if not original_file.exists():
            raise HTTPException(status_code=404, detail="원본 이미지를 찾을 수 없습니다")

        # 이미지 메타데이터 추출
        import cv2
        import numpy as np

        image = cv2.imread(str(original_file))
        if image is None:
            raise HTTPException(status_code=500, detail="이미지를 읽을 수 없습니다")

        height, width = image.shape[:2]
        channels = image.shape[2] if len(image.shape) == 3 else 1

        # 파일 크기
        file_size = original_file.stat().st_size

        # 이미지 통계 정보
        file_stat = original_file.stat()

        return {
            "request_id": request_id,
            "page_number": page_number,
            "image_metadata": {
                "width": int(width),
                "height": int(height),
                "channels": int(channels),
                "format": "PNG",
                "file_size": file_size,
                "file_size_mb": round(file_size / 1024 / 1024, 2),
                "aspect_ratio": round(width / height, 3),
                "resolution": f"{width}x{height}",
                "megapixels": round(width * height / 1000000, 2)
            },
            "file_info": {
                "created_at": file_stat.st_ctime,
                "modified_at": file_stat.st_mtime,
                "file_path": str(original_file.relative_to(request_storage.base_output_dir))
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"메타데이터 조회 중 오류: {str(e)}")


@router.get("/requests/{request_id}/pages/{page_number}/thumbnail", summary="페이지 썸네일 이미지 조회")
async def get_page_thumbnail(
    request_id: str,
    page_number: int,
    size: int = Query(300, ge=50, le=800, description="썸네일 크기 (픽셀)")
):
    """
    페이지의 썸네일 이미지를 조회합니다

    썸네일이 존재하지 않으면 자동으로 생성합니다.
    """
    if not validate_request_id(request_id):
        raise HTTPException(status_code=400, detail="유효하지 않은 요청 ID")

    try:
        # 썸네일 파일 경로
        thumbnail_dir = request_storage.base_output_dir / request_id / "pages" / f"{page_number:03d}" / "thumbnails"
        thumbnail_file = thumbnail_dir / f"thumb_{size}.png"

        # 썸네일이 이미 존재하면 반환
        if thumbnail_file.exists():
            return FileResponse(
                path=str(thumbnail_file),
                media_type="image/png",
                filename=f"page_{page_number}_thumb_{size}.png"
            )

        # 썸네일이 없으면 생성
        original_file = request_storage.base_output_dir / request_id / "pages" / f"{page_number:03d}" / "original.png"

        if not original_file.exists():
            raise HTTPException(status_code=404, detail="원본 이미지를 찾을 수 없습니다")

        # 썸네일 디렉토리 생성
        thumbnail_dir.mkdir(exist_ok=True)

        # PIL로 썸네일 생성
        from PIL import Image

        with Image.open(original_file) as img:
            # 비율 유지하면서 리사이즈
            img.thumbnail((size, size), Image.Resampling.LANCZOS)

            # PNG로 저장
            img.save(thumbnail_file, "PNG", optimize=True)

        return FileResponse(
            path=str(thumbnail_file),
            media_type="image/png",
            filename=f"page_{page_number}_thumb_{size}.png"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"썸네일 생성 중 오류: {str(e)}")


@router.post("/requests/{request_id}/generate-thumbnails", summary="요청의 모든 페이지 썸네일 일괄 생성")
async def generate_all_thumbnails(
    request_id: str,
    size: int = Query(300, ge=50, le=800, description="썸네일 크기 (픽셀)")
) -> Dict[str, Any]:
    """
    요청의 모든 페이지에 대해 썸네일을 일괄 생성합니다
    """
    if not validate_request_id(request_id):
        raise HTTPException(status_code=400, detail="유효하지 않은 요청 ID")

    try:
        # 페이지 목록 가져오기
        page_numbers = list_page_directories(str(request_storage.base_output_dir), request_id)

        generated = []
        failed = []

        for page_num in page_numbers:
            try:
                # 각 페이지의 썸네일 생성
                original_file = request_storage.base_output_dir / request_id / "pages" / f"{page_num:03d}" / "original.png"

                if original_file.exists():
                    thumbnail_dir = request_storage.base_output_dir / request_id / "pages" / f"{page_num:03d}" / "thumbnails"
                    thumbnail_file = thumbnail_dir / f"thumb_{size}.png"

                    # 이미 존재하지 않을 때만 생성
                    if not thumbnail_file.exists():
                        thumbnail_dir.mkdir(exist_ok=True)

                        from PIL import Image
                        with Image.open(original_file) as img:
                            img.thumbnail((size, size), Image.Resampling.LANCZOS)
                            img.save(thumbnail_file, "PNG", optimize=True)

                    generated.append(page_num)
                else:
                    failed.append({"page": page_num, "reason": "원본 이미지 없음"})

            except Exception as e:
                failed.append({"page": page_num, "reason": str(e)})

        return {
            "request_id": request_id,
            "thumbnail_size": size,
            "total_pages": len(page_numbers),
            "generated_count": len(generated),
            "failed_count": len(failed),
            "generated_pages": generated,
            "failed_pages": failed
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"썸네일 일괄 생성 중 오류: {str(e)}")


@router.get("/search/blocks", summary="전체 블록 텍스트 검색")
async def search_blocks(
    q: str = Query(..., min_length=2, description="검색어 (최소 2자)"),
    request_id: Optional[str] = Query(None, description="특정 요청 내에서만 검색"),
    limit: int = Query(50, ge=1, le=200, description="최대 결과 수")
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
        raise HTTPException(status_code=500, detail=f"블록 검색 중 오류: {str(e)}")
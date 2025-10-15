from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from typing import List, Optional
from pathlib import Path
import tempfile
import shutil
import time
import os
from datetime import datetime

from api.models.schemas import ProcessingResult, BlockInfo
from services.file.request_manager import generate_request_metadata, create_request_structure, create_page_structure, create_block_file_path
from services.file.storage import RequestStorage
from services.ocr.extraction import crop_all_blocks

router = APIRouter()

# Global dependencies that will be injected
server_stats = None
extractor = None
pdf_processor = None
output_dir = None

def set_dependencies(stats, doc_extractor, pdf_proc, out_dir=None):
    global server_stats, extractor, pdf_processor, output_dir
    server_stats = stats
    extractor = doc_extractor
    pdf_processor = pdf_proc
    output_dir = out_dir or "output"

@router.post("/process-pdf")
async def process_pdf(
    file: UploadFile = File(...),
    merge_blocks: Optional[bool] = Query(True, description="인접한 블록들을 병합하여 문장 단위로 그룹화"),
    merge_threshold: Optional[int] = Query(30, description="블록 병합 임계값 (픽셀 단위)"),
    create_sections: Optional[bool] = Query(False, description="블록들을 논리적 섹션으로 그룹화 (header, body, footer 등)"),
    build_hierarchy_tree: Optional[bool] = Query(False, description="블록 간 계층 구조 구축 (포함 관계)")
):
    start_time = time.time()
    server_stats["total_requests"] += 1
    server_stats["last_request_time"] = datetime.now()

    if not file.content_type or file.content_type != 'application/pdf':
        server_stats["errors"] += 1
        raise HTTPException(status_code=400, detail="File must be a PDF")

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_path = tmp_file.name

        try:
            # 파일 정보 가져오기
            file_stats = os.stat(tmp_path)
            file_size = file_stats.st_size

            with tempfile.TemporaryDirectory() as temp_dir:
                print(f"🔄 PDF 변환 시작: {file.filename}")
                image_paths = pdf_processor.convert_pdf_to_images(tmp_path, temp_dir)
                total_pages = len(image_paths)
                print(f"✅ PDF 변환 완료: {total_pages} 페이지")

                # RequestStorage를 사용해서 저장
                storage = RequestStorage(output_dir)

                # 요청 생성
                request_id = storage.create_request(file.filename, "pdf", file_size, total_pages=total_pages)

                # 페이지별 처리 및 저장
                all_pages_data = []
                total_blocks_count = 0
                total_confidence_sum = 0

                for i, image_path in enumerate(image_paths):
                    page_num = i + 1
                    page_start_time = time.time()
                    print(f"🔄 페이지 {page_num} OCR 처리 시작...")

                    result = extractor.extract_blocks(
                        image_path,
                        merge_blocks=merge_blocks,
                        merge_threshold=merge_threshold,
                        create_sections=create_sections,
                        build_hierarchy_tree=build_hierarchy_tree
                    )
                    blocks = result.get('blocks', [])
                    page_processing_time = time.time() - page_start_time

                    # 메타데이터 준비 (섹션/계층 정보 포함)
                    ocr_metadata = {}
                    if create_sections and 'sections' in result:
                        ocr_metadata['sections'] = result['sections']
                        ocr_metadata['section_summary'] = result.get('section_summary', {})

                    if build_hierarchy_tree and 'hierarchical_blocks' in result:
                        ocr_metadata['hierarchical_blocks'] = result['hierarchical_blocks']
                        ocr_metadata['hierarchy_statistics'] = result.get('hierarchy_statistics', {})

                    # 페이지 결과 저장
                    storage.save_page_result(request_id, page_num, blocks, page_processing_time, metadata=ocr_metadata if ocr_metadata else None)

                    # 원본 이미지 저장 (PDF에서 변환된 페이지 이미지)
                    try:
                        storage.save_original_image(request_id, page_num, image_path)
                    except Exception as e:
                        print(f"페이지 {page_num} 원본 이미지 저장 실패: {e}")

                    # 블록별 이미지 크롭 및 저장
                    if blocks:
                        try:
                            cropped_blocks = crop_all_blocks(image_path, blocks, padding=5)
                            storage.save_block_images(request_id, page_num, cropped_blocks)
                        except Exception as e:
                            print(f"페이지 {page_num} 블록 이미지 저장 실패: {e}")

                    # 시각화 저장
                    if blocks:
                        try:
                            request_dir = Path(output_dir) / request_id
                            viz_path = request_dir / "pages" / f"{page_num:03d}" / "visualization.png"
                            extractor.visualize_blocks(image_path, {'blocks': blocks}, str(viz_path))
                        except Exception as e:
                            print(f"페이지 {page_num} 시각화 생성 실패: {e}")

                    # 통계 누적
                    total_blocks_count += len(blocks)
                    if blocks:
                        page_confidence = sum(block.get('confidence', 0) for block in blocks) / len(blocks)
                        total_confidence_sum += page_confidence
                        all_pages_data.append({
                            "page_number": page_num,
                            "total_blocks": len(blocks),
                            "average_confidence": round(page_confidence, 3),
                            "processing_time": round(page_processing_time, 3)
                        })
                    else:
                        all_pages_data.append({
                            "page_number": page_num,
                            "total_blocks": 0,
                            "average_confidence": 0.0,
                            "processing_time": round(page_processing_time, 3)
                        })

                # 요청 완료 처리
                processing_time = time.time() - start_time
                overall_confidence = total_confidence_sum / max(len([p for p in all_pages_data if p["total_blocks"] > 0]), 1)

                summary_data = {
                    "total_pages": total_pages,
                    "total_blocks": total_blocks_count,
                    "overall_confidence": round(overall_confidence, 3),
                    "processing_time": round(processing_time, 3),
                    "pages": all_pages_data,
                    "completed_at": datetime.now().isoformat(),
                    "sections_created": create_sections,
                    "hierarchy_built": build_hierarchy_tree
                }
                storage.complete_request(request_id, summary_data)

                # 통계 업데이트
                server_stats["total_pdfs_processed"] += 1
                server_stats["total_blocks_extracted"] += total_blocks_count
                server_stats["total_processing_time"] += processing_time

                return {
                    "request_id": request_id,
                    "status": "completed",
                    "original_filename": file.filename,
                    "file_type": "pdf",
                    "file_size": file_size,
                    "total_pages": total_pages,
                    "processing_time": round(processing_time, 3),
                    "processing_url": f"/requests/{request_id}"
                }

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except Exception as e:
        server_stats["errors"] += 1
        import traceback
        error_details = {
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc(),
            "filename": file.filename if file else "unknown",
            "request_id": request_id if 'request_id' in locals() else "unknown"
        }
        print(f"❌ PDF 처리 오류: {error_details}")

        # 파이프 오류 특별 처리
        if "Broken pipe" in str(e) or "파이프가 깨어짐" in str(e):
            print(f"🔍 파이프 오류 디버깅 정보:")
            print(f"   - 임시 파일 경로: {tmp_path if 'tmp_path' in locals() else 'unknown'}")
            print(f"   - 출력 디렉토리: {output_dir}")
            print(f"   - 현재 작업 디렉토리: {os.getcwd()}")

        raise HTTPException(status_code=500, detail=f"처리 중 오류 발생: PDF 처리 중 오류: {str(e)}")

@router.post("/process-document")
async def process_document(file: UploadFile = File(...)):
    """범용 문서 처리 (이미지/PDF 자동 감지)"""
    content_type = file.content_type or ""

    if content_type == 'application/pdf':
        return await process_pdf(file)
    elif content_type.startswith('image/'):
        from api.endpoints.process_image import process_image
        return await process_image(file)
    else:
        raise HTTPException(
            status_code=400,
            detail="File must be an image (JPEG, PNG, etc.) or PDF"
        )
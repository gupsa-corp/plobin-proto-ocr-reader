from fastapi import APIRouter, File, UploadFile, HTTPException
from typing import List
import tempfile
import shutil
import time
import os
from datetime import datetime

from api.models.schemas import ProcessingResult, BlockInfo
from api.utils.file_storage import save_processing_results, create_pdf_summary

router = APIRouter()

# Global dependencies that will be injected
server_stats = None
extractor = None
pdf_processor = None

def set_dependencies(stats, doc_extractor, pdf_proc):
    global server_stats, extractor, pdf_processor
    server_stats = stats
    extractor = doc_extractor
    pdf_processor = pdf_proc

@router.post("/process-pdf", response_model=List[ProcessingResult])
async def process_pdf(file: UploadFile = File(...)):
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
            with tempfile.TemporaryDirectory() as temp_dir:
                image_paths = pdf_processor.convert_pdf_to_images(tmp_path, temp_dir)

                results = []

                for i, image_path in enumerate(image_paths):
                    result = extractor.extract_blocks(image_path)
                    blocks = result.get('blocks', [])

                    if blocks:
                        block_infos = []
                        total_confidence = 0

                        for block in blocks:
                            block_info = BlockInfo(
                                text=block['text'],
                                confidence=block['confidence'],
                                bbox=block['bbox_points'],
                                block_type=block['type']
                            )
                            block_infos.append(block_info)
                            total_confidence += block['confidence']

                        avg_confidence = total_confidence / len(blocks)

                        # 페이지별 결과 데이터 준비
                        page_filename = f"{file.filename}_page_{i+1}"
                        result_data = {
                            "filename": page_filename,
                            "page_number": i+1,
                            "total_blocks": len(blocks),
                            "average_confidence": round(avg_confidence, 3),
                            "blocks": [block.dict() for block in block_infos]
                        }

                        # 페이지별 output 파일 저장
                        output_files = save_processing_results(
                            file.filename, result_data, blocks, image_path,
                            file_type="pdf", page_num=i+1
                        )

                        result = ProcessingResult(
                            filename=page_filename,
                            total_blocks=len(blocks),
                            average_confidence=round(avg_confidence, 3),
                            blocks=block_infos,
                            output_files=output_files
                        )
                    else:
                        result = ProcessingResult(
                            filename=f"{file.filename}_page_{i+1}",
                            total_blocks=0,
                            average_confidence=0.0,
                            blocks=[],
                            output_files=None
                        )

                    results.append(result)

                # PDF 처리 통계 업데이트
                processing_time = time.time() - start_time
                server_stats["total_pdfs_processed"] += 1
                total_blocks = sum(r.total_blocks for r in results)
                server_stats["total_blocks_extracted"] += total_blocks
                server_stats["total_processing_time"] += processing_time

                # PDF 요약 파일 저장
                all_pages_data = []
                for result in results:
                    all_pages_data.append({
                        "blocks": [block.dict() for block in result.blocks]
                    })

                summary_info = create_pdf_summary(file.filename, results)

                # 첫 번째 결과에 PDF 요약 정보 추가
                if results:
                    if results[0].output_files is None:
                        results[0].output_files = {}
                    results[0].output_files.update({
                        "pdf_summary": summary_info["summary_path"],
                        "pdf_folder": summary_info["relative_path"]
                    })

                return results

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except Exception as e:
        server_stats["errors"] += 1
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

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
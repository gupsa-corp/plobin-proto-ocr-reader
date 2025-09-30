from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from pathlib import Path
import tempfile
import shutil
import time
import os
from datetime import datetime
from typing import Optional

from api.models.schemas import ProcessingResult, BlockInfo
from api.utils.file_storage import save_processing_results

router = APIRouter()

# Global dependencies that will be injected
server_stats = None
extractor = None

def set_dependencies(stats, doc_extractor):
    global server_stats, extractor
    server_stats = stats
    extractor = doc_extractor

@router.post("/process-image", response_model=ProcessingResult)
async def process_image(
    file: UploadFile = File(...),
    merge_blocks: Optional[bool] = Query(True, description="인접한 블록들을 병합하여 문장 단위로 그룹화"),
    merge_threshold: Optional[int] = Query(30, description="블록 병합 임계값 (픽셀 단위)")
):
    start_time = time.time()
    server_stats["total_requests"] += 1
    server_stats["last_request_time"] = datetime.now()

    if not file.content_type or not file.content_type.startswith('image/'):
        server_stats["errors"] += 1
        raise HTTPException(status_code=400, detail="File must be an image")

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_path = tmp_file.name

        try:
            result = extractor.extract_blocks(tmp_path, merge_blocks=merge_blocks, merge_threshold=merge_threshold)
            blocks = result.get('blocks', [])

            if not blocks:
                return ProcessingResult(
                    filename=file.filename,
                    total_blocks=0,
                    average_confidence=0.0,
                    blocks=[]
                )

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

            # 통계 업데이트
            processing_time = time.time() - start_time
            server_stats["total_images_processed"] += 1
            server_stats["total_blocks_extracted"] += len(blocks)
            server_stats["total_processing_time"] += processing_time

            # Output 파일 저장
            result_data = {
                "filename": file.filename,
                "total_blocks": len(blocks),
                "average_confidence": round(avg_confidence, 3),
                "processing_time": round(processing_time, 3),
                "blocks": [block.dict() for block in block_infos],
                "image_info": {
                    "width": result.get('image_width', 0),
                    "height": result.get('image_height', 0)
                }
            }

            output_files = save_processing_results(
                file.filename, result_data, blocks, tmp_path, file_type="image"
            )

            return ProcessingResult(
                filename=file.filename,
                total_blocks=len(blocks),
                average_confidence=round(avg_confidence, 3),
                blocks=block_infos,
                processing_time=round(processing_time, 3),
                output_files=output_files
            )

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except Exception as e:
        server_stats["errors"] += 1
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
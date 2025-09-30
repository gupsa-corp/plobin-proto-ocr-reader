from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from pathlib import Path
import tempfile
import shutil
import time
import os
from datetime import datetime
from typing import Optional

from api.models.schemas import ProcessingResult, BlockInfo
from services.file.request_manager import generate_request_metadata, create_request_structure, create_page_structure, create_block_file_path
from services.file.storage import RequestStorage

router = APIRouter()

# Global dependencies that will be injected
server_stats = None
extractor = None
output_dir = None

def set_dependencies(stats, doc_extractor, out_dir=None):
    global server_stats, extractor, output_dir
    server_stats = stats
    extractor = doc_extractor
    output_dir = out_dir or "output"

@router.post("/process-image")
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

            # UUID 기반 새로운 구조로 저장
            file_stats = Path(tmp_path).stat() if Path(tmp_path).exists() else None
            file_size = file_stats.st_size if file_stats else 0

            # RequestStorage를 사용해서 저장
            storage = RequestStorage(output_dir)

            # 요청 생성
            request_id = storage.create_request(file.filename, "image", file_size, total_pages=1)

            # 페이지 결과 저장
            storage.save_page_result(request_id, 1, blocks, processing_time)

            # 시각화 저장
            if tmp_path and os.path.exists(tmp_path):
                try:
                    request_dir = Path(output_dir) / request_id
                    viz_path = request_dir / "pages" / "001" / "visualization.png"
                    extractor.visualize_blocks(tmp_path, {'blocks': blocks}, str(viz_path))
                except Exception as e:
                    print(f"시각화 생성 실패: {e}")

            # 요청 완료 처리
            summary_data = {
                "total_pages": 1,
                "total_blocks": len(blocks),
                "overall_confidence": round(avg_confidence, 3),
                "processing_time": round(processing_time, 3),
                "completed_at": datetime.now().isoformat()
            }
            storage.complete_request(request_id, summary_data)

            output_files = {
                "request_id": request_id,
                "processing_url": f"/requests/{request_id}",
                "page_url": f"/requests/{request_id}/pages/1",
                "visualization_url": f"/requests/{request_id}/pages/1/visualization"
            }

            return {
                "request_id": request_id,
                "status": "completed",
                "original_filename": file.filename,
                "file_type": "image",
                "file_size": file_size,
                "total_pages": 1,
                "processing_time": round(processing_time, 3),
                "processing_url": f"/requests/{request_id}"
            }

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except Exception as e:
        server_stats["errors"] += 1
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
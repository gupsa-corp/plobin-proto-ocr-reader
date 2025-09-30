from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import List, Optional, Union, Dict, Any
import tempfile
import os
import json
from pathlib import Path
import asyncio
import shutil
import time
import psutil
from datetime import datetime
import re

from document_block_extractor import DocumentBlockExtractor
from pdf_to_image_processor import PDFToImageProcessor

app = FastAPI(
    title="Document OCR API",
    description="API for document text extraction and block classification using PaddleOCR",
    version="1.0.0"
)

# 서버 상태 추적 변수들
server_stats = {
    "start_time": datetime.now(),
    "total_requests": 0,
    "total_images_processed": 0,
    "total_pdfs_processed": 0,
    "total_blocks_extracted": 0,
    "total_processing_time": 0.0,
    "last_request_time": None,
    "errors": 0
}

class BlockInfo(BaseModel):
    text: str
    confidence: float
    bbox: List[List[int]]
    block_type: str

class ProcessingResult(BaseModel):
    filename: str
    total_blocks: int
    average_confidence: float
    blocks: List[BlockInfo]
    processing_time: Optional[float] = None
    output_files: Optional[dict] = None

class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None

class ServerStatus(BaseModel):
    status: str
    uptime_seconds: float
    uptime_formatted: str
    total_requests: int
    total_images_processed: int
    total_pdfs_processed: int
    total_blocks_extracted: int
    average_processing_time: float
    last_request_time: Optional[str]
    errors: int
    system_info: dict
    gpu_available: bool

class OutputFile(BaseModel):
    filename: str
    content: Dict[str, Any]
    file_info: Dict[str, Any]

class BlockDetail(BaseModel):
    block_id: int
    text: str
    confidence: float
    bbox: List[List[int]]
    block_type: str
    file_info: Dict[str, Any]

class BlockStats(BaseModel):
    total_blocks: int
    confidence_distribution: Dict[str, int]
    block_type_counts: Dict[str, int]
    average_confidence: float
    text_length_stats: Dict[str, float]

class FileStats(BaseModel):
    total_files: int
    total_size_mb: float
    by_type: Dict[str, Dict[str, Any]]
    disk_usage: Dict[str, float]

class BatchOperation(BaseModel):
    action: str
    files: List[str]

extractor = DocumentBlockExtractor(use_gpu=False)
pdf_processor = PDFToImageProcessor()

# Output 폴더 생성
output_dir = Path("output")
output_dir.mkdir(exist_ok=True)

def create_output_folder_structure(file_type: str, filename: str, page_num: int = None) -> Path:
    """계층적 폴더 구조 생성"""
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H%M%S")

    base_name = Path(filename).stem

    # 기본 경로: output/타입/날짜/파일명_시간/
    if file_type == "pdf" and page_num is not None:
        # PDF: output/pdfs/2025-09-29/filename_HHMMSS/page_N/
        folder_path = output_dir / "pdfs" / date_str / f"{base_name}_{time_str}" / f"page_{page_num}"
    elif file_type == "image":
        # 이미지: output/images/2025-09-29/filename_HHMMSS/
        folder_path = output_dir / "images" / date_str / f"{base_name}_{time_str}"
    else:
        # 기본: output/documents/2025-09-29/filename_HHMMSS/
        folder_path = output_dir / "documents" / date_str / f"{base_name}_{time_str}"

    # 폴더 생성
    folder_path.mkdir(parents=True, exist_ok=True)
    return folder_path

def create_pdf_summary(filename: str, all_pages_results: List[ProcessingResult]) -> dict:
    """PDF 전체 요약 파일 생성"""
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H%M%S")
    base_name = Path(filename).stem

    # PDF 폴더 경로: output/pdfs/2025-09-29/filename_HHMMSS/
    pdf_folder = output_dir / "pdfs" / date_str / f"{base_name}_{time_str}"
    pdf_folder.mkdir(parents=True, exist_ok=True)

    # 요약 파일 경로
    summary_path = pdf_folder / "summary.json"

    # PDF 요약 데이터 생성
    summary_data = {
        "pdf_info": {
            "filename": filename,
            "processed_at": now.isoformat(),
            "total_pages": len(all_pages_results),
            "total_blocks": sum(result.total_blocks for result in all_pages_results),
            "overall_confidence": round(sum(result.average_confidence * result.total_blocks for result in all_pages_results) /
                                      max(sum(result.total_blocks for result in all_pages_results), 1), 3) if all_pages_results else 0
        },
        "pages": [
            {
                "page_number": i + 1,
                "blocks": result.total_blocks,
                "confidence": result.average_confidence,
                "blocks_detail": [block.dict() for block in result.blocks]
            }
            for i, result in enumerate(all_pages_results)
        ]
    }

    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, ensure_ascii=False, indent=2)

    return {
        "summary_path": str(summary_path),
        "pdf_folder": str(pdf_folder),
        "relative_path": str(pdf_folder.relative_to(output_dir))
    }

def save_processing_results(filename: str, result_data: dict, blocks: list, image_path: str = None,
                          file_type: str = "document", page_num: int = None) -> dict:
    """처리 결과를 계층적 폴더 구조로 저장"""

    # 폴더 구조 생성
    folder_path = create_output_folder_structure(file_type, filename, page_num)

    # JSON 결과 저장
    json_path = folder_path / "result.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)

    output_files = {
        "json_result": str(json_path),
        "result_filename": json_path.name,
        "folder_path": str(folder_path),
        "relative_path": str(folder_path.relative_to(output_dir))
    }

    # 시각화 이미지가 있으면 저장
    if image_path and os.path.exists(image_path):
        try:
            viz_path = folder_path / "visualization.png"

            # 시각화 생성 및 저장
            extractor.visualize_blocks(image_path, {'blocks': blocks}, str(viz_path))

            output_files["visualization"] = str(viz_path)
            output_files["visualization_filename"] = viz_path.name

        except Exception as e:
            print(f"시각화 생성 실패: {e}")

    return output_files

def save_pdf_summary(filename: str, all_pages_results: list) -> dict:
    """PDF 전체 요약 정보 저장"""
    base_name = Path(filename).stem
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H%M%S")

    pdf_folder = output_dir / "pdfs" / date_str / f"{base_name}_{time_str}"
    summary_path = pdf_folder / "summary.json"

    # 전체 통계 계산
    total_blocks = sum(len(page.get('blocks', [])) for page in all_pages_results)
    total_confidence = sum(
        sum(block.get('confidence', 0) for block in page.get('blocks', []))
        for page in all_pages_results
    )
    avg_confidence = total_confidence / total_blocks if total_blocks > 0 else 0.0

    summary_data = {
        "pdf_info": {
            "filename": filename,
            "total_pages": len(all_pages_results),
            "processed_date": now.isoformat(),
            "folder_path": str(pdf_folder.relative_to(output_dir))
        },
        "statistics": {
            "total_blocks": total_blocks,
            "average_confidence": round(avg_confidence, 3),
            "pages_summary": [
                {
                    "page_number": i + 1,
                    "blocks_count": len(page.get('blocks', [])),
                    "avg_confidence": round(
                        sum(block.get('confidence', 0) for block in page.get('blocks', [])) / len(page.get('blocks', [])), 3
                    ) if page.get('blocks') else 0.0,
                    "folder_path": f"page_{i + 1}"
                }
                for i, page in enumerate(all_pages_results)
            ]
        }
    }

    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, ensure_ascii=False, indent=2)

    return {
        "summary_path": str(summary_path),
        "pdf_folder": str(pdf_folder),
        "relative_path": str(pdf_folder.relative_to(output_dir))
    }

# 파일 관리 유틸리티 함수들
def validate_filename(filename: str) -> bool:
    """파일명 보안 검증"""
    if not filename or ".." in filename or "/" in filename or "\\" in filename:
        return False
    return True

def load_json_file(filename: str) -> Dict[str, Any]:
    """JSON 파일 로드"""
    file_path = output_dir / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail=f"Invalid JSON file: {filename}")

def get_file_info(filename: str) -> Dict[str, Any]:
    """파일 정보 가져오기"""
    file_path = output_dir / filename
    if not file_path.exists():
        return {}

    stat = file_path.stat()
    return {
        "filename": filename,
        "path": str(file_path),
        "size_mb": round(stat.st_size / (1024 * 1024), 2),
        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "type": "json" if file_path.suffix == ".json" else "image" if file_path.suffix in [".png", ".jpg", ".jpeg"] else "other"
    }

def filter_blocks(blocks: List[Dict[str, Any]],
                 confidence_min: Optional[float] = None,
                 confidence_max: Optional[float] = None,
                 text_contains: Optional[str] = None,
                 block_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """블록 필터링"""
    filtered = blocks

    if confidence_min is not None:
        filtered = [b for b in filtered if b.get('confidence', 0) >= confidence_min]

    if confidence_max is not None:
        filtered = [b for b in filtered if b.get('confidence', 0) <= confidence_max]

    if text_contains:
        filtered = [b for b in filtered if text_contains.lower() in b.get('text', '').lower()]

    if block_type:
        filtered = [b for b in filtered if b.get('block_type') == block_type or b.get('type') == block_type]

    return filtered

def calculate_block_stats(blocks: List[Dict[str, Any]]) -> BlockStats:
    """블록 통계 계산"""
    if not blocks:
        return BlockStats(
            total_blocks=0,
            confidence_distribution={},
            block_type_counts={},
            average_confidence=0.0,
            text_length_stats={}
        )

    # 신뢰도 분포 계산 (0.1 단위)
    conf_dist = {}
    for block in blocks:
        conf = block.get('confidence', 0)
        key = f"{int(conf * 10) / 10:.1f}-{int(conf * 10) / 10 + 0.1:.1f}"
        conf_dist[key] = conf_dist.get(key, 0) + 1

    # 블록 타입별 개수
    type_counts = {}
    for block in blocks:
        block_type = block.get('block_type') or block.get('type', 'unknown')
        type_counts[block_type] = type_counts.get(block_type, 0) + 1

    # 텍스트 길이 통계
    text_lengths = [len(block.get('text', '')) for block in blocks]
    text_stats = {
        'min': min(text_lengths) if text_lengths else 0,
        'max': max(text_lengths) if text_lengths else 0,
        'average': sum(text_lengths) / len(text_lengths) if text_lengths else 0
    }

    # 평균 신뢰도
    avg_conf = sum(block.get('confidence', 0) for block in blocks) / len(blocks)

    return BlockStats(
        total_blocks=len(blocks),
        confidence_distribution=conf_dist,
        block_type_counts=type_counts,
        average_confidence=round(avg_conf, 3),
        text_length_stats=text_stats
    )

def find_blocks_by_position(blocks: List[Dict[str, Any]], x: int, y: int, tolerance: int = 10) -> List[Dict[str, Any]]:
    """좌표 기반 블록 찾기"""
    found_blocks = []

    for i, block in enumerate(blocks):
        bbox = block.get('bbox_points') or block.get('bbox', [])
        if not bbox or len(bbox) != 4:
            continue

        # 바운딩 박스 영역 확인
        x_coords = [point[0] for point in bbox]
        y_coords = [point[1] for point in bbox]

        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)

        # 허용 오차 포함하여 영역 안에 있는지 확인
        if (min_x - tolerance <= x <= max_x + tolerance and
            min_y - tolerance <= y <= max_y + tolerance):
            block_copy = block.copy()
            block_copy['block_id'] = i
            found_blocks.append(block_copy)

    return found_blocks

@app.get("/")
async def root():
    return {"message": "Document OCR API", "version": "1.0.0", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "gpu_available": extractor.use_gpu}

@app.get("/status", response_model=ServerStatus)
async def get_server_status():
    """서버 상태 및 처리 통계 정보"""
    now = datetime.now()
    uptime = (now - server_stats["start_time"]).total_seconds()

    # 시스템 정보
    memory = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=0.1)

    # 평균 처리 시간 계산
    avg_processing_time = (
        server_stats["total_processing_time"] / server_stats["total_requests"]
        if server_stats["total_requests"] > 0 else 0.0
    )

    def format_uptime(seconds):
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if days > 0:
            return f"{days}d {hours}h {minutes}m {secs}s"
        elif hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"

    return ServerStatus(
        status="running",
        uptime_seconds=uptime,
        uptime_formatted=format_uptime(uptime),
        total_requests=server_stats["total_requests"],
        total_images_processed=server_stats["total_images_processed"],
        total_pdfs_processed=server_stats["total_pdfs_processed"],
        total_blocks_extracted=server_stats["total_blocks_extracted"],
        average_processing_time=round(avg_processing_time, 3),
        last_request_time=server_stats["last_request_time"].isoformat() if server_stats["last_request_time"] else None,
        errors=server_stats["errors"],
        system_info={
            "cpu_percent": cpu_percent,
            "memory_used_mb": round(memory.used / 1024 / 1024, 1),
            "memory_total_mb": round(memory.total / 1024 / 1024, 1),
            "memory_percent": memory.percent,
            "pid": os.getpid()
        },
        gpu_available=extractor.use_gpu
    )

@app.post("/process-image", response_model=ProcessingResult)
async def process_image(file: UploadFile = File(...)):
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
            result = extractor.extract_blocks(tmp_path)
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

@app.post("/process-pdf", response_model=List[ProcessingResult])
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

@app.post("/process-document")
async def process_document(file: UploadFile = File(...)):
    content_type = file.content_type or ""

    if content_type.startswith('image/'):
        return await process_image(file)
    elif content_type == 'application/pdf':
        return await process_pdf(file)
    else:
        raise HTTPException(
            status_code=400,
            detail="File must be an image (JPEG, PNG, etc.) or PDF"
        )

@app.get("/supported-formats")
async def get_supported_formats():
    return {
        "image_formats": ["JPEG", "PNG", "BMP", "TIFF", "WEBP"],
        "document_formats": ["PDF"],
        "max_file_size": "10MB (configurable)"
    }

@app.get("/output/list")
async def list_output_files():
    """Output 폴더의 처리 결과 파일 목록 조회 (계층적 + 기존 구조)"""
    try:
        files = []

        # 1. 기존 평면 파일들 (호환성)
        for file_path in output_dir.glob("*"):
            if file_path.is_file():
                stat = file_path.stat()
                files.append({
                    "filename": file_path.name,
                    "path": str(file_path),
                    "relative_path": file_path.name,
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "type": "json" if file_path.suffix == ".json" else "image" if file_path.suffix in [".png", ".jpg", ".jpeg"] else "other",
                    "structure": "legacy"
                })

        # 2. 새로운 계층적 구조의 파일들
        for category in ["pdfs", "images", "documents"]:
            category_path = output_dir / category
            if category_path.exists():
                for file_path in category_path.rglob("*"):
                    if file_path.is_file():
                        stat = file_path.stat()
                        relative_path = file_path.relative_to(output_dir)
                        files.append({
                            "filename": file_path.name,
                            "path": str(file_path),
                            "relative_path": str(relative_path),
                            "size_mb": round(stat.st_size / (1024 * 1024), 2),
                            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            "type": "json" if file_path.suffix == ".json" else "image" if file_path.suffix in [".png", ".jpg", ".jpeg"] else "other",
                            "structure": "hierarchical",
                            "category": category
                        })

        # 최신 파일 순으로 정렬
        files.sort(key=lambda x: x["created"], reverse=True)

        return {
            "total_files": len(files),
            "files": files,
            "output_directory": str(output_dir),
            "structure_info": {
                "legacy_files": len([f for f in files if f.get("structure") == "legacy"]),
                "hierarchical_files": len([f for f in files if f.get("structure") == "hierarchical"])
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list output files: {str(e)}")

@app.get("/output/stats", response_model=FileStats)
async def get_output_stats():
    """출력 폴더 통계 (계층적 + 기존 구조)"""
    try:
        all_files = []

        # 1. 기존 평면 파일들
        legacy_files = list(output_dir.glob("*"))
        legacy_file_files = [f for f in legacy_files if f.is_file()]
        all_files.extend(legacy_file_files)

        # 2. 새로운 계층적 구조의 파일들
        for category in ["pdfs", "images", "documents"]:
            category_path = output_dir / category
            if category_path.exists():
                for file_path in category_path.rglob("*"):
                    if file_path.is_file():
                        all_files.append(file_path)

        # 전체 크기 계산
        total_size = sum(f.stat().st_size for f in all_files)

        # 타입별 분류
        by_type = {}
        for file_path in all_files:
            file_type = "json" if file_path.suffix == ".json" else "image" if file_path.suffix in [".png", ".jpg", ".jpeg"] else "other"
            size_mb = round(file_path.stat().st_size / (1024 * 1024), 2)

            if file_type not in by_type:
                by_type[file_type] = {"count": 0, "size_mb": 0}

            by_type[file_type]["count"] += 1
            by_type[file_type]["size_mb"] += size_mb

        # 디스크 사용량 (시스템 전체)
        disk_usage = psutil.disk_usage('/')

        return FileStats(
            total_files=len(all_files),
            total_size_mb=round(total_size / (1024 * 1024), 2),
            by_type=by_type,
            disk_usage={
                "total_gb": round(disk_usage.total / (1024**3), 1),
                "used_gb": round(disk_usage.used / (1024**3), 1),
                "free_gb": round(disk_usage.free / (1024**3), 1),
                "percent": disk_usage.percent
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@app.get("/output/search")
async def search_output_files(
    query: Optional[str] = Query(None),
    file_type: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None)
):
    """출력 파일 검색"""
    try:
        files = []
        for file_path in output_dir.glob("*"):
            if not file_path.is_file():
                continue

            file_info = get_file_info(file_path.name)

            # 쿼리 필터링
            if query and query.lower() not in file_path.name.lower():
                continue

            # 타입 필터링
            if file_type and file_info["type"] != file_type:
                continue

            # 날짜 필터링
            if date_from:
                file_date = datetime.fromisoformat(file_info["created"].replace('Z', '+00:00'))
                if file_date < datetime.fromisoformat(date_from):
                    continue

            if date_to:
                file_date = datetime.fromisoformat(file_info["created"].replace('Z', '+00:00'))
                if file_date > datetime.fromisoformat(date_to):
                    continue

            files.append(file_info)

        # 최신 파일 순으로 정렬
        files.sort(key=lambda x: x["created"], reverse=True)

        return {
            "total_found": len(files),
            "search_params": {
                "query": query,
                "file_type": file_type,
                "date_from": date_from,
                "date_to": date_to
            },
            "files": files
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.post("/output/batch")
async def batch_output_operation(operation: BatchOperation):
    """배치 파일 작업"""
    if operation.action not in ["delete", "info"]:
        raise HTTPException(status_code=400, detail="Supported actions: delete, info")

    results = []

    for filename in operation.files:
        if not validate_filename(filename):
            results.append({"filename": filename, "status": "error", "message": "Invalid filename"})
            continue

        file_path = output_dir / filename
        if not file_path.exists():
            results.append({"filename": filename, "status": "error", "message": "File not found"})
            continue

        try:
            if operation.action == "delete":
                file_path.unlink()
                results.append({"filename": filename, "status": "success", "message": "Deleted"})

            elif operation.action == "info":
                file_info = get_file_info(filename)
                results.append({"filename": filename, "status": "success", "info": file_info})

        except Exception as e:
            results.append({"filename": filename, "status": "error", "message": str(e)})

    return {
        "action": operation.action,
        "total_files": len(operation.files),
        "results": results
    }

@app.get("/output/{filename}", response_model=OutputFile)
async def get_output_file(filename: str):
    """개별 출력 파일 내용 조회"""
    if not validate_filename(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")

    if not filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Only JSON files are supported")

    content = load_json_file(filename)
    file_info = get_file_info(filename)

    return OutputFile(
        filename=filename,
        content=content,
        file_info=file_info
    )

@app.get("/output/download/{filename}")
async def download_output_file(filename: str):
    """파일 다운로드"""
    if not validate_filename(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")

    file_path = output_dir / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type='application/octet-stream'
    )

@app.delete("/output/{filename}")
async def delete_output_file(filename: str, include_related: bool = Query(True)):
    """출력 파일 삭제"""
    if not validate_filename(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")

    file_path = output_dir / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")

    deleted_files = []

    try:
        # 메인 파일 삭제
        file_path.unlink()
        deleted_files.append(filename)

        # 관련 파일들도 삭제 (JSON-시각화 쌍)
        if include_related:
            base_name = filename.replace('_result.json', '').replace('_visualization.png', '')

            for related_file in output_dir.glob(f"{base_name}*"):
                if related_file.name != filename and related_file.is_file():
                    related_file.unlink()
                    deleted_files.append(related_file.name)

        return {
            "message": f"Successfully deleted {len(deleted_files)} file(s)",
            "deleted_files": deleted_files
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

@app.get("/output/search")
async def search_output_files(
    query: Optional[str] = Query(None),
    file_type: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None)
):
    """출력 파일 검색"""
    try:
        files = []
        for file_path in output_dir.glob("*"):
            if not file_path.is_file():
                continue

            file_info = get_file_info(file_path.name)

            # 쿼리 필터링
            if query and query.lower() not in file_path.name.lower():
                continue

            # 타입 필터링
            if file_type and file_info["type"] != file_type:
                continue

            # 날짜 필터링
            if date_from:
                file_date = datetime.fromisoformat(file_info["created"].replace('Z', '+00:00'))
                if file_date < datetime.fromisoformat(date_from):
                    continue

            if date_to:
                file_date = datetime.fromisoformat(file_info["created"].replace('Z', '+00:00'))
                if file_date > datetime.fromisoformat(date_to):
                    continue

            files.append(file_info)

        # 최신 파일 순으로 정렬
        files.sort(key=lambda x: x["created"], reverse=True)

        return {
            "total_found": len(files),
            "search_params": {
                "query": query,
                "file_type": file_type,
                "date_from": date_from,
                "date_to": date_to
            },
            "files": files
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.post("/output/batch")
async def batch_output_operation(operation: BatchOperation):
    """배치 파일 작업"""
    if operation.action not in ["delete", "info"]:
        raise HTTPException(status_code=400, detail="Supported actions: delete, info")

    results = []

    for filename in operation.files:
        if not validate_filename(filename):
            results.append({"filename": filename, "status": "error", "message": "Invalid filename"})
            continue

        file_path = output_dir / filename
        if not file_path.exists():
            results.append({"filename": filename, "status": "error", "message": "File not found"})
            continue

        try:
            if operation.action == "delete":
                file_path.unlink()
                results.append({"filename": filename, "status": "success", "message": "Deleted"})

            elif operation.action == "info":
                file_info = get_file_info(filename)
                results.append({"filename": filename, "status": "success", "info": file_info})

        except Exception as e:
            results.append({"filename": filename, "status": "error", "message": str(e)})

    return {
        "action": operation.action,
        "total_files": len(operation.files),
        "results": results
    }

# 블록 관련 API들
@app.get("/output/{filename}/blocks/stats", response_model=BlockStats)
async def get_block_stats(filename: str):
    """블록 통계"""
    if not validate_filename(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")

    if not filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Only JSON files are supported")

    content = load_json_file(filename)
    blocks = content.get('blocks', [])

    return calculate_block_stats(blocks)

@app.get("/output/{filename}/blocks/by_position")
async def get_blocks_by_position(
    filename: str,
    x: int = Query(...),
    y: int = Query(...),
    tolerance: int = Query(10)
):
    """좌표 기반 블록 찾기"""
    if not validate_filename(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")

    if not filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Only JSON files are supported")

    content = load_json_file(filename)
    blocks = content.get('blocks', [])

    found_blocks = find_blocks_by_position(blocks, x, y, tolerance)

    return {
        "filename": filename,
        "search_position": {"x": x, "y": y, "tolerance": tolerance},
        "found_blocks": len(found_blocks),
        "blocks": found_blocks
    }

@app.get("/output/{filename}/blocks/{block_id}", response_model=BlockDetail)
async def get_block_by_id(filename: str, block_id: int):
    """특정 블록 조회"""
    if not validate_filename(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")

    if not filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Only JSON files are supported")

    content = load_json_file(filename)
    blocks = content.get('blocks', [])

    if block_id < 0 or block_id >= len(blocks):
        raise HTTPException(status_code=404, detail=f"Block {block_id} not found")

    block = blocks[block_id]

    return BlockDetail(
        block_id=block_id,
        text=block.get('text', ''),
        confidence=block.get('confidence', 0.0),
        bbox=block.get('bbox_points', block.get('bbox', [])),
        block_type=block.get('block_type', block.get('type', 'unknown')),
        file_info={"filename": filename, "total_blocks": len(blocks)}
    )

@app.get("/output/{filename}/blocks")
async def get_filtered_blocks(
    filename: str,
    confidence_min: Optional[float] = Query(None),
    confidence_max: Optional[float] = Query(None),
    text_contains: Optional[str] = Query(None),
    block_type: Optional[str] = Query(None),
    start: Optional[int] = Query(None),
    end: Optional[int] = Query(None)
):
    """블록 필터링 및 범위 조회"""
    if not validate_filename(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")

    if not filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Only JSON files are supported")

    content = load_json_file(filename)
    blocks = content.get('blocks', [])

    # 필터링 적용
    filtered_blocks = filter_blocks(
        blocks,
        confidence_min=confidence_min,
        confidence_max=confidence_max,
        text_contains=text_contains,
        block_type=block_type
    )

    # 범위 조회 적용
    if start is not None or end is not None:
        start_idx = max(0, start or 0)
        end_idx = min(len(filtered_blocks), end or len(filtered_blocks))
        range_blocks = filtered_blocks[start_idx:end_idx]
    else:
        range_blocks = filtered_blocks
        start_idx = 0
        end_idx = len(filtered_blocks)

    return {
        "filename": filename,
        "total_blocks": len(blocks),
        "filtered_blocks": len(filtered_blocks),
        "returned_blocks": len(range_blocks),
        "filters": {
            "confidence_min": confidence_min,
            "confidence_max": confidence_max,
            "text_contains": text_contains,
            "block_type": block_type
        },
        "pagination": {
            "start": start_idx,
            "end": end_idx,
            "has_next": end_idx < len(filtered_blocks)
        },
        "blocks": range_blocks
    }

@app.get("/output/{filename}/blocks/stats", response_model=BlockStats)
async def get_block_stats(filename: str):
    """블록 통계"""
    if not validate_filename(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")

    if not filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Only JSON files are supported")

    content = load_json_file(filename)
    blocks = content.get('blocks', [])

    return calculate_block_stats(blocks)

@app.get("/output/{filename}/blocks/by_position")
async def get_blocks_by_position(
    filename: str,
    x: int = Query(...),
    y: int = Query(...),
    tolerance: int = Query(10)
):
    """좌표 기반 블록 찾기"""
    if not validate_filename(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")

    if not filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Only JSON files are supported")

    content = load_json_file(filename)
    blocks = content.get('blocks', [])

    found_blocks = find_blocks_by_position(blocks, x, y, tolerance)

    return {
        "filename": filename,
        "search_position": {"x": x, "y": y, "tolerance": tolerance},
        "found_blocks": len(found_blocks),
        "blocks": found_blocks
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6003)
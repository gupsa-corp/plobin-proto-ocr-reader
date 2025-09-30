from fastapi import APIRouter
from api.models.schemas import ServerStatus
import psutil
from datetime import datetime

router = APIRouter()

# Global stats that will be injected
server_stats = None

def set_server_stats(stats):
    global server_stats
    server_stats = stats

@router.get("/")
async def root():
    return {"message": "Document OCR API", "version": "1.0.0", "port": 6003}

@router.get("/health")
async def health_check():
    return {"status": "healthy", "gpu_available": False, "cpu_count": psutil.cpu_count()}

@router.get("/status", response_model=ServerStatus)
async def get_server_status():
    """서버 상태 및 처리 통계"""
    now = datetime.now()
    uptime = now - server_stats["start_time"]
    uptime_seconds = uptime.total_seconds()

    # 업타임을 시:분:초 형식으로 변환
    hours = int(uptime_seconds // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    seconds = int(uptime_seconds % 60)
    uptime_formatted = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    # 평균 처리 시간 계산
    total_processed = server_stats["total_images_processed"] + server_stats["total_pdfs_processed"]
    avg_processing_time = (server_stats["total_processing_time"] / total_processed) if total_processed > 0 else 0.0

    return ServerStatus(
        status="running",
        uptime_seconds=uptime_seconds,
        uptime_formatted=uptime_formatted,
        total_requests=server_stats["total_requests"],
        total_images_processed=server_stats["total_images_processed"],
        total_pdfs_processed=server_stats["total_pdfs_processed"],
        total_blocks_extracted=server_stats["total_blocks_extracted"],
        average_processing_time=round(avg_processing_time, 3),
        last_request_time=server_stats["last_request_time"].isoformat() if server_stats["last_request_time"] else None,
        errors=server_stats["errors"],
        gpu_available=False
    )

@router.get("/supported-formats")
async def get_supported_formats():
    return {
        "image_formats": ["JPEG", "PNG", "BMP", "TIFF", "WEBP"],
        "document_formats": ["PDF"],
        "max_file_size": "10MB (configurable)"
    }
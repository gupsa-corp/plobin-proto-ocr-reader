from fastapi import APIRouter, HTTPException
import psutil

from api.models.schemas import FileStats

router = APIRouter()

# Global dependencies that will be injected
output_dir = None

def set_dependencies(out_dir):
    global output_dir
    output_dir = out_dir

@router.get("/output/stats", response_model=FileStats)
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
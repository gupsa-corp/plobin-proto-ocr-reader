from fastapi import APIRouter, HTTPException
from datetime import datetime

router = APIRouter()

# Global dependencies that will be injected
output_dir = None

def set_dependencies(out_dir):
    global output_dir
    output_dir = out_dir

@router.get("/output/list")
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
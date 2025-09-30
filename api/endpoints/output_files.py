from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from typing import Optional, List
import re

from api.models.schemas import OutputFile, BlockDetail, BlockStats, BatchOperation
from api.utils.file_storage import validate_filename, load_json_file, get_file_info
from api.utils.block_processing import filter_blocks, calculate_block_stats, find_blocks_by_position

router = APIRouter()

# Global dependencies that will be injected
output_dir = None

def set_dependencies(out_dir):
    global output_dir
    output_dir = out_dir

@router.get("/output/search")
async def search_output_files(
    query: Optional[str] = Query(None, description="검색어"),
    file_type: Optional[str] = Query(None, description="파일 타입 (json, image, other)"),
    date_from: Optional[str] = Query(None, description="시작 날짜 (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="종료 날짜 (YYYY-MM-DD)"),
    limit: Optional[int] = Query(50, description="결과 개수 제한")
):
    """파일 검색"""
    try:
        files = []

        # 모든 파일 수집
        for file_path in output_dir.glob("*"):
            if file_path.is_file():
                files.append(file_path)

        # 계층적 구조의 파일들도 포함
        for category in ["pdfs", "images", "documents"]:
            category_path = output_dir / category
            if category_path.exists():
                for file_path in category_path.rglob("*"):
                    if file_path.is_file():
                        files.append(file_path)

        # 필터링
        filtered_files = []
        for file_path in files:
            file_info = get_file_info(file_path.name) or {"created": "", "type": ""}

            # 쿼리 필터
            if query and query.lower() not in file_path.name.lower():
                continue

            # 타입 필터
            if file_type and file_info.get("type") != file_type:
                continue

            # 날짜 필터 (간단한 문자열 비교)
            if date_from and file_info.get("created", "") < date_from:
                continue
            if date_to and file_info.get("created", "") > date_to + "T23:59:59":
                continue

            filtered_files.append({
                "filename": file_path.name,
                "path": str(file_path),
                "relative_path": str(file_path.relative_to(output_dir)) if file_path.is_relative_to(output_dir) else file_path.name,
                **file_info
            })

        # 제한
        if limit:
            filtered_files = filtered_files[:limit]

        return {
            "total_found": len(filtered_files),
            "files": filtered_files,
            "search_criteria": {
                "query": query,
                "file_type": file_type,
                "date_from": date_from,
                "date_to": date_to,
                "limit": limit
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/output/{filename}", response_model=OutputFile)
async def get_output_file(filename: str):
    """개별 파일 내용 조회"""
    if not validate_filename(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")

    try:
        content = load_json_file(filename)
        file_info = get_file_info(filename)

        return OutputFile(
            filename=filename,
            content=content,
            file_info=file_info
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load file: {str(e)}")

@router.get("/output/download/{filename}")
async def download_output_file(filename: str):
    """파일 다운로드"""
    if not validate_filename(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")

    file_path = output_dir / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type='application/octet-stream'
    )

@router.delete("/output/{filename}")
async def delete_output_file(filename: str):
    """파일 삭제"""
    if not validate_filename(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")

    file_path = output_dir / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    try:
        file_path.unlink()

        # 관련 시각화 파일도 삭제 시도
        if filename.endswith('_result.json'):
            viz_filename = filename.replace('_result.json', '_visualization.png')
            viz_path = output_dir / viz_filename
            if viz_path.exists():
                viz_path.unlink()

        return {"message": f"File {filename} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

@router.post("/output/batch")
async def batch_file_operations(operation: BatchOperation):
    """배치 파일 작업"""
    if operation.action not in ["delete", "info"]:
        raise HTTPException(status_code=400, detail="Unsupported action")

    results = []
    for filename in operation.files:
        if not validate_filename(filename):
            results.append({"filename": filename, "status": "error", "message": "Invalid filename"})
            continue

        try:
            if operation.action == "delete":
                file_path = output_dir / filename
                if file_path.exists():
                    file_path.unlink()
                    results.append({"filename": filename, "status": "deleted"})
                else:
                    results.append({"filename": filename, "status": "not_found"})
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
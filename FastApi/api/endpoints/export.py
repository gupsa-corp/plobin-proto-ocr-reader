from fastapi import APIRouter, HTTPException
from pathlib import Path
import json

router = APIRouter()

# Dependencies (will be set by main server)
_output_dir = None

def set_dependencies(output_dir: str):
    """Set dependencies from main server"""
    global _output_dir
    _output_dir = output_dir

@router.get("/export/{request_id}")
async def export_request_data(request_id: str):
    """
    특정 request_id의 모든 데이터를 Laravel로 export

    Args:
        request_id: FastAPI에서 생성된 요청 ID

    Returns:
        완전한 OCR 결과 데이터 (metadata, summary, pages)

    Raises:
        HTTPException: request_id가 존재하지 않거나 처리되지 않은 경우
    """
    if _output_dir is None:
        raise HTTPException(status_code=500, detail="Output directory not configured")

    # output 디렉토리 경로
    output_dir = Path(_output_dir) / request_id

    if not output_dir.exists():
        raise HTTPException(status_code=404, detail=f"Request ID not found: {request_id}")

    # metadata.json 확인
    metadata_file = output_dir / "metadata.json"
    if not metadata_file.exists():
        raise HTTPException(status_code=404, detail="Metadata file not found")

    # metadata.json 읽기
    metadata = json.loads(metadata_file.read_text(encoding='utf-8'))

    # summary.json 읽기
    summary_file = output_dir / "summary.json"
    summary = json.loads(summary_file.read_text(encoding='utf-8')) if summary_file.exists() else {}

    # 모든 페이지 데이터 수집
    pages_data = []
    pages_dir = output_dir / "pages"

    if pages_dir.exists():
        for page_dir in sorted(pages_dir.iterdir()):
            if page_dir.is_dir():
                try:
                    page_info_file = page_dir / "page_info.json"
                    result_file = page_dir / "result.json"
                    content_summary_file = page_dir / "content_summary.json"

                    page_info = json.loads(page_info_file.read_text(encoding='utf-8')) if page_info_file.exists() else {}
                    result = json.loads(result_file.read_text(encoding='utf-8')) if result_file.exists() else {}
                    content_summary = json.loads(content_summary_file.read_text(encoding='utf-8')) if content_summary_file.exists() else {}

                    pages_data.append({
                        "page_number": page_info.get("page_number", 0),
                        "page_info": page_info,
                        "ocr_result": result,
                        "content_summary": content_summary
                    })
                except Exception as e:
                    # 개별 페이지 읽기 실패는 경고만 하고 계속 진행
                    print(f"Warning: Failed to read page {page_dir.name}: {str(e)}")
                    continue

    return {
        "request_id": request_id,
        "metadata": metadata,
        "summary": summary,
        "pages": pages_data,
        "total_pages": len(pages_data)
    }

@router.get("/export/list/completed")
async def list_completed_requests():
    """
    완료된 모든 request 목록 반환

    Returns:
        완료 상태의 모든 요청 목록
    """
    if _output_dir is None:
        raise HTTPException(status_code=500, detail="Output directory not configured")

    output_dir = Path(_output_dir)
    requests = []

    if not output_dir.exists():
        return {"requests": []}

    for req_dir in output_dir.iterdir():
        if req_dir.is_dir():
            metadata_file = req_dir / "metadata.json"
            if metadata_file.exists():
                try:
                    metadata = json.loads(metadata_file.read_text(encoding='utf-8'))
                    if metadata.get("processing_status") == "completed":
                        requests.append({
                            "request_id": metadata["request_id"],
                            "original_filename": metadata.get("original_filename", "unknown"),
                            "completed_at": metadata.get("completed_at"),
                            "total_pages": metadata.get("total_pages", 0),
                            "file_type": metadata.get("file_type", "unknown")
                        })
                except Exception as e:
                    # 개별 요청 읽기 실패는 무시하고 계속 진행
                    print(f"Warning: Failed to read request {req_dir.name}: {str(e)}")
                    continue

    # completed_at 기준 내림차순 정렬 (최신 순)
    requests.sort(key=lambda x: x.get("completed_at", ""), reverse=True)

    return {
        "total": len(requests),
        "requests": requests
    }

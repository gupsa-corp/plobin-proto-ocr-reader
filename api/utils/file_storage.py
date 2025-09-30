import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from fastapi import HTTPException

from api.models.schemas import ProcessingResult

# Global references that will be injected
output_dir = None
extractor = None

def set_global_dependencies(out_dir: Path, doc_extractor):
    """Set global dependencies for the utility functions"""
    global output_dir, extractor
    output_dir = out_dir
    extractor = doc_extractor

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
    import os

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
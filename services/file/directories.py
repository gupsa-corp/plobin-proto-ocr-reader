#!/usr/bin/env python3
"""
Create directory structures for OCR output
"""

from pathlib import Path
from typing import Dict, List
from .request_manager import validate_request_id


def create_directories(base_output_dir, create_subdirs=True):
    """
    OCR 출력을 위한 디렉토리 구조 생성 (레거시 지원)

    Args:
        base_output_dir: 기본 출력 디렉토리
        create_subdirs: 하위 디렉토리 생성 여부

    Returns:
        생성된 디렉토리 경로들의 딕셔너리
    """
    base_path = Path(base_output_dir)
    base_path.mkdir(parents=True, exist_ok=True)

    directories = {
        'base': str(base_path)
    }

    if create_subdirs:
        # 하위 디렉토리 생성
        subdirs = ['images', 'results', 'visualizations']

        for subdir in subdirs:
            subdir_path = base_path / subdir
            subdir_path.mkdir(exist_ok=True)
            directories[subdir] = str(subdir_path)

    return directories


def create_request_directory(base_output_dir: str, request_id: str) -> Path:
    """
    요청별 디렉토리 생성

    Args:
        base_output_dir: 기본 출력 디렉토리
        request_id: 요청 ID (UUID)

    Returns:
        생성된 요청 디렉토리 경로

    Raises:
        ValueError: 유효하지 않은 요청 ID
    """
    if not validate_request_id(request_id):
        raise ValueError(f"유효하지 않은 요청 ID: {request_id}")

    base_path = Path(base_output_dir)
    request_path = base_path / request_id

    request_path.mkdir(parents=True, exist_ok=True)
    return request_path


def create_page_directory(request_dir: Path, page_number: int) -> Dict[str, Path]:
    """
    페이지별 디렉토리 구조 생성

    Args:
        request_dir: 요청 디렉토리 경로
        page_number: 페이지 번호

    Returns:
        페이지 관련 경로들의 딕셔너리
    """
    page_dir = request_dir / f"page_{page_number:03d}"
    blocks_dir = page_dir / "blocks"

    # 디렉토리 생성
    page_dir.mkdir(exist_ok=True)
    blocks_dir.mkdir(exist_ok=True)

    return {
        'page_dir': page_dir,
        'blocks_dir': blocks_dir
    }


def list_request_directories(base_output_dir: str) -> List[str]:
    """
    모든 요청 디렉토리 나열

    Args:
        base_output_dir: 기본 출력 디렉토리

    Returns:
        요청 ID 리스트 (시간순 정렬)
    """
    base_path = Path(base_output_dir)
    if not base_path.exists():
        return []

    request_ids = []
    for item in base_path.iterdir():
        if item.is_dir() and validate_request_id(item.name):
            request_ids.append(item.name)

    # UUID가 시간 기반이므로 자연 정렬이 시간순 정렬
    return sorted(request_ids)


def list_page_directories(base_output_dir: str, request_id: str) -> List[int]:
    """
    요청의 페이지 디렉토리 나열

    Args:
        base_output_dir: 기본 출력 디렉토리
        request_id: 요청 ID

    Returns:
        페이지 번호 리스트
    """
    request_path = Path(base_output_dir) / request_id
    if not request_path.exists():
        return []

    # pages 하위 디렉토리에서 3자리 숫자 디렉토리 찾기
    pages_path = request_path / "pages"
    if not pages_path.exists():
        return []

    page_numbers = []
    for item in pages_path.iterdir():
        if item.is_dir() and item.name.isdigit() and len(item.name) == 3:
            try:
                page_num = int(item.name)
                page_numbers.append(page_num)
            except ValueError:
                continue

    return sorted(page_numbers)


def cleanup_empty_directories(base_output_dir: str) -> int:
    """
    빈 디렉토리 정리

    Args:
        base_output_dir: 기본 출력 디렉토리

    Returns:
        정리된 디렉토리 수
    """
    base_path = Path(base_output_dir)
    if not base_path.exists():
        return 0

    cleaned_count = 0
    for request_dir in base_path.iterdir():
        if not request_dir.is_dir() or not validate_request_id(request_dir.name):
            continue

        # 페이지 디렉토리 정리
        for page_dir in request_dir.iterdir():
            if page_dir.is_dir() and page_dir.name.startswith('page_'):
                # 블록 디렉토리가 비어있으면 제거
                blocks_dir = page_dir / 'blocks'
                if blocks_dir.exists() and not any(blocks_dir.iterdir()):
                    blocks_dir.rmdir()
                    cleaned_count += 1

                # 페이지 디렉토리가 비어있으면 제거
                if not any(page_dir.iterdir()):
                    page_dir.rmdir()
                    cleaned_count += 1

        # 요청 디렉토리가 비어있으면 제거
        if not any(request_dir.iterdir()):
            request_dir.rmdir()
            cleaned_count += 1

    return cleaned_count


__all__ = [
    'create_directories',
    'create_request_directory',
    'create_page_directory',
    'list_request_directories',
    'list_page_directories',
    'cleanup_empty_directories'
]
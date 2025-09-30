#!/usr/bin/env python3
"""
Request management services for OCR processing
"""

import uuid
import time
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


def generate_time_based_uuid():
    """
    시간 기반 UUID 생성 (UUID v7 유사)

    Returns:
        시간 순서를 보장하는 UUID 문자열
    """
    # 현재 시간을 밀리초 단위로 가져오기
    timestamp = int(time.time() * 1000)

    # UUID v4를 생성하고 첫 8자리를 타임스탬프로 교체
    base_uuid = uuid.uuid4()
    uuid_hex = base_uuid.hex

    # 타임스탬프를 16진수로 변환 (8자리)
    timestamp_hex = f"{timestamp:012x}"[-12:]  # 12자리로 제한

    # UUID 형식으로 조합
    time_uuid = f"{timestamp_hex[:8]}-{timestamp_hex[8:]}-{uuid_hex[12:16]}-{uuid_hex[16:20]}-{uuid_hex[20:]}"

    return time_uuid


def generate_request_id():
    """
    요청 ID 생성

    Returns:
        고유한 요청 ID (시간 기반 UUID)
    """
    return generate_time_based_uuid()


def validate_request_id(request_id: str) -> bool:
    """
    요청 ID 유효성 검증

    Args:
        request_id: 검증할 요청 ID

    Returns:
        유효하면 True, 아니면 False
    """
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    return bool(uuid_pattern.match(request_id))


def create_request_structure(base_output_dir: str, request_id: str) -> Dict[str, Path]:
    """
    요청별 디렉토리 구조 생성

    Args:
        base_output_dir: 기본 출력 디렉토리
        request_id: 요청 ID

    Returns:
        생성된 경로들의 딕셔너리
    """
    base_path = Path(base_output_dir)
    request_path = base_path / request_id

    # 기본 요청 디렉토리 생성
    request_path.mkdir(parents=True, exist_ok=True)

    paths = {
        'request_dir': request_path,
        'metadata_file': request_path / 'metadata.json',
        'summary_file': request_path / 'summary.json'
    }

    return paths


def create_page_structure(request_dir: Path, page_number: int) -> Dict[str, Path]:
    """
    페이지별 디렉토리 구조 생성

    Args:
        request_dir: 요청 디렉토리 경로
        page_number: 페이지 번호

    Returns:
        페이지 관련 경로들의 딕셔너리
    """
    pages_dir = request_dir / "pages"
    page_dir = pages_dir / f"{page_number:03d}"
    blocks_dir = page_dir / "blocks"

    # 디렉토리 생성
    pages_dir.mkdir(exist_ok=True)
    page_dir.mkdir(exist_ok=True)
    blocks_dir.mkdir(exist_ok=True)

    paths = {
        'pages_dir': pages_dir,
        'page_dir': page_dir,
        'blocks_dir': blocks_dir,
        'page_info_file': page_dir / 'page_info.json',
        'result_file': page_dir / 'result.json',
        'visualization_file': page_dir / 'visualization.png'
    }

    return paths


def create_block_file_path(blocks_dir: Path, block_id: int) -> Path:
    """
    블록 파일 경로 생성

    Args:
        blocks_dir: 블록 디렉토리 경로
        block_id: 블록 ID

    Returns:
        블록 파일 경로
    """
    return blocks_dir / f"block_{block_id:03d}.json"


def extract_timestamp_from_uuid(request_id: str) -> Optional[datetime]:
    """
    시간 기반 UUID에서 타임스탬프 추출

    Args:
        request_id: 요청 ID

    Returns:
        추출된 datetime 객체 또는 None
    """
    try:
        # UUID의 첫 12자리에서 타임스탬프 추출
        timestamp_hex = request_id.replace('-', '')[:12]
        timestamp_ms = int(timestamp_hex, 16)
        return datetime.fromtimestamp(timestamp_ms / 1000)
    except (ValueError, IndexError):
        return None


def generate_request_metadata(original_filename: str, file_type: str,
                             file_size: int, total_pages: int = 1) -> Dict[str, Any]:
    """
    요청 메타데이터 생성

    Args:
        original_filename: 원본 파일명
        file_type: 파일 타입
        file_size: 파일 크기
        total_pages: 총 페이지 수

    Returns:
        메타데이터 딕셔너리
    """
    request_id = generate_request_id()
    timestamp = datetime.now()

    return {
        'request_id': request_id,
        'original_filename': original_filename,
        'timestamp': timestamp.strftime('%Y%m%d_%H%M%S'),
        'created_at': timestamp.isoformat(),
        'file_type': file_type,
        'file_size': file_size,
        'total_pages': total_pages,
        'processing_status': 'pending',
        'version': '1.0'
    }


__all__ = [
    'generate_request_id',
    'validate_request_id',
    'create_request_structure',
    'create_page_structure',
    'create_block_file_path',
    'extract_timestamp_from_uuid',
    'generate_request_metadata'
]
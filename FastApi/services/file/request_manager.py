#!/usr/bin/env python3
"""
Request management services for OCR processing
"""

import uuid
import time
import re
import struct
import secrets
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


def generate_uuid_v7():
    """
    UUID v7 표준 구현 (RFC 9562)

    UUID v7 구조:
    - 48비트: 타임스탬프 (milliseconds since Unix epoch)
    - 12비트: 순서 보장을 위한 추가 정밀도
    - 2비트: 버전 (0b01)
    - 62비트: 랜덤 데이터

    Returns:
        UUID v7 문자열
    """
    # 현재 시간을 밀리초 단위로 가져오기 (48비트)
    timestamp_ms = int(time.time() * 1000)

    # 48비트 타임스탬프를 바이트로 변환
    timestamp_bytes = struct.pack('>Q', timestamp_ms)[2:]  # 상위 48비트만 사용

    # 12비트 추가 정밀도 + 4비트 버전 필드 (0x7xxx)
    # 12비트 랜덤 + 버전 7
    ver_and_rand = 0x7000 | (secrets.randbits(12))
    ver_bytes = struct.pack('>H', ver_and_rand)

    # 2비트 variant (0b10) + 62비트 랜덤
    variant_and_rand = 0x8000000000000000 | secrets.randbits(62)
    variant_bytes = struct.pack('>Q', variant_and_rand)

    # 모든 바이트 조합
    uuid_bytes = timestamp_bytes + ver_bytes + variant_bytes

    # UUID 포맷으로 변환
    uuid_hex = uuid_bytes.hex()
    uuid_str = f"{uuid_hex[:8]}-{uuid_hex[8:12]}-{uuid_hex[12:16]}-{uuid_hex[16:20]}-{uuid_hex[20:]}"

    return uuid_str


def generate_time_based_uuid():
    """
    레거시 호환성을 위한 래퍼 함수
    이제 실제 UUID v7을 생성
    """
    return generate_uuid_v7()


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
        'original_image_file': page_dir / 'original.png',
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


def extract_timestamp_from_uuid_v7(uuid_str: str) -> Optional[datetime]:
    """
    UUID v7에서 정확한 타임스탬프 추출

    Args:
        uuid_str: UUID v7 문자열

    Returns:
        추출된 datetime 객체 또는 None
    """
    try:
        # UUID v7 형식 검증
        if not validate_request_id(uuid_str):
            return None

        # 하이픈 제거하고 16진수 문자열로 변환
        uuid_hex = uuid_str.replace('-', '')

        # 첫 12자리(48비트)가 타임스탬프
        timestamp_hex = uuid_hex[:12]
        timestamp_ms = int(timestamp_hex, 16)

        return datetime.fromtimestamp(timestamp_ms / 1000)
    except (ValueError, IndexError, OverflowError):
        return None


def extract_timestamp_from_uuid(request_id: str) -> Optional[datetime]:
    """
    레거시 호환성을 위한 래퍼 함수
    UUID v7 타임스탬프 추출
    """
    return extract_timestamp_from_uuid_v7(request_id)


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
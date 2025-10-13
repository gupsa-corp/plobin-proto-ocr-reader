#!/usr/bin/env python3
"""
Generate timestamped filenames and metadata for OCR results
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from .request_manager import generate_request_id, generate_request_metadata


def generate_filename(original_filename, suffix="result", extension="json"):
    """
    타임스탬프가 포함된 파일명 생성 (레거시 지원)

    Args:
        original_filename: 원본 파일명
        suffix: 접미사 (기본값: "result")
        extension: 확장자 (기본값: "json")

    Returns:
        타임스탬프가 포함된 새 파일명
    """
    # 원본 파일명에서 확장자 제거
    stem = Path(original_filename).stem

    # 현재 시간으로 타임스탬프 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 새 파일명 생성
    new_filename = f"{stem}_{timestamp}_{suffix}.{extension}"

    return new_filename


def create_page_metadata(page_number: int, total_blocks: int,
                        average_confidence: float, processing_time: float) -> Dict[str, Any]:
    """
    페이지 메타데이터 생성

    Args:
        page_number: 페이지 번호
        total_blocks: 총 블록 수
        average_confidence: 평균 신뢰도
        processing_time: 처리 시간

    Returns:
        페이지 메타데이터 딕셔너리
    """
    return {
        'page_number': page_number,
        'total_blocks': total_blocks,
        'average_confidence': average_confidence,
        'processing_time': processing_time,
        'processed_at': datetime.now().isoformat(),
        'version': '1.0'
    }


def create_block_metadata(block_id: int, text: str, confidence: float,
                         bbox: list, block_type: str = "text") -> Dict[str, Any]:
    """
    블록 메타데이터 생성

    Args:
        block_id: 블록 ID
        text: 추출된 텍스트
        confidence: 신뢰도
        bbox: 바운딩 박스 좌표
        block_type: 블록 타입

    Returns:
        블록 메타데이터 딕셔너리
    """
    return {
        'block_id': block_id,
        'text': text,
        'confidence': confidence,
        'bbox': bbox,
        'block_type': block_type,
        'text_length': len(text),
        'created_at': datetime.now().isoformat(),
        'version': '1.0'
    }


def save_metadata(metadata: Dict[str, Any], file_path: Path) -> None:
    """
    메타데이터를 JSON 파일로 저장

    Args:
        metadata: 저장할 메타데이터
        file_path: 저장할 파일 경로
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


def load_metadata(file_path: Path) -> Dict[str, Any]:
    """
    JSON 파일에서 메타데이터 로드

    Args:
        file_path: 로드할 파일 경로

    Returns:
        로드된 메타데이터
    """
    if not file_path.exists():
        raise FileNotFoundError(f"메타데이터 파일을 찾을 수 없습니다: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


__all__ = [
    'generate_filename',
    'create_page_metadata',
    'create_block_metadata',
    'save_metadata',
    'load_metadata'
]
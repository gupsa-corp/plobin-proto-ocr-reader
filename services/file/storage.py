#!/usr/bin/env python3
"""
File storage services for OCR results
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from .request_manager import (
    create_request_structure,
    create_page_structure,
    create_block_file_path,
    generate_request_metadata
)
from .metadata import save_metadata, load_metadata, create_page_metadata, create_block_metadata


def save_result(result_data, filename, output_dir):
    """
    OCR 결과를 JSON 파일로 저장 (레거시 지원)

    Args:
        result_data: 저장할 결과 데이터
        filename: 파일명 (확장자 포함)
        output_dir: 출력 디렉토리 경로

    Returns:
        저장된 파일의 전체 경로
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    file_path = output_path / filename

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)

    return str(file_path)


def load_result(file_path):
    """
    JSON 파일에서 OCR 결과를 로드

    Args:
        file_path: JSON 파일 경로

    Returns:
        로드된 결과 데이터
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


class RequestStorage:
    """새로운 요청 기반 저장 시스템"""

    def __init__(self, base_output_dir: str):
        self.base_output_dir = Path(base_output_dir)
        self.base_output_dir.mkdir(parents=True, exist_ok=True)

    def create_request(self, original_filename: str, file_type: str,
                      file_size: int, total_pages: int = 1) -> str:
        """
        새로운 요청 생성

        Args:
            original_filename: 원본 파일명
            file_type: 파일 타입
            file_size: 파일 크기
            total_pages: 총 페이지 수

        Returns:
            생성된 요청 ID
        """
        metadata = generate_request_metadata(
            original_filename, file_type, file_size, total_pages
        )
        request_id = metadata['request_id']

        # 요청 구조 생성
        paths = create_request_structure(str(self.base_output_dir), request_id)

        # 메타데이터 저장
        save_metadata(metadata, paths['metadata_file'])

        return request_id

    def save_page_result(self, request_id: str, page_number: int,
                        blocks: List[Dict[str, Any]], processing_time: float,
                        visualization_data: bytes = None) -> Dict[str, str]:
        """
        페이지 OCR 결과 저장

        Args:
            request_id: 요청 ID
            page_number: 페이지 번호
            blocks: 블록 데이터 리스트
            processing_time: 처리 시간
            visualization_data: 시각화 이미지 데이터

        Returns:
            저장된 파일 경로들
        """
        request_dir = self.base_output_dir / request_id
        if not request_dir.exists():
            raise ValueError(f"요청 ID를 찾을 수 없습니다: {request_id}")

        # 페이지 구조 생성
        page_paths = create_page_structure(request_dir, page_number)

        # 페이지 메타데이터 생성 및 저장
        total_blocks = len(blocks)
        avg_confidence = sum(block.get('confidence', 0) for block in blocks) / max(total_blocks, 1)

        page_metadata = create_page_metadata(
            page_number, total_blocks, avg_confidence, processing_time
        )
        save_metadata(page_metadata, page_paths['page_info_file'])

        # 전체 결과 저장
        page_result = {
            'page_number': page_number,
            'total_blocks': total_blocks,
            'average_confidence': avg_confidence,
            'processing_time': processing_time,
            'blocks': blocks
        }
        with open(page_paths['result_file'], 'w', encoding='utf-8') as f:
            json.dump(page_result, f, ensure_ascii=False, indent=2)

        # 개별 블록 저장
        for i, block in enumerate(blocks):
            block_metadata = create_block_metadata(
                i + 1,
                block.get('text', ''),
                block.get('confidence', 0),
                block.get('bbox', []),
                block.get('block_type', 'text')
            )
            block_file = create_block_file_path(page_paths['blocks_dir'], i + 1)
            save_metadata(block_metadata, block_file)

        # 시각화 저장
        if visualization_data:
            with open(page_paths['visualization_file'], 'wb') as f:
                f.write(visualization_data)

        return {
            'page_info': str(page_paths['page_info_file']),
            'result': str(page_paths['result_file']),
            'visualization': str(page_paths['visualization_file']) if visualization_data else None,
            'blocks_dir': str(page_paths['blocks_dir'])
        }

    def complete_request(self, request_id: str, summary_data: Dict[str, Any]) -> None:
        """
        요청 완료 처리

        Args:
            request_id: 요청 ID
            summary_data: 요약 데이터
        """
        request_dir = self.base_output_dir / request_id
        if not request_dir.exists():
            raise ValueError(f"요청 ID를 찾을 수 없습니다: {request_id}")

        # 요청 메타데이터 업데이트
        metadata_file = request_dir / 'metadata.json'
        metadata = load_metadata(metadata_file)
        metadata['processing_status'] = 'completed'
        metadata['completed_at'] = summary_data.get('completed_at')
        save_metadata(metadata, metadata_file)

        # 요약 저장
        summary_file = request_dir / 'summary.json'
        save_metadata(summary_data, summary_file)

    def get_request_metadata(self, request_id: str) -> Dict[str, Any]:
        """
        요청 메타데이터 조회

        Args:
            request_id: 요청 ID

        Returns:
            요청 메타데이터
        """
        metadata_file = self.base_output_dir / request_id / 'metadata.json'
        return load_metadata(metadata_file)

    def get_page_result(self, request_id: str, page_number: int) -> Dict[str, Any]:
        """
        페이지 결과 조회

        Args:
            request_id: 요청 ID
            page_number: 페이지 번호

        Returns:
            페이지 결과 데이터
        """
        result_file = self.base_output_dir / request_id / f"page_{page_number:03d}" / 'result.json'
        return load_metadata(result_file)

    def get_block_data(self, request_id: str, page_number: int, block_id: int) -> Dict[str, Any]:
        """
        개별 블록 데이터 조회

        Args:
            request_id: 요청 ID
            page_number: 페이지 번호
            block_id: 블록 ID

        Returns:
            블록 데이터
        """
        blocks_dir = self.base_output_dir / request_id / f"page_{page_number:03d}" / 'blocks'
        block_file = create_block_file_path(blocks_dir, block_id)
        return load_metadata(block_file)


__all__ = ['save_result', 'load_result', 'RequestStorage']
#!/usr/bin/env python3
"""
File storage services for OCR results
"""

import json
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional
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
                        visualization_data: bytes = None, original_image_data: bytes = None) -> Dict[str, str]:
        """
        페이지 OCR 결과 저장

        Args:
            request_id: 요청 ID
            page_number: 페이지 번호
            blocks: 블록 데이터 리스트
            processing_time: 처리 시간
            visualization_data: 시각화 이미지 데이터
            original_image_data: 원본 페이지 이미지 데이터

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

        # 개별 블록 저장 및 이미지 크롭
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

            # 블록 이미지 크롭 및 저장
            if original_image_data and block.get('bbox'):
                self._save_block_image(
                    original_image_data,
                    block['bbox'],
                    page_paths['blocks_dir'],
                    i + 1
                )

        # 원본 이미지 저장
        if original_image_data:
            with open(page_paths['original_image_file'], 'wb') as f:
                f.write(original_image_data)

        # 시각화 저장
        if visualization_data:
            with open(page_paths['visualization_file'], 'wb') as f:
                f.write(visualization_data)

        return {
            'page_info': str(page_paths['page_info_file']),
            'result': str(page_paths['result_file']),
            'original_image': str(page_paths['original_image_file']) if original_image_data else None,
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
        result_file = self.base_output_dir / request_id / "pages" / f"{page_number:03d}" / 'result.json'
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
        blocks_dir = self.base_output_dir / request_id / "pages" / f"{page_number:03d}" / 'blocks'
        block_file = create_block_file_path(blocks_dir, block_id)
        return load_metadata(block_file)

    def save_block_images(self, request_id: str, page_number: int,
                         block_images: List[tuple]) -> Dict[str, str]:
        """
        블록 이미지들을 저장

        Args:
            request_id: 요청 ID
            page_number: 페이지 번호
            block_images: (블록_id, 이미지_데이터) 튜플 리스트

        Returns:
            저장된 블록 이미지 경로들
        """
        request_dir = self.base_output_dir / request_id
        if not request_dir.exists():
            raise ValueError(f"요청 ID를 찾을 수 없습니다: {request_id}")

        blocks_dir = request_dir / "pages" / f"{page_number:03d}" / "blocks"
        if not blocks_dir.exists():
            raise ValueError(f"블록 디렉토리를 찾을 수 없습니다: {blocks_dir}")

        saved_paths = {}

        for block_id, image_data in block_images:
            try:
                # 블록 이미지 파일 경로
                image_file = blocks_dir / f"block_{block_id + 1:03d}.png"

                # numpy 배열인 경우 PNG로 저장
                if isinstance(image_data, np.ndarray):
                    cv2.imwrite(str(image_file), image_data)
                # bytes 데이터인 경우 직접 저장
                elif isinstance(image_data, bytes):
                    with open(image_file, 'wb') as f:
                        f.write(image_data)
                else:
                    print(f"지원되지 않는 이미지 데이터 타입: {type(image_data)}")
                    continue

                saved_paths[f"block_{block_id + 1:03d}"] = str(image_file)

            except Exception as e:
                print(f"블록 {block_id} 이미지 저장 실패: {e}")
                continue

        return saved_paths

    def save_original_image(self, request_id: str, page_number: int, image_path: str) -> Optional[str]:
        """
        원본 이미지를 요청 디렉토리에 복사 저장

        Args:
            request_id: 요청 ID
            page_number: 페이지 번호
            image_path: 원본 이미지 경로

        Returns:
            저장된 이미지 경로
        """
        request_dir = self.base_output_dir / request_id
        if not request_dir.exists():
            raise ValueError(f"요청 ID를 찾을 수 없습니다: {request_id}")

        page_dir = request_dir / "pages" / f"{page_number:03d}"
        if not page_dir.exists():
            raise ValueError(f"페이지 디렉토리를 찾을 수 없습니다: {page_dir}")

        try:
            # 원본 이미지 읽기
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"이미지를 읽을 수 없습니다: {image_path}")

            # 저장 경로
            original_file = page_dir / "original.png"

            # 이미지 저장
            cv2.imwrite(str(original_file), image)

            return str(original_file)

        except Exception as e:
            print(f"원본 이미지 저장 실패: {e}")
            return None

    def _save_block_image(self, original_image_data: bytes, bbox: list, blocks_dir: Path, block_id: int) -> None:
        """
        블록 영역을 크롭하여 이미지로 저장

        Args:
            original_image_data: 원본 이미지 바이트 데이터
            bbox: 바운딩 박스 좌표 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            blocks_dir: 블록 디렉토리 경로
            block_id: 블록 ID
        """
        try:
            # 바이트 데이터를 numpy 배열로 변환
            img_array = np.frombuffer(original_image_data, np.uint8)
            image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

            if image is None:
                print(f"블록 {block_id}: 이미지 디코딩 실패")
                return

            # 바운딩 박스에서 min/max 좌표 추출
            if len(bbox) >= 4 and all(len(point) >= 2 for point in bbox):
                x_coords = [point[0] for point in bbox]
                y_coords = [point[1] for point in bbox]

                x_min, x_max = max(0, min(x_coords)), min(image.shape[1], max(x_coords))
                y_min, y_max = max(0, min(y_coords)), min(image.shape[0], max(y_coords))

                # 유효한 영역인지 확인
                if x_max > x_min and y_max > y_min:
                    # 이미지 크롭
                    cropped = image[y_min:y_max, x_min:x_max]

                    # 블록 이미지 저장
                    block_image_path = blocks_dir / f"block_{block_id:03d}.png"
                    cv2.imwrite(str(block_image_path), cropped)
                    print(f"블록 {block_id} 이미지 저장 완료: {block_image_path}")
                else:
                    print(f"블록 {block_id}: 유효하지 않은 바운딩 박스 영역")
            else:
                print(f"블록 {block_id}: 잘못된 바운딩 박스 형식")

        except Exception as e:
            print(f"블록 {block_id} 이미지 크롭 실패: {e}")


__all__ = ['save_result', 'load_result', 'RequestStorage']
#!/usr/bin/env python3
"""
Block editing and management services
"""

import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from services.file.storage import RequestStorage
from services.ocr.visualization import visualize_blocks


class BlockEditor:
    """블록 편집 및 관리 서비스"""

    def __init__(self, request_storage: RequestStorage):
        self.storage = request_storage

    def get_block(self, request_id: str, page_number: int, block_id: int) -> Optional[Dict[str, Any]]:
        """
        특정 블록 정보 조회

        Args:
            request_id: 요청 ID
            page_number: 페이지 번호
            block_id: 블록 ID (1부터 시작)

        Returns:
            블록 정보 또는 None
        """
        try:
            request_dir = self.storage.base_output_dir / request_id
            page_dir = request_dir / "pages" / f"{page_number:03d}"
            result_file = page_dir / "result.json"

            if not result_file.exists():
                return None

            with open(result_file, 'r', encoding='utf-8') as f:
                page_result = json.load(f)

            blocks = page_result.get('blocks', [])
            if block_id < 1 or block_id > len(blocks):
                return None

            block = blocks[block_id - 1].copy()
            block['block_id'] = block_id
            block['page_number'] = page_number

            # 블록 이미지 URL 추가
            block['image_url'] = f"/requests/{request_id}/pages/{page_number}/blocks/{block_id}/image"

            # 블록 요약 정보 추가 (옵션)
            try:
                from services.analysis import ContentSummarizer
                summarizer = ContentSummarizer()
                block_summary = summarizer.create_block_summary(block)
                block['summary'] = block_summary
            except Exception as summary_error:
                print(f"블록 요약 생성 실패: {summary_error}")
                block['summary'] = None

            return block

        except Exception as e:
            print(f"블록 조회 실패: {e}")
            return None

    def get_blocks_filtered(self, request_id: str, page_number: int,
                          block_type: Optional[str] = None,
                          confidence_min: Optional[float] = None,
                          start: int = 0, limit: int = 100) -> Dict[str, Any]:
        """
        필터링된 블록 목록 조회

        Args:
            request_id: 요청 ID
            page_number: 페이지 번호
            block_type: 블록 타입 필터
            confidence_min: 최소 신뢰도
            start: 시작 인덱스
            limit: 최대 개수

        Returns:
            필터링된 블록 목록과 메타데이터
        """
        try:
            request_dir = self.storage.base_output_dir / request_id
            page_dir = request_dir / "pages" / f"{page_number:03d}"
            result_file = page_dir / "result.json"

            if not result_file.exists():
                return {"blocks": [], "total": 0, "filtered": 0}

            with open(result_file, 'r', encoding='utf-8') as f:
                page_result = json.load(f)

            blocks = page_result.get('blocks', [])
            total_blocks = len(blocks)

            # 필터링
            filtered_blocks = []
            for i, block in enumerate(blocks):
                # 타입 필터
                if block_type and block.get('block_type') != block_type:
                    continue

                # 신뢰도 필터
                if confidence_min and block.get('confidence', 0) < confidence_min:
                    continue

                # 블록 정보 보강
                enhanced_block = block.copy()
                enhanced_block['block_id'] = i + 1
                enhanced_block['page_number'] = page_number
                enhanced_block['image_url'] = f"/requests/{request_id}/pages/{page_number}/blocks/{i + 1}/image"

                filtered_blocks.append(enhanced_block)

            # 페이지네이션
            filtered_count = len(filtered_blocks)
            paginated_blocks = filtered_blocks[start:start + limit]

            return {
                "blocks": paginated_blocks,
                "total": total_blocks,
                "filtered": filtered_count,
                "start": start,
                "limit": limit,
                "has_more": start + limit < filtered_count
            }

        except Exception as e:
            print(f"블록 필터링 실패: {e}")
            return {"blocks": [], "total": 0, "filtered": 0}

    def update_block_text(self, request_id: str, page_number: int, block_id: int, new_text: str) -> bool:
        """
        블록 텍스트 업데이트

        Args:
            request_id: 요청 ID
            page_number: 페이지 번호
            block_id: 블록 ID
            new_text: 새로운 텍스트

        Returns:
            업데이트 성공 여부
        """
        return self.storage.update_block_in_page(request_id, page_number, block_id, {'text': new_text})

    def update_block_type(self, request_id: str, page_number: int, block_id: int, new_type: str) -> bool:
        """
        블록 타입 업데이트

        Args:
            request_id: 요청 ID
            page_number: 페이지 번호
            block_id: 블록 ID
            new_type: 새로운 블록 타입

        Returns:
            업데이트 성공 여부
        """
        valid_types = ['title', 'paragraph', 'table', 'list', 'other']
        if new_type not in valid_types:
            return False

        return self.storage.update_block_in_page(request_id, page_number, block_id, {'block_type': new_type})

    def update_block(self, request_id: str, page_number: int, block_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        블록 정보 일괄 업데이트

        Args:
            request_id: 요청 ID
            page_number: 페이지 번호
            block_id: 블록 ID
            updates: 업데이트할 데이터

        Returns:
            업데이트 결과 및 블록 정보
        """
        try:
            # 유효성 검사
            if 'block_type' in updates:
                valid_types = ['title', 'paragraph', 'table', 'list', 'other']
                if updates['block_type'] not in valid_types:
                    return {"success": False, "error": "Invalid block type"}

            if 'confidence' in updates:
                confidence = updates['confidence']
                if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
                    return {"success": False, "error": "Invalid confidence value"}

            # 업데이트 수행
            success = self.storage.update_block_in_page(request_id, page_number, block_id, updates)

            if success:
                # 시각화 재생성 필요 여부 확인
                regenerate_viz = any(key in updates for key in ['bbox', 'block_type'])

                # 업데이트된 블록 정보 조회
                updated_block = self.get_block(request_id, page_number, block_id)

                return {
                    "success": True,
                    "updated_block": updated_block,
                    "regenerated_visualization": regenerate_viz
                }
            else:
                return {"success": False, "error": "Update failed"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_block(self, request_id: str, page_number: int, block_id: int) -> Dict[str, Any]:
        """
        블록 삭제

        Args:
            request_id: 요청 ID
            page_number: 페이지 번호
            block_id: 블록 ID

        Returns:
            삭제 결과
        """
        try:
            success = self.storage.delete_block_from_page(request_id, page_number, block_id)

            if success:
                return {
                    "success": True,
                    "deleted_block_id": block_id,
                    "regenerated_visualization": True
                }
            else:
                return {"success": False, "error": "Delete failed"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def add_block(self, request_id: str, page_number: int, block_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        새 블록 추가

        Args:
            request_id: 요청 ID
            page_number: 페이지 번호
            block_data: 블록 데이터

        Returns:
            추가 결과 및 새 블록 정보
        """
        try:
            # 유효성 검사
            required_fields = ['text', 'bbox']
            for field in required_fields:
                if field not in block_data:
                    return {"success": False, "error": f"Missing required field: {field}"}

            # 기본값 설정
            block_data.setdefault('confidence', 1.0)
            block_data.setdefault('block_type', 'other')

            # 블록 추가
            new_block_id = self.storage.add_block_to_page(request_id, page_number, block_data)

            if new_block_id:
                # 새로 추가된 블록 정보 조회
                new_block = self.get_block(request_id, page_number, new_block_id)

                return {
                    "success": True,
                    "new_block": new_block,
                    "new_block_id": new_block_id,
                    "regenerated_visualization": True
                }
            else:
                return {"success": False, "error": "Add failed"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def regenerate_visualization(self, request_id: str, page_number: int) -> bool:
        """
        페이지 시각화 재생성

        Args:
            request_id: 요청 ID
            page_number: 페이지 번호

        Returns:
            재생성 성공 여부
        """
        try:
            request_dir = self.storage.base_output_dir / request_id
            page_dir = request_dir / "pages" / f"{page_number:03d}"

            # 원본 이미지와 결과 데이터 확인
            original_file = page_dir / "original.png"
            result_file = page_dir / "result.json"

            if not original_file.exists() or not result_file.exists():
                return False

            # 결과 데이터 로드
            with open(result_file, 'r', encoding='utf-8') as f:
                page_result = json.load(f)

            blocks = page_result.get('blocks', [])

            # 시각화 재생성
            visualization_path = page_dir / "visualization.png"
            visualize_blocks(str(original_file), blocks, str(visualization_path))

            return True

        except Exception as e:
            print(f"시각화 재생성 실패: {e}")
            return False


__all__ = ['BlockEditor']
"""
Template matching service.
"""

from typing import Dict, List, Optional, Tuple, Any
import logging
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)


class TemplateMatcher:
    """템플릿 매칭 서비스"""

    def __init__(self):
        pass

    def find_best_template(self, image_path: str, templates: List[Dict[str, Any]]) -> Tuple[Optional[str], float]:
        """
        이미지에 가장 적합한 템플릿 찾기

        Args:
            image_path: 이미지 파일 경로
            templates: 사용 가능한 템플릿 목록

        Returns:
            (template_id, confidence_score) 튜플
        """
        try:
            if not templates:
                return None, 0.0

            # TODO: 실제 매칭 알고리즘 구현
            # 현재는 더미 로직으로 첫 번째 템플릿을 반환
            best_template = templates[0]
            confidence = 0.82

            logger.info(f"Best template match: {best_template['template_id']} with confidence {confidence}")
            return best_template['template_id'], confidence

        except Exception as e:
            logger.error(f"Error finding best template: {str(e)}")
            return None, 0.0

    def match_template(self, image_path: str, template_id: str, template_data: Dict[str, Any]) -> float:
        """
        특정 템플릿과의 유사도 계산

        Args:
            image_path: 이미지 파일 경로
            template_id: 템플릿 ID
            template_data: 템플릿 데이터

        Returns:
            유사도 점수 (0.0 ~ 1.0)
        """
        try:
            # TODO: 실제 매칭 알고리즘 구현
            # 현재는 더미 값 반환
            confidence = 0.85

            logger.info(f"Template {template_id} match confidence: {confidence}")
            return confidence

        except Exception as e:
            logger.error(f"Error matching template {template_id}: {str(e)}")
            return 0.0

    def extract_with_template(self, image_path: str, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        템플릿 기반 데이터 추출

        Args:
            image_path: 이미지 파일 경로
            template_data: 템플릿 데이터

        Returns:
            추출된 데이터
        """
        try:
            # TODO: 실제 템플릿 기반 추출 로직 구현
            # 현재는 더미 데이터 반환
            extracted_data = {}
            field_confidences = {}

            for field in template_data.get('fields', []):
                field_id = field['field_id']
                field_name = field['name']

                # 더미 추출 데이터
                if field['type'] == 'currency':
                    extracted_data[field_id] = "₩1,234,567"
                    field_confidences[field_id] = 0.92
                elif field['type'] == 'date':
                    extracted_data[field_id] = "2025-10-01"
                    field_confidences[field_id] = 0.88
                elif field['type'] == 'text':
                    extracted_data[field_id] = f"추출된 {field_name}"
                    field_confidences[field_id] = 0.85
                elif field['type'] == 'table':
                    extracted_data[field_id] = [
                        {"상품명": "제품A", "수량": "2", "단가": "₩10,000", "금액": "₩20,000"},
                        {"상품명": "제품B", "수량": "1", "단가": "₩15,000", "금액": "₩15,000"}
                    ]
                    field_confidences[field_id] = 0.79
                else:
                    extracted_data[field_id] = f"값_{field_id}"
                    field_confidences[field_id] = 0.80

            result = {
                "template_id": template_data.get('template_id'),
                "template_name": template_data.get('name'),
                "confidence_score": 0.85,
                "extracted_fields": extracted_data,
                "field_confidences": field_confidences,
                "processing_time": 1.2,
                "validation_errors": []
            }

            logger.info(f"Template extraction completed for {template_data.get('template_id')}")
            return result

        except Exception as e:
            logger.error(f"Error extracting with template: {str(e)}")
            return {
                "template_id": template_data.get('template_id'),
                "template_name": template_data.get('name'),
                "confidence_score": 0.0,
                "extracted_fields": {},
                "field_confidences": {},
                "processing_time": 0.0,
                "validation_errors": [f"추출 중 오류 발생: {str(e)}"]
            }
"""
Template validation service.
"""

import re
import json
from typing import Dict, List, Any, Tuple
from datetime import datetime
from pathlib import Path

from api.models.template import (
    TemplateCreate, TemplateField, FieldType,
    TemplateValidationResult, BoundingBox
)


class TemplateValidator:
    """템플릿 검증 서비스"""

    def __init__(self):
        self.categories_path = Path("templates/metadata/categories.json")
        self._load_categories()

    def _load_categories(self):
        """카테고리 정보 로드"""
        try:
            with open(self.categories_path, 'r', encoding='utf-8') as f:
                categories_data = json.load(f)
                self.categories = categories_data.get('categories', {})
                self.field_types = categories_data.get('field_types', {})
        except Exception:
            self.categories = {}
            self.field_types = {}

    def validate_template(self, template_data: TemplateCreate) -> TemplateValidationResult:
        """
        템플릿 전체 검증

        Args:
            template_data: 검증할 템플릿 데이터

        Returns:
            검증 결과
        """
        errors = []
        warnings = []
        field_validation_results = {}

        # 기본 정보 검증
        errors.extend(self._validate_basic_info(template_data))

        # 페이지 레이아웃 검증
        errors.extend(self._validate_page_layout(template_data.page_layout))

        # 필드들 검증
        field_errors, field_results = self._validate_fields(
            template_data.fields,
            template_data.page_layout
        )
        errors.extend(field_errors)
        field_validation_results = field_results

        # 필드 중복 검증
        errors.extend(self._validate_field_uniqueness(template_data.fields))

        # 바운딩 박스 겹침 검증
        warnings.extend(self._validate_bbox_overlaps(template_data.fields))

        # 매칭 규칙 검증
        if template_data.matching_rules:
            errors.extend(self._validate_matching_rules(template_data.matching_rules))

        return TemplateValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            field_validation_results=field_validation_results
        )

    def _validate_basic_info(self, template_data: TemplateCreate) -> List[str]:
        """기본 정보 검증"""
        errors = []

        # 이름 검증
        if not template_data.name or len(template_data.name.strip()) == 0:
            errors.append("템플릿 이름은 필수입니다")
        elif len(template_data.name) > 100:
            errors.append("템플릿 이름은 100자를 초과할 수 없습니다")

        # 문서 타입 검증
        if not template_data.document_type or len(template_data.document_type.strip()) == 0:
            errors.append("문서 타입은 필수입니다")

        # 카테고리 검증
        if template_data.category.value not in self.categories:
            errors.append(f"지원하지 않는 카테고리입니다: {template_data.category}")

        # 신뢰도 임계값 검증
        if not 0.0 <= template_data.confidence_threshold <= 1.0:
            errors.append("신뢰도 임계값은 0.0과 1.0 사이여야 합니다")

        # 언어 코드 검증
        valid_languages = ['ko', 'en', 'ja', 'zh', 'auto']
        if template_data.language not in valid_languages:
            errors.append(f"지원하지 않는 언어 코드입니다: {template_data.language}")

        return errors

    def _validate_page_layout(self, page_layout) -> List[str]:
        """페이지 레이아웃 검증"""
        errors = []

        # 크기 검증
        if page_layout.width <= 0:
            errors.append("페이지 너비는 0보다 커야 합니다")
        if page_layout.height <= 0:
            errors.append("페이지 높이는 0보다 커야 합니다")

        # 최대 크기 제한
        max_dimension = 10000
        if page_layout.width > max_dimension:
            errors.append(f"페이지 너비는 {max_dimension}픽셀을 초과할 수 없습니다")
        if page_layout.height > max_dimension:
            errors.append(f"페이지 높이는 {max_dimension}픽셀을 초과할 수 없습니다")

        # 방향 검증
        valid_orientations = ['portrait', 'landscape']
        if page_layout.orientation not in valid_orientations:
            errors.append(f"지원하지 않는 방향입니다: {page_layout.orientation}")

        # 단위 검증
        valid_units = ['pixels', 'points', 'inches', 'mm']
        if page_layout.unit not in valid_units:
            errors.append(f"지원하지 않는 단위입니다: {page_layout.unit}")

        return errors

    def _validate_fields(self, fields: List[TemplateField], page_layout) -> Tuple[List[str], Dict]:
        """필드들 검증"""
        errors = []
        field_results = {}

        if not fields:
            errors.append("최소 하나의 필드가 필요합니다")
            return errors, field_results

        for i, field in enumerate(fields):
            field_errors = []

            # 필드 ID 검증
            if not field.field_id or not field.field_id.strip():
                field_errors.append("필드 ID는 필수입니다")
            elif not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', field.field_id):
                field_errors.append("필드 ID는 영문자로 시작하고 영문자, 숫자, 언더스코어만 포함해야 합니다")

            # 필드 이름 검증
            if not field.name or not field.name.strip():
                field_errors.append("필드 이름은 필수입니다")

            # 바운딩 박스 검증
            bbox_errors = self._validate_bbox(field.bbox, page_layout)
            field_errors.extend(bbox_errors)

            # 필드 타입별 검증
            type_errors = self._validate_field_type(field)
            field_errors.extend(type_errors)

            # 검증 규칙 확인
            if field.validation:
                validation_errors = self._validate_field_validation(field)
                field_errors.extend(validation_errors)

            field_results[field.field_id] = {
                'is_valid': len(field_errors) == 0,
                'errors': field_errors
            }

            errors.extend([f"필드 '{field.field_id}': {error}" for error in field_errors])

        return errors, field_results

    def _validate_bbox(self, bbox: BoundingBox, page_layout) -> List[str]:
        """바운딩 박스 검증"""
        errors = []

        # 좌표 유효성 검증
        if bbox.x1 < 0 or bbox.y1 < 0:
            errors.append("바운딩 박스 좌상단 좌표는 0 이상이어야 합니다")

        if bbox.x2 > page_layout.width or bbox.y2 > page_layout.height:
            errors.append("바운딩 박스가 페이지 범위를 벗어납니다")

        # 최소 크기 검증
        min_size = 10
        if (bbox.x2 - bbox.x1) < min_size:
            errors.append(f"바운딩 박스 너비는 최소 {min_size}픽셀이어야 합니다")
        if (bbox.y2 - bbox.y1) < min_size:
            errors.append(f"바운딩 박스 높이는 최소 {min_size}픽셀이어야 합니다")

        return errors

    def _validate_field_type(self, field: TemplateField) -> List[str]:
        """필드 타입별 검증"""
        errors = []

        # 테이블 타입 특별 검증
        if field.type == FieldType.TABLE:
            if not field.table_structure:
                errors.append("테이블 타입은 table_structure가 필요합니다")
            else:
                if 'columns' not in field.table_structure:
                    errors.append("테이블 구조에 columns 정의가 필요합니다")
                elif len(field.table_structure['columns']) == 0:
                    errors.append("테이블은 최소 하나의 컬럼이 필요합니다")

        return errors

    def _validate_field_validation(self, field: TemplateField) -> List[str]:
        """필드 검증 규칙 확인"""
        errors = []
        validation = field.validation

        # 정규식 검증
        if validation.regex:
            try:
                re.compile(validation.regex)
            except re.error:
                errors.append("유효하지 않은 정규식입니다")

        # 길이 검증
        if validation.max_length is not None and validation.max_length <= 0:
            errors.append("최대 길이는 0보다 커야 합니다")

        if (validation.min_length is not None and
            validation.max_length is not None and
            validation.min_length > validation.max_length):
            errors.append("최소 길이는 최대 길이보다 작아야 합니다")

        # 숫자/화폐 값 검증
        if (validation.min_value is not None and
            validation.max_value is not None and
            validation.min_value > validation.max_value):
            errors.append("최소값은 최대값보다 작아야 합니다")

        # 날짜 형식 검증
        if validation.date_format:
            try:
                datetime.strptime("2025-01-01", validation.date_format)
            except ValueError:
                errors.append("유효하지 않은 날짜 형식입니다")

        return errors

    def _validate_field_uniqueness(self, fields: List[TemplateField]) -> List[str]:
        """필드 고유성 검증"""
        errors = []

        # 필드 ID 중복 검사
        field_ids = [field.field_id for field in fields]
        duplicates = set([id for id in field_ids if field_ids.count(id) > 1])

        for duplicate in duplicates:
            errors.append(f"중복된 필드 ID가 있습니다: {duplicate}")

        return errors

    def _validate_bbox_overlaps(self, fields: List[TemplateField]) -> List[str]:
        """바운딩 박스 겹침 검증 (경고)"""
        warnings = []

        for i, field1 in enumerate(fields):
            for j, field2 in enumerate(fields[i+1:], i+1):
                if self._bboxes_overlap(field1.bbox, field2.bbox):
                    warnings.append(
                        f"필드 '{field1.field_id}'와 '{field2.field_id}'의 "
                        f"바운딩 박스가 겹칩니다"
                    )

        return warnings

    def _bboxes_overlap(self, bbox1: BoundingBox, bbox2: BoundingBox) -> bool:
        """두 바운딩 박스가 겹치는지 확인"""
        return not (bbox1.x2 <= bbox2.x1 or bbox2.x2 <= bbox1.x1 or
                   bbox1.y2 <= bbox2.y1 or bbox2.y2 <= bbox1.y1)

    def _validate_matching_rules(self, matching_rules) -> List[str]:
        """매칭 규칙 검증"""
        errors = []

        # 임계값 검증
        if not 0.0 <= matching_rules.layout_similarity_threshold <= 1.0:
            errors.append("레이아웃 유사도 임계값은 0.0과 1.0 사이여야 합니다")

        if not 0.0 <= matching_rules.text_similarity_threshold <= 1.0:
            errors.append("텍스트 유사도 임계값은 0.0과 1.0 사이여야 합니다")

        # 키 지시어 검증
        total_weight = sum(indicator.get('weight', 0) for indicator in matching_rules.key_indicators)
        if total_weight > 1.0:
            errors.append("키 지시어들의 가중치 합은 1.0을 초과할 수 없습니다")

        return errors
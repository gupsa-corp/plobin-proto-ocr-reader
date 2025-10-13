"""
Template management service.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging

from api.models.template import (
    TemplateCreate, TemplateUpdate, TemplateResponse,
    TemplateValidationResult, TemplateListResponse
)
from .storage import TemplateStorage
from .validator import TemplateValidator

logger = logging.getLogger(__name__)


class TemplateManager:
    """템플릿 관리 서비스"""

    def __init__(self):
        self.storage = TemplateStorage()
        self.validator = TemplateValidator()

    def create_template(self, template_data: TemplateCreate, author: str = "system") -> Tuple[bool, str, Optional[str]]:
        """
        새 템플릿 생성

        Args:
            template_data: 템플릿 생성 데이터
            author: 생성자

        Returns:
            (성공여부, 메시지, 템플릿ID)
        """
        try:
            # 템플릿 검증
            validation_result = self.validator.validate_template(template_data)

            if not validation_result.is_valid:
                error_msg = "템플릿 검증 실패: " + "; ".join(validation_result.errors)
                logger.warning(f"Template validation failed: {error_msg}")
                return False, error_msg, None

            # 중복 이름 확인
            existing_templates = self.storage.list_templates()
            existing_names = [t['name'] for t in existing_templates]

            if template_data.name in existing_names:
                return False, f"이미 존재하는 템플릿 이름입니다: {template_data.name}", None

            # 템플릿 저장
            template_id = self.storage.save_template(template_data, author)

            logger.info(f"Template created successfully: {template_id}")
            return True, f"템플릿이 성공적으로 생성되었습니다: {template_id}", template_id

        except Exception as e:
            error_msg = f"템플릿 생성 중 오류 발생: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None

    def get_template(self, template_id: str) -> Optional[TemplateResponse]:
        """
        템플릿 조회

        Args:
            template_id: 템플릿 ID

        Returns:
            템플릿 응답 데이터 또는 None
        """
        try:
            template_data = self.storage.get_template(template_id)
            if not template_data:
                return None

            return self._convert_to_response(template_data)

        except Exception as e:
            logger.error(f"Error getting template {template_id}: {str(e)}")
            return None

    def list_templates(self,
                      category: Optional[str] = None,
                      document_type: Optional[str] = None,
                      status: Optional[str] = None,
                      page: int = 1,
                      limit: int = 20) -> TemplateListResponse:
        """
        템플릿 목록 조회

        Args:
            category: 카테고리 필터
            document_type: 문서 타입 필터
            status: 상태 필터
            page: 페이지 번호
            limit: 페이지당 항목 수

        Returns:
            템플릿 목록 응답
        """
        try:
            # 모든 템플릿 조회
            all_templates = self.storage.list_templates(category, document_type, status)

            # 정렬 (최근 업데이트순)
            all_templates.sort(key=lambda x: x.get('updated_at', ''), reverse=True)

            # 페이징
            total = len(all_templates)
            start_idx = (page - 1) * limit
            end_idx = start_idx + limit
            page_templates = all_templates[start_idx:end_idx]

            # 응답 변환
            template_responses = []
            for template_summary in page_templates:
                template_data = self.storage.get_template(template_summary['template_id'])
                if template_data:
                    template_responses.append(self._convert_to_response(template_data))

            return TemplateListResponse(
                templates=template_responses,
                total=total,
                page=page,
                limit=limit
            )

        except Exception as e:
            logger.error(f"Error listing templates: {str(e)}")
            return TemplateListResponse(templates=[], total=0, page=page, limit=limit)

    def update_template(self, template_id: str, updates: TemplateUpdate) -> Tuple[bool, str]:
        """
        템플릿 업데이트

        Args:
            template_id: 템플릿 ID
            updates: 업데이트 데이터

        Returns:
            (성공여부, 메시지)
        """
        try:
            # 기존 템플릿 확인
            existing_template = self.storage.get_template(template_id)
            if not existing_template:
                return False, f"템플릿을 찾을 수 없습니다: {template_id}"

            # 업데이트 데이터 준비
            update_dict = {}
            for field, value in updates.dict(exclude_unset=True).items():
                if value is not None:
                    if hasattr(value, 'dict'):
                        update_dict[field] = value.dict()
                    elif isinstance(value, list):
                        update_dict[field] = [
                            item.dict() if hasattr(item, 'dict') else item
                            for item in value
                        ]
                    else:
                        update_dict[field] = value

            # 이름 중복 확인 (이름 변경 시)
            if 'name' in update_dict:
                existing_templates = self.storage.list_templates()
                existing_names = [
                    t['name'] for t in existing_templates
                    if t['template_id'] != template_id
                ]

                if update_dict['name'] in existing_names:
                    return False, f"이미 존재하는 템플릿 이름입니다: {update_dict['name']}"

            # 업데이트 적용
            success = self.storage.update_template(template_id, update_dict)

            if success:
                logger.info(f"Template updated successfully: {template_id}")
                return True, "템플릿이 성공적으로 업데이트되었습니다"
            else:
                return False, "템플릿 업데이트에 실패했습니다"

        except Exception as e:
            error_msg = f"템플릿 업데이트 중 오류 발생: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def delete_template(self, template_id: str) -> Tuple[bool, str]:
        """
        템플릿 삭제

        Args:
            template_id: 템플릿 ID

        Returns:
            (성공여부, 메시지)
        """
        try:
            # 템플릿 존재 확인
            if not self.storage.get_template(template_id):
                return False, f"템플릿을 찾을 수 없습니다: {template_id}"

            # 삭제 실행
            success = self.storage.delete_template(template_id)

            if success:
                logger.info(f"Template deleted successfully: {template_id}")
                return True, "템플릿이 성공적으로 삭제되었습니다"
            else:
                return False, "템플릿 삭제에 실패했습니다"

        except Exception as e:
            error_msg = f"템플릿 삭제 중 오류 발생: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def validate_template(self, template_data: TemplateCreate) -> TemplateValidationResult:
        """
        템플릿 검증

        Args:
            template_data: 검증할 템플릿 데이터

        Returns:
            검증 결과
        """
        return self.validator.validate_template(template_data)

    def get_statistics(self) -> Dict[str, Any]:
        """
        템플릿 통계 조회

        Returns:
            통계 정보
        """
        try:
            return self.storage.get_template_statistics()
        except Exception as e:
            logger.error(f"Error getting template statistics: {str(e)}")
            return {}

    def increment_usage(self, template_id: str) -> bool:
        """
        템플릿 사용 횟수 증가

        Args:
            template_id: 템플릿 ID

        Returns:
            성공 여부
        """
        try:
            return self.storage.increment_usage_count(template_id)
        except Exception as e:
            logger.error(f"Error incrementing usage for template {template_id}: {str(e)}")
            return False

    def update_accuracy(self, template_id: str, accuracy: float) -> bool:
        """
        템플릿 정확도 업데이트

        Args:
            template_id: 템플릿 ID
            accuracy: 정확도 (0.0 ~ 1.0)

        Returns:
            성공 여부
        """
        try:
            if not 0.0 <= accuracy <= 1.0:
                logger.warning(f"Invalid accuracy value: {accuracy}")
                return False

            return self.storage.update_accuracy_rate(template_id, accuracy)
        except Exception as e:
            logger.error(f"Error updating accuracy for template {template_id}: {str(e)}")
            return False

    def search_templates(self, query: str) -> List[TemplateResponse]:
        """
        템플릿 검색

        Args:
            query: 검색 쿼리

        Returns:
            검색 결과 템플릿 목록
        """
        try:
            all_templates = self.storage.list_templates()
            matching_templates = []

            query_lower = query.lower()

            for template_summary in all_templates:
                # 이름, 설명, 문서 타입에서 검색
                if (query_lower in template_summary.get('name', '').lower() or
                    query_lower in template_summary.get('document_type', '').lower()):

                    template_data = self.storage.get_template(template_summary['template_id'])
                    if template_data:
                        description = template_data.get('description', '')
                        if query_lower in description.lower():
                            matching_templates.append(self._convert_to_response(template_data))
                        elif template_data not in [self._convert_to_response(t) for t in matching_templates]:
                            matching_templates.append(self._convert_to_response(template_data))

            return matching_templates

        except Exception as e:
            logger.error(f"Error searching templates: {str(e)}")
            return []

    def duplicate_template(self, template_id: str, new_name: str, author: str = "system") -> Tuple[bool, str, Optional[str]]:
        """
        템플릿 복제

        Args:
            template_id: 복제할 템플릿 ID
            new_name: 새 템플릿 이름
            author: 생성자

        Returns:
            (성공여부, 메시지, 새_템플릿ID)
        """
        try:
            # 원본 템플릿 조회
            original_template = self.storage.get_template(template_id)
            if not original_template:
                return False, f"원본 템플릿을 찾을 수 없습니다: {template_id}", None

            # 새 이름 중복 확인
            existing_templates = self.storage.list_templates()
            existing_names = [t['name'] for t in existing_templates]

            if new_name in existing_names:
                return False, f"이미 존재하는 템플릿 이름입니다: {new_name}", None

            # 템플릿 데이터 복사
            from api.models.template import TemplateCreate, PageLayout, TemplateField, BoundingBox

            # PageLayout 복원
            page_layout_data = original_template['page_layout']
            page_layout = PageLayout(**page_layout_data)

            # TemplateField 복원
            fields = []
            for field_data in original_template['fields']:
                bbox_data = field_data['bbox']
                bbox = BoundingBox(
                    x1=bbox_data['x1'], y1=bbox_data['y1'],
                    x2=bbox_data['x2'], y2=bbox_data['y2']
                )
                field_data_copy = field_data.copy()
                field_data_copy['bbox'] = bbox
                fields.append(TemplateField(**field_data_copy))

            # 새 템플릿 생성 데이터
            new_template_data = TemplateCreate(
                name=new_name,
                description=f"{original_template.get('description', '')} (복제본)",
                document_type=original_template['document_type'],
                category=original_template['category'],
                language=original_template['language'],
                confidence_threshold=original_template['confidence_threshold'],
                page_layout=page_layout,
                fields=fields
            )

            # 새 템플릿 생성
            return self.create_template(new_template_data, author)

        except Exception as e:
            error_msg = f"템플릿 복제 중 오류 발생: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None

    def _convert_to_response(self, template_data: Dict[str, Any]) -> TemplateResponse:
        """템플릿 데이터를 응답 모델로 변환"""
        from api.models.template import (
            PageLayout, TemplateField, BoundingBox, FieldValidation,
            MatchingRule, PreprocessingConfig
        )

        # PageLayout 변환
        page_layout_data = template_data['page_layout']
        page_layout = PageLayout(**page_layout_data)

        # TemplateField 변환
        fields = []
        for field_data in template_data['fields']:
            # BoundingBox 변환
            bbox_data = field_data['bbox']
            bbox = BoundingBox(
                x1=bbox_data['x1'], y1=bbox_data['y1'],
                x2=bbox_data['x2'], y2=bbox_data['y2']
            )

            # FieldValidation 변환
            validation = None
            if field_data.get('validation'):
                validation = FieldValidation(**field_data['validation'])

            field_data_copy = field_data.copy()
            field_data_copy['bbox'] = bbox
            field_data_copy['validation'] = validation

            fields.append(TemplateField(**field_data_copy))

        # 선택적 필드들 변환
        matching_rules = None
        if template_data.get('matching_rules'):
            matching_rules = MatchingRule(**template_data['matching_rules'])

        preprocessing = None
        if template_data.get('preprocessing'):
            preprocessing = PreprocessingConfig(**template_data['preprocessing'])

        return TemplateResponse(
            template_id=template_data['template_id'],
            name=template_data['name'],
            description=template_data.get('description'),
            document_type=template_data['document_type'],
            category=template_data['category'],
            version=template_data['version'],
            language=template_data['language'],
            confidence_threshold=template_data['confidence_threshold'],
            page_layout=page_layout,
            fields=fields,
            matching_rules=matching_rules,
            preprocessing=preprocessing,
            created_at=datetime.fromisoformat(template_data['created_at']),
            updated_at=datetime.fromisoformat(template_data['updated_at']),
            author=template_data['author'],
            status=template_data['status'],
            usage_count=template_data.get('usage_count', 0),
            accuracy_rate=template_data.get('accuracy_rate', 0.0)
        )
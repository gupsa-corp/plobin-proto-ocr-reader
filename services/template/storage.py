"""
Template storage service.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import shutil

from api.models.template import TemplateCreate, TemplateResponse, DocumentCategory


class TemplateStorage:
    """템플릿 저장 관리 서비스"""

    def __init__(self):
        self.base_path = Path("templates")
        self.metadata_path = self.base_path / "metadata"
        self.definitions_path = self.base_path / "definitions"
        self.samples_path = self.base_path / "samples"
        self.visualizations_path = self.base_path / "visualizations"

        self.registry_file = self.metadata_path / "template_registry.json"
        self.categories_file = self.metadata_path / "categories.json"

        # 디렉토리 생성 확인
        for path in [self.metadata_path, self.definitions_path,
                    self.samples_path, self.visualizations_path]:
            path.mkdir(parents=True, exist_ok=True)

    def save_template(self, template_data: TemplateCreate, author: str = "system") -> str:
        """
        새 템플릿 저장

        Args:
            template_data: 템플릿 데이터
            author: 생성자

        Returns:
            생성된 템플릿 ID
        """
        # 고유한 템플릿 ID 생성
        template_id = self._generate_template_id(template_data.name, template_data.document_type)

        # 템플릿 정의 파일 생성
        template_definition = self._create_template_definition(
            template_id, template_data, author
        )

        # 파일 저장
        definition_file = self.definitions_path / f"{template_id}.json"
        with open(definition_file, 'w', encoding='utf-8') as f:
            json.dump(template_definition, f, ensure_ascii=False, indent=2, default=str)

        # 레지스트리 업데이트
        self._update_registry(template_id, template_definition)

        # 샘플 디렉토리 생성
        sample_dir = self.samples_path / template_id
        sample_dir.mkdir(exist_ok=True)

        return template_id

    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        템플릿 조회

        Args:
            template_id: 템플릿 ID

        Returns:
            템플릿 데이터 또는 None
        """
        definition_file = self.definitions_path / f"{template_id}.json"

        if not definition_file.exists():
            return None

        try:
            with open(definition_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None

    def update_template(self, template_id: str, updates: Dict[str, Any]) -> bool:
        """
        템플릿 업데이트

        Args:
            template_id: 템플릿 ID
            updates: 업데이트할 데이터

        Returns:
            성공 여부
        """
        template_data = self.get_template(template_id)
        if not template_data:
            return False

        # 업데이트 적용
        template_data.update(updates)
        template_data['updated_at'] = datetime.now().isoformat()
        template_data['version'] = self._increment_version(template_data.get('version', '1.0'))

        # 파일 저장
        definition_file = self.definitions_path / f"{template_id}.json"
        with open(definition_file, 'w', encoding='utf-8') as f:
            json.dump(template_data, f, ensure_ascii=False, indent=2, default=str)

        # 레지스트리 업데이트
        self._update_registry(template_id, template_data)

        return True

    def delete_template(self, template_id: str) -> bool:
        """
        템플릿 삭제

        Args:
            template_id: 템플릿 ID

        Returns:
            성공 여부
        """
        definition_file = self.definitions_path / f"{template_id}.json"
        sample_dir = self.samples_path / template_id

        # 파일들 삭제
        try:
            if definition_file.exists():
                definition_file.unlink()

            if sample_dir.exists():
                shutil.rmtree(sample_dir)

            # 시각화 이미지 삭제
            viz_files = list(self.visualizations_path.glob(f"{template_id}_*.png"))
            for viz_file in viz_files:
                viz_file.unlink()

            # 레지스트리에서 제거
            self._remove_from_registry(template_id)

            return True
        except Exception:
            return False

    def list_templates(self,
                      category: Optional[str] = None,
                      document_type: Optional[str] = None,
                      status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        템플릿 목록 조회

        Args:
            category: 카테고리 필터
            document_type: 문서 타입 필터
            status: 상태 필터

        Returns:
            템플릿 목록
        """
        registry = self._load_registry()
        templates = registry.get('templates', [])

        # 필터 적용
        if category:
            templates = [t for t in templates if t.get('category') == category]
        if document_type:
            templates = [t for t in templates if t.get('document_type') == document_type]
        if status:
            templates = [t for t in templates if t.get('status') == status]

        return templates

    def get_template_statistics(self) -> Dict[str, Any]:
        """
        템플릿 통계 조회

        Returns:
            통계 정보
        """
        registry = self._load_registry()
        return registry.get('statistics', {})

    def increment_usage_count(self, template_id: str) -> bool:
        """
        템플릿 사용 횟수 증가

        Args:
            template_id: 템플릿 ID

        Returns:
            성공 여부
        """
        template_data = self.get_template(template_id)
        if not template_data:
            return False

        template_data['usage_count'] = template_data.get('usage_count', 0) + 1
        template_data['last_used'] = datetime.now().isoformat()

        return self.update_template(template_id, template_data)

    def update_accuracy_rate(self, template_id: str, accuracy: float) -> bool:
        """
        템플릿 정확도 업데이트

        Args:
            template_id: 템플릿 ID
            accuracy: 정확도 (0.0 ~ 1.0)

        Returns:
            성공 여부
        """
        template_data = self.get_template(template_id)
        if not template_data:
            return False

        # 가중 평균으로 정확도 업데이트
        current_accuracy = template_data.get('accuracy_rate', 0.0)
        usage_count = template_data.get('usage_count', 0)

        if usage_count > 0:
            new_accuracy = (current_accuracy * usage_count + accuracy) / (usage_count + 1)
        else:
            new_accuracy = accuracy

        template_data['accuracy_rate'] = round(new_accuracy, 4)

        return self.update_template(template_id, template_data)

    def save_sample_image(self, template_id: str, image_data: bytes, filename: str) -> str:
        """
        샘플 이미지 저장

        Args:
            template_id: 템플릿 ID
            image_data: 이미지 데이터
            filename: 파일명

        Returns:
            저장된 파일 경로
        """
        sample_dir = self.samples_path / template_id
        sample_dir.mkdir(exist_ok=True)

        file_path = sample_dir / filename
        with open(file_path, 'wb') as f:
            f.write(image_data)

        return str(file_path)

    def get_sample_images(self, template_id: str) -> List[str]:
        """
        샘플 이미지 목록 조회

        Args:
            template_id: 템플릿 ID

        Returns:
            이미지 파일 경로 목록
        """
        sample_dir = self.samples_path / template_id
        if not sample_dir.exists():
            return []

        image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']
        image_files = []

        for ext in image_extensions:
            image_files.extend(sample_dir.glob(f"*{ext}"))

        return [str(f) for f in sorted(image_files)]

    def _generate_template_id(self, name: str, document_type: str) -> str:
        """템플릿 ID 생성"""
        # 이름과 문서 타입을 기반으로 ID 생성
        clean_name = ''.join(c for c in name if c.isalnum() or c in '_-').lower()
        clean_type = ''.join(c for c in document_type if c.isalnum() or c in '_-').lower()

        base_id = f"{clean_type}_{clean_name}"

        # 중복 확인 및 번호 추가
        counter = 1
        template_id = f"{base_id}_{counter:03d}"

        while (self.definitions_path / f"{template_id}.json").exists():
            counter += 1
            template_id = f"{base_id}_{counter:03d}"

        return template_id

    def _create_template_definition(self, template_id: str,
                                  template_data: TemplateCreate,
                                  author: str) -> Dict[str, Any]:
        """템플릿 정의 딕셔너리 생성"""
        now = datetime.now()

        definition = {
            "template_id": template_id,
            "name": template_data.name,
            "description": template_data.description,
            "document_type": template_data.document_type,
            "category": template_data.category.value,
            "version": "1.0",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "author": author,
            "language": template_data.language,
            "confidence_threshold": template_data.confidence_threshold,
            "page_layout": template_data.page_layout.dict(),
            "fields": [field.dict() for field in template_data.fields],
            "matching_rules": template_data.matching_rules.dict() if template_data.matching_rules else None,
            "preprocessing": template_data.preprocessing.dict() if template_data.preprocessing else None,
            "status": "active",
            "usage_count": 0,
            "accuracy_rate": 0.0,
            "last_used": None
        }

        return definition

    def _load_registry(self) -> Dict[str, Any]:
        """레지스트리 파일 로드"""
        if not self.registry_file.exists():
            return {"templates": [], "statistics": {"total_templates": 0, "active_templates": 0, "categories": {}}}

        try:
            with open(self.registry_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {"templates": [], "statistics": {"total_templates": 0, "active_templates": 0, "categories": {}}}

    def _save_registry(self, registry: Dict[str, Any]):
        """레지스트리 파일 저장"""
        registry['last_updated'] = datetime.now().isoformat()

        with open(self.registry_file, 'w', encoding='utf-8') as f:
            json.dump(registry, f, ensure_ascii=False, indent=2, default=str)

    def _update_registry(self, template_id: str, template_data: Dict[str, Any]):
        """레지스트리 업데이트"""
        registry = self._load_registry()

        # 기존 템플릿 찾기
        templates = registry.get('templates', [])
        existing_idx = None
        for i, template in enumerate(templates):
            if template['template_id'] == template_id:
                existing_idx = i
                break

        # 템플릿 요약 정보 생성
        template_summary = {
            "template_id": template_id,
            "name": template_data['name'],
            "category": template_data['category'],
            "document_type": template_data['document_type'],
            "version": template_data['version'],
            "file_path": f"definitions/{template_id}.json",
            "preview_path": f"visualizations/{template_id}_preview.png",
            "sample_count": len(self.get_sample_images(template_id)),
            "usage_count": template_data.get('usage_count', 0),
            "accuracy_rate": template_data.get('accuracy_rate', 0.0),
            "created_at": template_data['created_at'],
            "last_used": template_data.get('last_used'),
            "status": template_data.get('status', 'active')
        }

        # 업데이트 또는 추가
        if existing_idx is not None:
            templates[existing_idx] = template_summary
        else:
            templates.append(template_summary)

        # 통계 업데이트
        stats = self._calculate_statistics(templates)
        registry['templates'] = templates
        registry['statistics'] = stats

        self._save_registry(registry)

    def _remove_from_registry(self, template_id: str):
        """레지스트리에서 템플릿 제거"""
        registry = self._load_registry()
        templates = registry.get('templates', [])

        # 템플릿 제거
        templates = [t for t in templates if t['template_id'] != template_id]

        # 통계 업데이트
        stats = self._calculate_statistics(templates)
        registry['templates'] = templates
        registry['statistics'] = stats

        self._save_registry(registry)

    def _calculate_statistics(self, templates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """통계 계산"""
        total_templates = len(templates)
        active_templates = len([t for t in templates if t.get('status') == 'active'])

        # 카테고리별 집계
        categories = {}
        for template in templates:
            category = template.get('category', 'unknown')
            categories[category] = categories.get(category, 0) + 1

        return {
            "total_templates": total_templates,
            "active_templates": active_templates,
            "categories": categories
        }

    def _increment_version(self, current_version: str) -> str:
        """버전 번호 증가"""
        try:
            parts = current_version.split('.')
            if len(parts) >= 2:
                minor = int(parts[1]) + 1
                return f"{parts[0]}.{minor}"
            else:
                return "1.1"
        except:
            return "1.1"
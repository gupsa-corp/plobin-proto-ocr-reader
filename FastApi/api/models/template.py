"""
Pydantic models for template management API.
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class FieldType(str, Enum):
    """지원하는 필드 타입들"""
    TEXT = "text"
    NUMBER = "number"
    CURRENCY = "currency"
    DATE = "date"
    EMAIL = "email"
    PHONE = "phone"
    TABLE = "table"
    CHECKBOX = "checkbox"


class DocumentCategory(str, Enum):
    """문서 카테고리"""
    FINANCIAL_DOCUMENT = "financial_document"
    GOVERNMENT_FORM = "government_form"
    BUSINESS_DOCUMENT = "business_document"
    MEDICAL_RECORD = "medical_record"
    IDENTITY_DOCUMENT = "identity_document"


class BoundingBox(BaseModel):
    """바운딩 박스 좌표"""
    x1: float = Field(..., description="좌상단 X 좌표")
    y1: float = Field(..., description="좌상단 Y 좌표")
    x2: float = Field(..., description="우하단 X 좌표")
    y2: float = Field(..., description="우하단 Y 좌표")

    @validator('x2')
    def x2_must_be_greater_than_x1(cls, v, values):
        if 'x1' in values and v <= values['x1']:
            raise ValueError('x2 must be greater than x1')
        return v

    @validator('y2')
    def y2_must_be_greater_than_y1(cls, v, values):
        if 'y1' in values and v <= values['y1']:
            raise ValueError('y2 must be greater than y1')
        return v


class FieldValidation(BaseModel):
    """필드 검증 규칙"""
    regex: Optional[str] = None
    max_length: Optional[int] = None
    min_length: Optional[int] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    currency_code: Optional[str] = None
    date_format: Optional[str] = None
    required: bool = True


class TableColumn(BaseModel):
    """테이블 컬럼 정의"""
    name: str
    type: FieldType
    validation: Optional[FieldValidation] = None


class TemplateField(BaseModel):
    """템플릿 필드 정의"""
    field_id: str = Field(..., description="필드 고유 ID")
    name: str = Field(..., description="필드 표시명")
    type: FieldType = Field(..., description="필드 타입")
    required: bool = Field(default=True, description="필수 필드 여부")
    bbox: BoundingBox = Field(..., description="바운딩 박스 좌표")
    validation: Optional[FieldValidation] = Field(None, description="검증 규칙")
    extraction_hint: Optional[str] = Field(None, description="추출 힌트")
    table_structure: Optional[Dict[str, List[TableColumn]]] = Field(None, description="테이블 구조 (table 타입인 경우)")


class PageLayout(BaseModel):
    """페이지 레이아웃 정보"""
    width: int = Field(..., description="페이지 너비 (픽셀)")
    height: int = Field(..., description="페이지 높이 (픽셀)")
    unit: str = Field(default="pixels", description="단위")
    orientation: str = Field(default="portrait", description="방향 (portrait/landscape)")


class MatchingRule(BaseModel):
    """템플릿 매칭 규칙"""
    key_indicators: List[Dict[str, Union[str, float]]] = Field(default=[], description="키 지시어들")
    layout_similarity_threshold: float = Field(default=0.75, description="레이아웃 유사도 임계값")
    text_similarity_threshold: float = Field(default=0.6, description="텍스트 유사도 임계값")


class PreprocessingConfig(BaseModel):
    """전처리 설정"""
    auto_rotate: bool = Field(default=True, description="자동 회전")
    denoise: bool = Field(default=True, description="노이즈 제거")
    enhance_contrast: bool = Field(default=True, description="대비 향상")
    deskew: bool = Field(default=True, description="기울기 보정")


class TemplateCreate(BaseModel):
    """템플릿 생성 요청"""
    name: str = Field(..., description="템플릿 이름")
    description: Optional[str] = Field(None, description="템플릿 설명")
    document_type: str = Field(..., description="문서 타입")
    category: DocumentCategory = Field(..., description="문서 카테고리")
    language: str = Field(default="ko", description="언어")
    confidence_threshold: float = Field(default=0.85, description="신뢰도 임계값")
    page_layout: PageLayout = Field(..., description="페이지 레이아웃")
    fields: List[TemplateField] = Field(..., description="템플릿 필드들")
    matching_rules: Optional[MatchingRule] = Field(None, description="매칭 규칙")
    preprocessing: Optional[PreprocessingConfig] = Field(None, description="전처리 설정")


class TemplateUpdate(BaseModel):
    """템플릿 수정 요청"""
    name: Optional[str] = None
    description: Optional[str] = None
    confidence_threshold: Optional[float] = None
    fields: Optional[List[TemplateField]] = None
    matching_rules: Optional[MatchingRule] = None
    preprocessing: Optional[PreprocessingConfig] = None


class TemplateResponse(BaseModel):
    """템플릿 응답"""
    template_id: str
    name: str
    description: Optional[str]
    document_type: str
    category: DocumentCategory
    version: str
    language: str
    confidence_threshold: float
    page_layout: PageLayout
    fields: List[TemplateField]
    matching_rules: Optional[MatchingRule]
    preprocessing: Optional[PreprocessingConfig]
    created_at: datetime
    updated_at: datetime
    author: str
    status: str
    usage_count: int = 0
    accuracy_rate: float = 0.0


class TemplateListResponse(BaseModel):
    """템플릿 목록 응답"""
    templates: List[TemplateResponse]
    total: int
    page: int
    limit: int


class TemplateMatchResult(BaseModel):
    """템플릿 매칭 결과"""
    template_id: str
    template_name: str
    confidence_score: float
    matched_fields: int
    total_fields: int
    processing_time: float


class TemplateValidationResult(BaseModel):
    """템플릿 검증 결과"""
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    field_validation_results: Dict[str, Dict[str, Any]] = {}


class ExtractedData(BaseModel):
    """템플릿 기반 추출 데이터"""
    template_id: str
    template_name: str
    confidence_score: float
    extracted_fields: Dict[str, Any]
    field_confidences: Dict[str, float]
    processing_time: float
    validation_errors: List[str] = []
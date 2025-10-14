"""
LLM 분석 API를 위한 Pydantic 모델들
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class LLMModelEnum(str, Enum):
    """사용 가능한 LLM 모델"""
    BOTO = "boto"  # Qwen3-Omni-30B-A3B-Instruct (로컬 LLM)


class SectionTypeEnum(str, Enum):
    """섹션 유형"""
    GENERAL = "general"
    INVOICE = "invoice"
    RECEIPT = "receipt"
    CONTRACT = "contract"
    TABLE = "table"
    HEADER = "header"
    FOOTER = "footer"


class SectionConfig(BaseModel):
    """섹션별 분석 설정"""
    section_index: int = Field(..., description="섹션 인덱스")
    section_type: SectionTypeEnum = Field(SectionTypeEnum.GENERAL, description="섹션 유형")
    custom_prompt: Optional[str] = Field(None, description="사용자 정의 분석 프롬프트")
    extract_fields: Optional[List[str]] = Field(None, description="추출할 특정 필드 목록")


class SectionAnalysisRequest(BaseModel):
    """개별 섹션 분석 요청"""
    text: str = Field(..., description="분석할 텍스트")
    section_type: SectionTypeEnum = Field(SectionTypeEnum.GENERAL, description="섹션 유형")
    custom_prompt: Optional[str] = Field(None, description="사용자 정의 분석 프롬프트")
    model: LLMModelEnum = Field(LLMModelEnum.BOTO, description="사용할 LLM 모델")
    temperature: float = Field(0.1, ge=0.0, le=2.0, description="창의성 수준")
    extract_fields: Optional[List[str]] = Field(None, description="추출할 특정 필드 목록")


class AnalysisConfigRequest(BaseModel):
    """문서 분석 설정"""
    model: LLMModelEnum = Field(LLMModelEnum.BOTO, description="사용할 LLM 모델")
    temperature: float = Field(0.1, ge=0.0, le=2.0, description="창의성 수준")
    section_configs: Optional[List[SectionConfig]] = Field(None, description="섹션별 분석 설정")
    auto_section_detection: bool = Field(True, description="자동 섹션 감지 여부")
    include_confidence: bool = Field(True, description="신뢰도 점수 포함 여부")


class DocumentAnalysisRequest(BaseModel):
    """문서 분석 요청"""
    request_id: str = Field(..., description="처리 요청 ID")
    page_number: int = Field(..., ge=1, description="페이지 번호")
    config: Optional[AnalysisConfigRequest] = Field(None, description="분석 설정")


class SectionAnalysisResponse(BaseModel):
    """섹션 분석 응답"""
    success: bool = Field(..., description="분석 성공 여부")
    section_id: str = Field(..., description="섹션 고유 ID")
    section_type: str = Field(..., description="섹션 유형")
    original_text: str = Field(..., description="원본 텍스트")
    analyzed_content: str = Field(..., description="분석 결과 내용")
    extracted_data: Dict[str, Any] = Field(..., description="추출된 구조화 데이터")
    confidence_score: Optional[float] = Field(None, description="분석 신뢰도 점수")
    model_used: Optional[str] = Field(None, description="사용된 LLM 모델")
    analysis_timestamp: str = Field(..., description="분석 수행 시간")
    processing_time: Optional[float] = Field(None, description="처리 시간 (초)")
    error_message: Optional[str] = Field(None, description="오류 메시지")


class DocumentAnalysisResponse(BaseModel):
    """문서 분석 응답"""
    success: bool = Field(..., description="분석 성공 여부")
    request_id: str = Field(..., description="처리 요청 ID")
    page_number: int = Field(..., description="페이지 번호")
    total_sections: int = Field(..., description="총 섹션 수")
    sections: List[SectionAnalysisResponse] = Field(..., description="섹션별 분석 결과")
    summary: Dict[str, Any] = Field(..., description="전체 문서 요약")
    processing_time: float = Field(..., description="전체 처리 시간 (초)")
    analysis_timestamp: str = Field(..., description="분석 수행 시간")
    analysis_file_path: str = Field(..., description="분석 결과 파일 경로")


class DocumentAnalysisSummary(BaseModel):
    """문서 분석 요약"""
    request_id: str = Field(..., description="처리 요청 ID")
    total_pages: int = Field(..., description="총 페이지 수")
    analyzed_pages: int = Field(..., description="분석된 페이지 수")
    total_sections: int = Field(..., description="총 섹션 수")
    total_processing_time: float = Field(..., description="전체 처리 시간 (초)")
    pages: List[Dict[str, Any]] = Field(..., description="페이지별 분석 정보")
    summary_timestamp: str = Field(..., description="요약 생성 시간")


class LLMModelInfo(BaseModel):
    """LLM 모델 정보"""
    model_id: str = Field(..., description="모델 ID")
    name: str = Field(..., description="모델 이름")
    description: str = Field(..., description="모델 설명")
    max_tokens: Optional[int] = Field(None, description="최대 토큰 수")
    cost_per_token: Optional[float] = Field(None, description="토큰당 비용")


class LLMModelsResponse(BaseModel):
    """사용 가능한 LLM 모델 목록 응답"""
    success: bool = Field(..., description="요청 성공 여부")
    models: List[LLMModelInfo] = Field(..., description="사용 가능한 모델 목록")


class AnalysisHealthResponse(BaseModel):
    """분석 서비스 상태 응답"""
    success: bool = Field(..., description="상태 확인 성공 여부")
    status: str = Field(..., description="서비스 상태 (healthy/unhealthy)")
    llm_connection: str = Field(..., description="LLM 연결 상태")
    test_response: Optional[str] = Field(None, description="테스트 응답 내용")
    error: Optional[str] = Field(None, description="오류 메시지")
    timestamp: str = Field(..., description="상태 확인 시간")


class AnalysisStatsResponse(BaseModel):
    """분석 통계 응답"""
    success: bool = Field(..., description="요청 성공 여부")
    total_requests: int = Field(..., description="총 분석 요청 수")
    total_pages: int = Field(..., description="총 분석 페이지 수")
    total_sections: int = Field(..., description="총 분석 섹션 수")
    average_processing_time: float = Field(..., description="평균 처리 시간 (초)")
    model_usage: Dict[str, int] = Field(..., description="모델별 사용 횟수")
    section_type_distribution: Dict[str, int] = Field(..., description="섹션 유형별 분포")
    success_rate: float = Field(..., description="분석 성공률")
    timestamp: str = Field(..., description="통계 생성 시간")


class BulkAnalysisRequest(BaseModel):
    """일괄 분석 요청"""
    request_ids: List[str] = Field(..., description="분석할 요청 ID 목록")
    config: Optional[AnalysisConfigRequest] = Field(None, description="공통 분석 설정")
    parallel_processing: bool = Field(True, description="병렬 처리 여부")
    max_concurrent: int = Field(3, ge=1, le=10, description="최대 동시 처리 수")


class BulkAnalysisResponse(BaseModel):
    """일괄 분석 응답"""
    success: bool = Field(..., description="일괄 분석 성공 여부")
    total_requests: int = Field(..., description="총 요청 수")
    successful_requests: int = Field(..., description="성공한 요청 수")
    failed_requests: int = Field(..., description="실패한 요청 수")
    results: List[Dict[str, Any]] = Field(..., description="요청별 분석 결과")
    total_processing_time: float = Field(..., description="전체 처리 시간 (초)")
    timestamp: str = Field(..., description="처리 완료 시간")


class AnalysisExportRequest(BaseModel):
    """분석 결과 내보내기 요청"""
    request_id: str = Field(..., description="처리 요청 ID")
    export_format: str = Field("json", description="내보내기 형식 (json, csv, xlsx)")
    include_sections: bool = Field(True, description="섹션별 상세 내용 포함 여부")
    include_original_text: bool = Field(False, description="원본 텍스트 포함 여부")
    custom_fields: Optional[List[str]] = Field(None, description="사용자 정의 내보내기 필드")


# 통합 OCR + LLM 분석 모델들
class IntegratedAnalysisConfig(BaseModel):
    """통합 분석 설정"""
    perform_llm_analysis: bool = Field(True, description="LLM 분석 수행 여부")
    model: LLMModelEnum = Field(LLMModelEnum.BOTO, description="사용할 LLM 모델")
    temperature: float = Field(0.1, ge=0.0, le=2.0, description="창의성 수준")
    section_configs: Optional[List[SectionConfig]] = Field(None, description="섹션별 분석 설정")
    auto_section_detection: bool = Field(True, description="자동 섹션 감지 여부")
    document_type: Optional[str] = Field(None, description="문서 유형 힌트 (invoice, receipt, contract 등)")
    custom_analysis_prompt: Optional[str] = Field(None, description="전체 문서 분석용 사용자 정의 프롬프트")


class PageIntegratedResult(BaseModel):
    """페이지별 통합 결과"""
    page_number: int = Field(..., description="페이지 번호")

    # OCR 결과
    ocr_confidence: float = Field(..., description="OCR 신뢰도")
    text_blocks_count: int = Field(..., description="텍스트 블록 수")
    extracted_text: str = Field(..., description="추출된 전체 텍스트")

    # LLM 분석 결과
    llm_analysis: Optional[Dict[str, Any]] = Field(None, description="LLM 분석 결과")
    sections_analyzed: Optional[int] = Field(None, description="분석된 섹션 수")

    # 이미지 URL들
    original_image_url: str = Field(..., description="원본 이미지 URL")
    visualization_url: str = Field(..., description="시각화 이미지 URL")

    # 상세 데이터 URL들
    detailed_ocr_url: str = Field(..., description="상세 OCR 결과 URL")
    detailed_analysis_url: Optional[str] = Field(None, description="상세 분석 결과 URL")


class IntegratedProcessResult(BaseModel):
    """통합 처리 결과"""
    success: bool = Field(..., description="처리 성공 여부")
    request_id: str = Field(..., description="처리 요청 ID")
    original_filename: str = Field(..., description="원본 파일명")
    file_type: str = Field(..., description="파일 유형")
    file_size: int = Field(..., description="파일 크기 (바이트)")
    total_pages: int = Field(..., description="총 페이지 수")

    # OCR 결과
    ocr_processing_time: float = Field(..., description="OCR 처리 시간 (초)")
    ocr_confidence: float = Field(..., description="OCR 평균 신뢰도")
    total_text_blocks: int = Field(..., description="추출된 텍스트 블록 수")

    # LLM 분석 결과
    llm_analysis_performed: bool = Field(..., description="LLM 분석 수행 여부")
    llm_processing_time: Optional[float] = Field(None, description="LLM 분석 시간 (초)")
    llm_model_used: Optional[str] = Field(None, description="사용된 LLM 모델")

    # 통합 결과
    total_processing_time: float = Field(..., description="전체 처리 시간 (초)")
    pages: List[PageIntegratedResult] = Field(..., description="페이지별 통합 결과")

    # 요약 정보
    document_summary: Optional[Dict[str, Any]] = Field(None, description="전체 문서 분석 요약")
    extracted_data: Optional[Dict[str, Any]] = Field(None, description="통합 추출 데이터")

    # 접근 URL들
    processing_url: str = Field(..., description="처리 결과 조회 URL")
    analysis_url: Optional[str] = Field(None, description="분석 결과 조회 URL")

    timestamp: str = Field(..., description="처리 완료 시간")
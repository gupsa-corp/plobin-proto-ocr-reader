"""
Analysis 앱의 API 뷰 (LLM 분석)
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema


class AnalysisHealthView(APIView):
    """LLM 분석 서비스 헬스 체크"""

    @extend_schema(
        summary="LLM 분석 서비스 상태 확인",
        description="LLM 분석 서비스의 상태를 확인합니다."
    )
    def get(self, request):
        """헬스 체크"""
        return Response({
            "status": "healthy",
            "service": "llm_analysis",
            "version": "2.0.0"
        })


# TODO: 나머지 LLM 분석 엔드포인트 구현
# - POST /analysis/sections/analyze - 섹션 텍스트 분석
# - POST /analysis/documents/{request_id}/pages/{page_number}/analyze - 문서 페이지 분석
# - GET /analysis/documents/{request_id}/pages/{page_number}/analysis - 분석 결과 조회
# - GET /analysis/documents/{request_id}/analysis/summary - 전체 문서 분석 요약

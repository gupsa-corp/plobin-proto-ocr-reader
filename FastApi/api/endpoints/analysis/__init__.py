"""
분석 API 엔드포인트 모듈
"""

from fastapi import APIRouter

from .section_analysis import router as section_router
from .debug import router as debug_router
from .integrated_analysis import router as integrated_router
from .document_analysis import router as document_router
from .block_analysis import router as block_router
from .document_summary import router as summary_router

# 메인 분석 라우터
router = APIRouter(prefix="/analysis", tags=["Analysis"])

# 하위 라우터들 등록
router.include_router(section_router)
router.include_router(debug_router)
router.include_router(integrated_router)
router.include_router(document_router)
router.include_router(block_router)
router.include_router(summary_router)
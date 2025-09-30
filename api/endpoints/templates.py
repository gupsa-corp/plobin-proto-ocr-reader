"""
Template management API endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, File, UploadFile, HTTPException, Query, Depends
from fastapi.responses import FileResponse, JSONResponse

from api.models.template import (
    TemplateCreate, TemplateUpdate, TemplateResponse,
    TemplateListResponse, TemplateValidationResult,
    TemplateMatchResult, ExtractedData
)
from services.template import TemplateManager

router = APIRouter(prefix="/templates", tags=["templates"])

# 템플릿 매니저 인스턴스
template_manager = TemplateManager()


@router.post("", response_model=TemplateResponse)
async def create_template(template_data: TemplateCreate):
    """새 템플릿 생성"""
    try:
        success, message, template_id = template_manager.create_template(template_data)

        if not success:
            raise HTTPException(status_code=400, detail=message)

        # 생성된 템플릿 조회
        template = template_manager.get_template(template_id)
        if not template:
            raise HTTPException(status_code=500, detail="템플릿 생성 후 조회에 실패했습니다")

        return template

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"템플릿 생성 중 오류 발생: {str(e)}")


@router.get("", response_model=TemplateListResponse)
async def list_templates(
    category: Optional[str] = Query(None, description="카테고리 필터"),
    document_type: Optional[str] = Query(None, description="문서 타입 필터"),
    status: Optional[str] = Query(None, description="상태 필터"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수")
):
    """템플릿 목록 조회"""
    try:
        return template_manager.list_templates(
            category=category,
            document_type=document_type,
            status=status,
            page=page,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"템플릿 목록 조회 중 오류 발생: {str(e)}")


@router.get("/search", response_model=List[TemplateResponse])
async def search_templates(
    query: str = Query(..., description="검색 쿼리")
):
    """템플릿 검색"""
    try:
        if len(query.strip()) < 2:
            raise HTTPException(status_code=400, detail="검색 쿼리는 최소 2자 이상이어야 합니다")

        return template_manager.search_templates(query)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"템플릿 검색 중 오류 발생: {str(e)}")


@router.get("/statistics")
async def get_template_statistics():
    """템플릿 통계 조회"""
    try:
        return template_manager.get_statistics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 조회 중 오류 발생: {str(e)}")


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(template_id: str):
    """특정 템플릿 상세 조회"""
    try:
        template = template_manager.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail=f"템플릿을 찾을 수 없습니다: {template_id}")

        return template
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"템플릿 조회 중 오류 발생: {str(e)}")


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(template_id: str, template_data: TemplateUpdate):
    """템플릿 수정"""
    try:
        success, message = template_manager.update_template(template_id, template_data)

        if not success:
            if "찾을 수 없습니다" in message:
                raise HTTPException(status_code=404, detail=message)
            else:
                raise HTTPException(status_code=400, detail=message)

        # 업데이트된 템플릿 조회
        template = template_manager.get_template(template_id)
        if not template:
            raise HTTPException(status_code=500, detail="템플릿 업데이트 후 조회에 실패했습니다")

        return template

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"템플릿 업데이트 중 오류 발생: {str(e)}")


@router.delete("/{template_id}")
async def delete_template(template_id: str):
    """템플릿 삭제"""
    try:
        success, message = template_manager.delete_template(template_id)

        if not success:
            if "찾을 수 없습니다" in message:
                raise HTTPException(status_code=404, detail=message)
            else:
                raise HTTPException(status_code=400, detail=message)

        return {"message": message}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"템플릿 삭제 중 오류 발생: {str(e)}")


@router.post("/{template_id}/duplicate", response_model=TemplateResponse)
async def duplicate_template(
    template_id: str,
    new_name: str = Query(..., description="새 템플릿 이름")
):
    """템플릿 복제"""
    try:
        success, message, new_template_id = template_manager.duplicate_template(
            template_id, new_name
        )

        if not success:
            if "찾을 수 없습니다" in message:
                raise HTTPException(status_code=404, detail=message)
            else:
                raise HTTPException(status_code=400, detail=message)

        # 생성된 템플릿 조회
        template = template_manager.get_template(new_template_id)
        if not template:
            raise HTTPException(status_code=500, detail="템플릿 복제 후 조회에 실패했습니다")

        return template

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"템플릿 복제 중 오류 발생: {str(e)}")


@router.post("/validate", response_model=TemplateValidationResult)
async def validate_template(template_data: TemplateCreate):
    """템플릿 검증"""
    try:
        return template_manager.validate_template(template_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"템플릿 검증 중 오류 발생: {str(e)}")


@router.post("/{template_id}/match", response_model=TemplateMatchResult)
async def match_document_to_template(
    template_id: str,
    file: UploadFile = File(..., description="처리할 문서 파일")
):
    """문서를 특정 템플릿에 매칭하여 처리"""
    try:
        # 템플릿 존재 확인
        template = template_manager.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail=f"템플릿을 찾을 수 없습니다: {template_id}")

        # 파일 유효성 검증
        if not file.content_type or not any(
            file.content_type.startswith(ct) for ct in ['image/', 'application/pdf']
        ):
            raise HTTPException(
                status_code=400,
                detail="지원하지 않는 파일 형식입니다. 이미지 또는 PDF 파일만 허용됩니다."
            )

        # TODO: 실제 템플릿 매칭 로직 구현
        # 현재는 더미 응답 반환
        return TemplateMatchResult(
            template_id=template_id,
            template_name=template.name,
            confidence_score=0.85,
            matched_fields=len(template.fields),
            total_fields=len(template.fields),
            processing_time=1.2
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"템플릿 매칭 중 오류 발생: {str(e)}")


@router.post("/auto-match", response_model=TemplateMatchResult)
async def auto_match_document(
    file: UploadFile = File(..., description="처리할 문서 파일"),
    confidence_threshold: float = Query(0.7, ge=0.0, le=1.0, description="최소 신뢰도 임계값")
):
    """문서에 가장 적합한 템플릿 자동 선택하여 처리"""
    try:
        # 파일 유효성 검증
        if not file.content_type or not any(
            file.content_type.startswith(ct) for ct in ['image/', 'application/pdf']
        ):
            raise HTTPException(
                status_code=400,
                detail="지원하지 않는 파일 형식입니다. 이미지 또는 PDF 파일만 허용됩니다."
            )

        # TODO: 실제 자동 매칭 로직 구현
        # 현재는 더미 응답 반환
        templates = template_manager.list_templates()
        if not templates.templates:
            raise HTTPException(status_code=404, detail="사용 가능한 템플릿이 없습니다")

        best_template = templates.templates[0]

        return TemplateMatchResult(
            template_id=best_template.template_id,
            template_name=best_template.name,
            confidence_score=0.82,
            matched_fields=len(best_template.fields),
            total_fields=len(best_template.fields),
            processing_time=1.5
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"자동 매칭 중 오류 발생: {str(e)}")


@router.get("/{template_id}/preview")
async def get_template_preview(template_id: str):
    """템플릿 시각화 이미지 다운로드"""
    try:
        # 템플릿 존재 확인
        template = template_manager.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail=f"템플릿을 찾을 수 없습니다: {template_id}")

        # TODO: 실제 시각화 이미지 생성 로직 구현
        # 현재는 플레이스홀더 응답
        return JSONResponse(
            content={"message": f"템플릿 {template_id}의 시각화 이미지 (구현 예정)"},
            status_code=200
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시각화 이미지 조회 중 오류 발생: {str(e)}")


@router.post("/{template_id}/validate-document")
async def validate_document_with_template(
    template_id: str,
    files: List[UploadFile] = File(..., description="검증할 테스트 문서들")
):
    """테스트 문서들로 템플릿 검증"""
    try:
        # 템플릿 존재 확인
        template = template_manager.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail=f"템플릿을 찾을 수 없습니다: {template_id}")

        if len(files) > 10:
            raise HTTPException(status_code=400, detail="한 번에 최대 10개의 파일만 처리할 수 있습니다")

        # 파일 유효성 검증
        for file in files:
            if not file.content_type or not any(
                file.content_type.startswith(ct) for ct in ['image/', 'application/pdf']
            ):
                raise HTTPException(
                    status_code=400,
                    detail=f"지원하지 않는 파일 형식입니다: {file.filename}"
                )

        # TODO: 실제 템플릿 검증 로직 구현
        # 현재는 더미 응답 반환
        validation_results = []
        for i, file in enumerate(files):
            validation_results.append({
                "filename": file.filename,
                "confidence_score": 0.85 + (i * 0.02),
                "matched_fields": len(template.fields) - (i % 2),
                "total_fields": len(template.fields),
                "errors": []
            })

        return {
            "template_id": template_id,
            "template_name": template.name,
            "test_files_count": len(files),
            "average_confidence": sum(r["confidence_score"] for r in validation_results) / len(validation_results),
            "validation_results": validation_results
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"템플릿 검증 중 오류 발생: {str(e)}")


@router.post("/{template_id}/usage")
async def increment_template_usage(template_id: str):
    """템플릿 사용 횟수 증가"""
    try:
        success = template_manager.increment_usage(template_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"템플릿을 찾을 수 없습니다: {template_id}")

        return {"message": "사용 횟수가 증가되었습니다"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"사용 횟수 업데이트 중 오류 발생: {str(e)}")


@router.post("/{template_id}/accuracy")
async def update_template_accuracy(
    template_id: str,
    accuracy: float = Query(..., ge=0.0, le=1.0, description="정확도 (0.0 ~ 1.0)")
):
    """템플릿 정확도 업데이트"""
    try:
        success = template_manager.update_accuracy(template_id, accuracy)
        if not success:
            raise HTTPException(status_code=404, detail=f"템플릿을 찾을 수 없습니다: {template_id}")

        return {"message": "정확도가 업데이트되었습니다"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"정확도 업데이트 중 오류 발생: {str(e)}")
#!/usr/bin/env python3
"""
PP-OCRv5 관련 API 엔드포인트
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
import tempfile
import os

from services.ocr.version_manager import create_backup, restore_backup, list_backups, get_current_version, OCRVersion
from services.ocr.ppocrv5_initialization import get_ppocrv5_info
from services.ocr.tensorrt_acceleration import get_tensorrt_info, benchmark_tensorrt
from services.ocr import DocumentBlockExtractor

router = APIRouter()

@router.get("/ppocrv5/info")
async def get_ppocrv5_model_info():
    """PP-OCRv5 모델 정보 조회"""
    try:
        info = get_ppocrv5_info()
        return JSONResponse({
            "status": "success",
            "model_info": info,
            "available": info.get("status") == "initialized"
        })
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "error": str(e)
        }, status_code=500)

@router.post("/ppocrv5/process-image")
async def process_image_with_ppocrv5(
    file: UploadFile = File(...),
    description: Optional[str] = Form("PP-OCRv5 이미지 처리"),
    confidence_threshold: float = Form(0.5),
    use_korean_enhancement: bool = Form(True),
    preprocessing_level: str = Form("medium")
):
    """PP-OCRv5를 사용한 이미지 OCR 처리"""

    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp')):
        raise HTTPException(status_code=400, detail="지원하지 않는 이미지 형식입니다.")

    try:
        # 임시 파일 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name

        # PP-OCRv5로 OCR 처리
        extractor = DocumentBlockExtractor(
            use_gpu=True,
            lang='korean',
            use_korean_enhancement=use_korean_enhancement,
            use_ppocrv5=True  # PP-OCRv5 활성화
        )

        result = extractor.extract_blocks(
            temp_path,
            confidence_threshold=confidence_threshold,
            use_korean_enhancement=use_korean_enhancement,
            preprocessing_level=preprocessing_level
        )

        # 임시 파일 삭제
        os.unlink(temp_path)

        return JSONResponse({
            "status": "success",
            "model_version": "PP-OCRv5",
            "filename": file.filename,
            "description": description,
            "total_blocks": len(result),
            "blocks": result
        })

    except Exception as e:
        # 임시 파일 정리
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)

        raise HTTPException(status_code=500, detail=f"PP-OCRv5 처리 실패: {str(e)}")

@router.get("/version/current")
async def get_current_ocr_version():
    """현재 OCR 버전 정보 조회"""
    try:
        version_info = get_current_version()
        return JSONResponse({
            "status": "success",
            "version_info": version_info
        })
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "error": str(e)
        }, status_code=500)

@router.get("/version/backups")
async def list_ocr_backups():
    """OCR 백업 목록 조회"""
    try:
        backups = list_backups()
        return JSONResponse({
            "status": "success",
            "backups": backups,
            "total_backups": len(backups)
        })
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "error": str(e)
        }, status_code=500)

@router.post("/version/backup")
async def create_ocr_backup(
    version: str = Form(...),
    description: str = Form("")
):
    """OCR 시스템 백업 생성"""
    try:
        # 버전 검증
        try:
            ocr_version = OCRVersion(version)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"잘못된 버전: {version}")

        backup_name = create_backup(ocr_version, description)

        return JSONResponse({
            "status": "success",
            "backup_name": backup_name,
            "version": version,
            "description": description
        })
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "error": str(e)
        }, status_code=500)

@router.post("/version/restore")
async def restore_ocr_backup(
    backup_name: str = Form(...)
):
    """OCR 시스템 백업 복원"""
    try:
        success = restore_backup(backup_name)

        if success:
            return JSONResponse({
                "status": "success",
                "backup_name": backup_name,
                "message": "복원 완료"
            })
        else:
            raise HTTPException(status_code=400, detail="복원 실패")

    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "error": str(e)
        }, status_code=500)
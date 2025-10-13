#!/usr/bin/env python3
"""
TensorRT 가속화 관련 API 엔드포인트
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
import tempfile
import os
import time

from services.ocr.tensorrt_acceleration import get_tensorrt_info, benchmark_tensorrt
from services.ocr.initialization import initialize_ocr

router = APIRouter()

@router.get("/tensorrt/info")
async def get_tensorrt_acceleration_info():
    """TensorRT 가속화 정보 조회"""
    try:
        info = get_tensorrt_info()
        return JSONResponse({
            "status": "success",
            "tensorrt_info": info
        })
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "error": str(e)
        }, status_code=500)

@router.post("/tensorrt/process-image")
async def process_image_with_tensorrt(
    file: UploadFile = File(...),
    description: Optional[str] = Form("TensorRT 가속화 이미지 처리"),
    confidence_threshold: float = Form(0.5)
):
    """TensorRT 가속화를 사용한 이미지 OCR 처리"""

    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp')):
        raise HTTPException(status_code=400, detail="지원하지 않는 이미지 형식입니다.")

    try:
        # 임시 파일 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name

        start_time = time.time()

        # TensorRT 모드로 OCR 초기화
        ocr = initialize_ocr(
            use_gpu=True,
            lang='korean',
            enable_layout_analysis=True,
            use_korean_optimized=True,
            use_tensorrt=True
        )

        # OCR 처리
        result = ocr.ocr(temp_path)
        processing_time = time.time() - start_time

        # 임시 파일 삭제
        os.unlink(temp_path)

        return JSONResponse({
            "status": "success",
            "model_version": "TensorRT-Accelerated",
            "filename": file.filename,
            "description": description,
            "processing_time": round(processing_time, 3),
            "result": result if result else []
        })

    except Exception as e:
        # 임시 파일 정리
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)

        raise HTTPException(status_code=500, detail=f"TensorRT 처리 실패: {str(e)}")

@router.post("/tensorrt/benchmark")
async def benchmark_tensorrt_performance(
    file: UploadFile = File(...),
    iterations: int = Form(5, ge=1, le=20)
):
    """TensorRT 성능 벤치마크"""

    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp')):
        raise HTTPException(status_code=400, detail="지원하지 않는 이미지 형식입니다.")

    try:
        # 임시 파일 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name

        # 벤치마크 실행
        benchmark_result = benchmark_tensorrt(temp_path, iterations)

        # 임시 파일 삭제
        os.unlink(temp_path)

        return JSONResponse({
            "status": "success",
            "benchmark_result": benchmark_result,
            "filename": file.filename,
            "iterations": iterations
        })

    except Exception as e:
        # 임시 파일 정리
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)

        raise HTTPException(status_code=500, detail=f"벤치마크 실패: {str(e)}")

@router.get("/tensorrt/test")
async def test_tensorrt_availability():
    """TensorRT 사용 가능 여부 테스트"""
    try:
        from services.ocr.tensorrt_acceleration import tensorrt_manager

        # TensorRT 환경 확인
        available = tensorrt_manager._check_tensorrt_availability()

        return JSONResponse({
            "status": "success",
            "tensorrt_available": available,
            "message": "TensorRT 사용 가능" if available else "TensorRT 사용 불가능"
        })
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "error": str(e)
        }, status_code=500)
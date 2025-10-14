"""
디버그 및 상태 확인 API 엔드포인트
"""

import os
import httpx
from typing import Dict, Any
from datetime import datetime

from fastapi import APIRouter, Body, Depends
from fastapi.responses import JSONResponse

from services.llm import LLMClient, LLMModel
from .dependencies import get_llm_client

router = APIRouter()


@router.get("/models")
async def get_available_models():
    """
    사용 가능한 LLM 모델 목록 조회
    """
    return JSONResponse({
        "success": True,
        "models": [
            {
                "model_id": LLMModel.BOTO,
                "name": "Boto (Qwen3-Omni-30B)",
                "description": "로컬 LLM 모델 (기본값)"
            }
        ]
    })


@router.get("/debug/api-info")
async def get_llm_api_info():
    """
    LLM API 연결 정보 및 설정 확인
    """
    api_key = os.getenv("GUPSA_AI_API_KEY")

    return JSONResponse({
        "success": True,
        "api_config": {
            "base_url": "https://llm.gupsa.net/v1",
            "api_key_configured": bool(api_key),
            "api_key_preview": f"{api_key[:10]}..." if api_key else None,
            "endpoints": {
                "chat_completions": "/chat/completions",
                "models": "/models",
                "health": "/health"
            }
        },
        "supported_models": [model.value for model in LLMModel],
        "timestamp": datetime.now().isoformat()
    })


@router.get("/debug/test-connection")
async def test_llm_connection():
    """
    다양한 LLM API 엔드포인트 연결 테스트
    """
    results = {}

    # 기본 URL 테스트
    base_urls = [
        "https://llm.gupsa.net",
        "https://llm.gupsa.net/v1",
        "https://ai.gupsa.net/v1",  # 이전 URL
        "https://api.openai.com/v1"  # 비교용
    ]

    for base_url in base_urls:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(base_url)
                results[base_url] = {
                    "status_code": response.status_code,
                    "accessible": response.status_code < 500,
                    "content_type": response.headers.get("content-type", ""),
                    "response_size": len(response.text)
                }
        except Exception as e:
            results[base_url] = {
                "error": str(e),
                "accessible": False
            }

    # Chat completions 엔드포인트 테스트
    chat_endpoints = [
        "https://llm.gupsa.net/v1/chat/completions",
        "https://ai.gupsa.net/v1/chat/completions",  # 이전 URL
        "https://api.openai.com/v1/chat/completions"  # 비교용
    ]

    results["chat_endpoints"] = {}
    for endpoint in chat_endpoints:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # OPTIONS 요청으로 CORS 확인
                response = await client.options(endpoint)
                results["chat_endpoints"][endpoint] = {
                    "options_status": response.status_code,
                    "cors_headers": dict(response.headers)
                }
        except Exception as e:
            results["chat_endpoints"][endpoint] = {
                "error": str(e)
            }

    return JSONResponse({
        "success": True,
        "connection_tests": results,
        "timestamp": datetime.now().isoformat()
    })


@router.post("/debug/manual-request")
async def manual_llm_request(
    url: str = Body(..., description="LLM API URL"),
    method: str = Body("POST", description="HTTP 메서드"),
    headers: Dict[str, str] = Body({}, description="HTTP 헤더"),
    payload: Dict[str, Any] = Body({}, description="요청 페이로드")
):
    """
    수동 LLM API 요청 테스트
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if method.upper() == "GET":
                response = await client.get(url, headers=headers, params=payload)
            elif method.upper() == "POST":
                response = await client.post(url, headers=headers, json=payload)
            else:
                raise ValueError(f"지원하지 않는 HTTP 메서드: {method}")

            return JSONResponse({
                "success": True,
                "request": {
                    "url": url,
                    "method": method,
                    "headers": headers,
                    "payload": payload
                },
                "response": {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "content": response.text[:1000],  # 처음 1000자만
                    "content_length": len(response.text)
                },
                "timestamp": datetime.now().isoformat()
            })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e),
            "request": {
                "url": url,
                "method": method,
                "headers": headers,
                "payload": payload
            },
            "timestamp": datetime.now().isoformat()
        }, status_code=500)


@router.get("/health")
async def check_analysis_health(llm_client: LLMClient = Depends(get_llm_client)):
    """
    LLM 분석 서비스 상태 확인
    """
    try:
        # 간단한 테스트 요청으로 연결 확인
        test_response = await llm_client.analyze_text(
            text="test",
            prompt="Just respond with 'OK'",
            model=LLMModel.BOTO  # 실제 작동하는 모델 사용
        )

        return JSONResponse({
            "success": True,
            "status": "healthy",
            "llm_connection": "connected",
            "test_response": test_response[:50] if test_response else "No response",
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "status": "unhealthy",
            "llm_connection": "failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, status_code=503)
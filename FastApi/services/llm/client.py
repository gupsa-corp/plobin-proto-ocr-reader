"""
ai.gupsa.net/v1 LLM API 클라이언트
"""

import httpx
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class LLMModel(str, Enum):
    """사용 가능한 LLM 모델들"""
    BOTO = "boto"  # Qwen3-Omni-30B-A3B-Instruct (로컬 LLM)


@dataclass
class LLMRequest:
    """LLM API 요청 데이터"""
    messages: List[Dict[str, str]]
    model: str = LLMModel.BOTO
    temperature: float = 0.1
    max_tokens: Optional[int] = None
    stream: bool = False


@dataclass
class LLMResponse:
    """LLM API 응답 데이터"""
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str
    created: int


class LLMClient:
    """ai.gupsa.net/v1 LLM API 클라이언트"""

    def __init__(self, base_url: str = "https://llm.gupsa.net/v1", api_key: Optional[str] = None):
        """
        LLM 클라이언트 초기화

        Args:
            base_url: LLM API 기본 URL
            api_key: API 키 (환경변수에서 자동 로드 가능)
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.client = httpx.Client(
            timeout=httpx.Timeout(60.0),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}" if api_key else None
            } if api_key else {"Content-Type": "application/json"}
        )

    async def chat_completion(self, request: LLMRequest) -> LLMResponse:
        """
        채팅 완성 API 호출

        Args:
            request: LLM 요청 데이터

        Returns:
            LLM 응답 데이터

        Raises:
            httpx.HTTPError: API 호출 실패 시
        """
        url = f"{self.base_url}/chat/completions"

        payload = {
            "model": request.model,
            "messages": request.messages,
            "temperature": request.temperature,
            "stream": request.stream
        }

        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens

        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
            if self.api_key:
                client.headers.update({"Authorization": f"Bearer {self.api_key}"})

            response = await client.post(url, json=payload)
            response.raise_for_status()

            data = response.json()
            choice = data["choices"][0]

            return LLMResponse(
                content=choice["message"]["content"],
                model=data["model"],
                usage=data.get("usage", {}),
                finish_reason=choice["finish_reason"],
                created=data["created"]
            )

    async def analyze_text(
        self,
        text: str,
        prompt: str,
        model: str = LLMModel.BOTO,
        temperature: float = 0.1
    ) -> str:
        """
        텍스트 분석을 위한 간편한 메서드

        Args:
            text: 분석할 텍스트
            prompt: 분석 프롬프트
            model: 사용할 모델
            temperature: 창의성 수준

        Returns:
            분석 결과 텍스트
        """
        request = LLMRequest(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text}
            ],
            model=model,
            temperature=temperature
        )

        response = await self.chat_completion(request)
        return response.content

    def close(self):
        """클라이언트 연결 종료"""
        self.client.close()
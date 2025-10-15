#!/bin/bash
"""
OCR API 서버 시작 스크립트 (환경 검증 포함)
"""

# 스크립트 디렉토리로 이동
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🚀 OCR API 서버 시작 중..."
echo "프로젝트 디렉토리: $PROJECT_DIR"

# Python 환경 검증 스크립트 실행
echo ""
echo "🔍 환경 검증 실행 중..."
python3 "$SCRIPT_DIR/check_environment.py"

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ 환경 검증 실패! 서버 시작을 중단합니다."
    echo "위의 오류들을 해결한 후 다시 시도해주세요."
    exit 1
fi

echo ""
echo "✅ 환경 검증 완료! 서버를 시작합니다..."

# FastAPI 서버 시작
cd "$PROJECT_DIR/FastApi"

# 가상환경이 있다면 활성화
if [ -d "venv" ]; then
    echo "🐍 가상환경 활성화 중..."
    source venv/bin/activate
fi

# 서버 시작
echo "🌐 FastAPI 서버 시작 중..."
uvicorn api_server:app --host 0.0.0.0 --port 6003 --reload

echo "서버가 종료되었습니다."
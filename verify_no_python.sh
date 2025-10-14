#!/bin/bash
# Python 의존성 제거 검증 스크립트
# 작성일: 2025-10-14

echo "🔍 Python 의존성 제거 검증"
echo "=========================="
echo ""

# 1. Go 코드에서 Python 참조 확인
echo "1️⃣ Go 코드에서 Python 참조 검색:"
echo "--------------------------------"
PYTHON_REFS=$(grep -r "python" GenkitGo/internal GenkitGo/cmd --include="*.go" 2>/dev/null || echo "")
if [ -z "$PYTHON_REFS" ]; then
    echo "✅ Python 참조 없음"
else
    echo "❌ Python 참조 발견:"
    echo "$PYTHON_REFS"
fi
echo ""

# 2. subprocess/exec 호출 확인
echo "2️⃣ Subprocess/exec 호출 검색:"
echo "-----------------------------"
EXEC_REFS=$(grep -r "exec.Command" GenkitGo/internal GenkitGo/cmd --include="*.go" 2>/dev/null || echo "")
if [ -z "$EXEC_REFS" ]; then
    echo "✅ exec.Command 호출 없음"
else
    echo "⚠️  exec.Command 호출 발견 (확인 필요):"
    echo "$EXEC_REFS"
fi
echo ""

# 3. FastAPI 참조 확인
echo "3️⃣ FastAPI 참조 검색:"
echo "-------------------"
FASTAPI_REFS=$(grep -r "FastApi\|fastapi" GenkitGo/ --include="*.go" 2>/dev/null || echo "")
if [ -z "$FASTAPI_REFS" ]; then
    echo "✅ FastAPI 참조 없음"
else
    echo "❌ FastAPI 참조 발견:"
    echo "$FASTAPI_REFS"
fi
echo ""

# 4. Python 프로세스 확인
echo "4️⃣ 실행 중인 Python 프로세스:"
echo "----------------------------"
PYTHON_PROCS=$(pgrep -af "python.*FastApi" 2>/dev/null || echo "")
if [ -z "$PYTHON_PROCS" ]; then
    echo "✅ Python 프로세스 없음"
else
    echo "⚠️  Python 프로세스 발견:"
    echo "$PYTHON_PROCS"
fi
echo ""

# 5. Pure Go 라이브러리 사용 확인
echo "5️⃣ Pure Go 라이브러리 사용 확인:"
echo "------------------------------"
if grep -q "gosseract" GenkitGo/go.mod; then
    echo "✅ gosseract (Tesseract Go 바인딩) 사용"
fi
if grep -q "go-fitz" GenkitGo/go.mod; then
    echo "✅ go-fitz (MuPDF Go 바인딩) 사용"
fi
echo ""

# 6. 서버 프로세스 확인
echo "6️⃣ GenkitGo 서버 상태:"
echo "--------------------"
if pgrep -f "bin/server" > /dev/null; then
    echo "✅ Pure Go 서버 실행 중"
    ps aux | grep "bin/server" | grep -v grep
else
    echo "⚠️  서버 실행 안됨"
fi
echo ""

# 7. 최종 결론
echo "=========================="
echo "📊 검증 결과:"
echo "=========================="
ALL_CLEAR=true

if [ -n "$PYTHON_REFS" ]; then
    echo "❌ Python 참조 발견"
    ALL_CLEAR=false
else
    echo "✅ Python 참조 없음"
fi

if [ -n "$FASTAPI_REFS" ]; then
    echo "❌ FastAPI 참조 발견"
    ALL_CLEAR=false
else
    echo "✅ FastAPI 참조 없음"
fi

if [ -n "$PYTHON_PROCS" ]; then
    echo "⚠️  Python 프로세스 실행 중"
else
    echo "✅ Python 프로세스 없음"
fi

echo ""
if [ "$ALL_CLEAR" = true ]; then
    echo "🎉 모든 검증 통과! FastAPI 폴더 삭제 가능합니다."
    echo ""
    echo "삭제 명령:"
    echo "  rm -rf FastApi/"
else
    echo "⚠️  일부 Python 의존성이 남아있습니다."
fi

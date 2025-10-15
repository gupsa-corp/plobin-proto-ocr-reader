#!/bin/bash
"""
OCR API 서버 중지 스크립트
"""

echo "🛑 OCR API 서버 중지 중..."

# uvicorn 프로세스 찾기 및 중지
UVICORN_PIDS=$(pgrep -f "uvicorn.*api_server")

if [ -z "$UVICORN_PIDS" ]; then
    echo "❌ 실행 중인 OCR API 서버를 찾을 수 없습니다."
    exit 1
fi

echo "📋 발견된 서버 프로세스:"
ps -p $UVICORN_PIDS -o pid,ppid,cmd

echo ""
echo "🔪 서버 프로세스 종료 중..."

# SIGTERM으로 정상 종료 시도
for pid in $UVICORN_PIDS; do
    echo "  → PID $pid 종료 중..."
    kill -TERM $pid
done

# 3초 대기 후 강제 종료 확인
sleep 3

# 아직 살아있는 프로세스 확인
REMAINING_PIDS=$(pgrep -f "uvicorn.*api_server")

if [ ! -z "$REMAINING_PIDS" ]; then
    echo "⚠️  일부 프로세스가 아직 실행 중입니다. 강제 종료합니다..."
    for pid in $REMAINING_PIDS; do
        echo "  → PID $pid 강제 종료 중..."
        kill -KILL $pid
    done
    sleep 1
fi

# 최종 확인
FINAL_CHECK=$(pgrep -f "uvicorn.*api_server")
if [ -z "$FINAL_CHECK" ]; then
    echo "✅ OCR API 서버가 성공적으로 중지되었습니다."
else
    echo "❌ 서버 중지에 실패했습니다. 수동으로 확인해주세요."
    echo "실행 중인 프로세스:"
    ps -p $FINAL_CHECK -o pid,ppid,cmd
    exit 1
fi
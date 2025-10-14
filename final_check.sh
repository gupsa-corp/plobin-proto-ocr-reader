#!/bin/bash
# GenkitGo 타임아웃 설정 확인 스크립트
# 작성일: 2025-10-14

echo "🔍 GenkitGo 타임아웃 설정 확인"
echo "================================"
echo ""

MAIN_GO="GenkitGo/cmd/server/main.go"

if [ ! -f "$MAIN_GO" ]; then
    echo "❌ 오류: $MAIN_GO 파일을 찾을 수 없습니다."
    exit 1
fi

echo "📄 파일: $MAIN_GO"
echo ""

# 현재 설정 확인
echo "⚙️  현재 타임아웃 설정:"
echo "-------------------"
grep -n "middleware.Timeout" "$MAIN_GO" | head -1
grep -n "ReadTimeout:" "$MAIN_GO" | head -1
grep -n "WriteTimeout:" "$MAIN_GO" | head -1
echo ""

# 권장 설정 표시
echo "✅ 권장 설정 (대용량 PDF 지원):"
echo "----------------------------"
echo "Line 84: r.Use(middleware.Timeout(10 * time.Minute))"
echo "Line 669: ReadTimeout:  2 * time.Minute,"
echo "Line 670: WriteTimeout: 10 * time.Minute,"
echo ""

# 현재 설정 분석
MIDDLEWARE_TIMEOUT=$(grep "middleware.Timeout" "$MAIN_GO" | grep -oE '[0-9]+ \* time\.(Second|Minute)')
READ_TIMEOUT=$(grep "ReadTimeout:" "$MAIN_GO" | grep -oE '[0-9]+ \* time\.(Second|Minute)')
WRITE_TIMEOUT=$(grep "WriteTimeout:" "$MAIN_GO" | grep -oE '[0-9]+ \* time\.(Second|Minute)')

echo "📊 설정 분석:"
echo "------------"

# 분석 결과 표시
if echo "$MIDDLEWARE_TIMEOUT" | grep -q "10 \* time.Minute"; then
    echo "✅ 미들웨어 타임아웃: 10분 (권장값)"
elif echo "$MIDDLEWARE_TIMEOUT" | grep -q "60 \* time.Second"; then
    echo "⚠️  미들웨어 타임아웃: 60초 (대용량 PDF 처리 시 부족)"
else
    echo "❓ 미들웨어 타임아웃: $MIDDLEWARE_TIMEOUT"
fi

if echo "$READ_TIMEOUT" | grep -q "2 \* time.Minute"; then
    echo "✅ ReadTimeout: 2분 (권장값)"
elif echo "$READ_TIMEOUT" | grep -q "15 \* time.Second"; then
    echo "⚠️  ReadTimeout: 15초 (대용량 PDF 처리 시 부족)"
else
    echo "❓ ReadTimeout: $READ_TIMEOUT"
fi

if echo "$WRITE_TIMEOUT" | grep -q "10 \* time.Minute"; then
    echo "✅ WriteTimeout: 10분 (권장값)"
elif echo "$WRITE_TIMEOUT" | grep -q "15 \* time.Second"; then
    echo "⚠️  WriteTimeout: 15초 (대용량 PDF 처리 시 부족)"
else
    echo "❓ WriteTimeout: $WRITE_TIMEOUT"
fi

echo ""
echo "📝 참고:"
echo "- 2MB/9페이지 PDF 처리 시간: ~3.5분"
echo "- 현재 60초 타임아웃으로는 대용량 PDF 처리 불가"
echo "- 권장 사항: 타임아웃을 10분으로 증가"
echo ""

# 테스트 파일 정보
echo "📂 테스트 파일 정보:"
echo "-----------------"
if [ -f "251014-te-arn-rfp.pdf" ]; then
    ls -lh 251014-te-arn-rfp.pdf
    echo "✅ 테스트 PDF 파일 존재"
else
    echo "❌ 테스트 PDF 파일 없음"
fi
echo ""

# 서버 실행 여부 확인
echo "🚀 서버 실행 상태:"
echo "----------------"
if lsof -i :6003 > /dev/null 2>&1; then
    echo "✅ GenkitGo 서버 실행 중 (포트 6003)"
    lsof -i :6003 | grep LISTEN
else
    echo "❌ GenkitGo 서버 미실행"
fi
echo ""

echo "================================"
echo "✅ 확인 완료"

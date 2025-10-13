# Quick Start Guide

## 빠른 시작

### 1. 환경 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일에서 GOOGLE_API_KEY 설정
# GOOGLE_API_KEY=your_actual_api_key_here
```

### 2. 의존성 설치

```bash
make deps
# 또는
go mod download
```

### 3. 서버 실행

#### 개발 모드
```bash
make dev
# 또는
go run cmd/server/main.go
```

#### 프로덕션 빌드
```bash
make build
make run
# 또는
go build -o bin/server cmd/server/main.go
./bin/server
```

서버는 `http://localhost:6003`에서 실행됩니다.

### 4. API 테스트

#### Health Check
```bash
curl http://localhost:6003/health
```

예상 응답:
```json
{
  "status": "healthy"
}
```

#### 서버 상태
```bash
curl http://localhost:6003/
```

예상 응답:
```json
{
  "status": "ok",
  "message": "Genkit OCR API is running"
}
```

## 사용 가능한 Make 명령어

```bash
make help           # 사용 가능한 명령어 보기
make build          # 애플리케이션 빌드
make run            # 빌드 후 실행
make dev            # 개발 모드 실행
make test           # 테스트 실행
make test-coverage  # 커버리지 포함 테스트
make clean          # 빌드 아티팩트 정리
make deps           # 의존성 다운로드
make lint           # 린터 실행
make fmt            # 코드 포맷팅
```

## 다음 단계

1. **API 문서**: `README.md`의 API 엔드포인트 섹션 참조
2. **아키텍처**: `ARCHITECTURE.md`에서 프로젝트 구조 확인
3. **개발 가이드**: `README.md`의 개발 가이드 섹션 참조

## 문제 해결

### API Key 오류
```
GOOGLE_API_KEY is required
```
→ `.env` 파일에 `GOOGLE_API_KEY` 설정 필요

### 포트 이미 사용 중
```
bind: address already in use
```
→ `.env`에서 `SERVER_PORT` 변경 (기본값: 6003)

### 빌드 오류
```bash
make clean
make deps
make build
```

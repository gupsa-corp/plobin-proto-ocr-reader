# GenkitGo - Document OCR API (Go + Genkit)

FastAPI 기반 OCR 시스템의 Go 포팅 버전입니다.

## 아키텍처

CLAUDE.md의 Laravel 패턴을 Go 언어에 적용한 구조:

```
Route → Controller → Service
```

## 디렉토리 구조

```
GenkitGo/
├── cmd/server/main.go              # Entry point + Route 등록
├── internal/
│   ├── http/controllers/           # HTTP 핸들러 (요청/응답 제어)
│   │   └── {Domain}/{Action}/
│   │       ├── controller.go       # 1파일 1메서드
│   │       ├── request.go          # 입력 검증
│   │       └── response.go         # 응답 구조
│   ├── services/                   # 비즈니스 로직
│   │   └── {Domain}/{Feature}/
│   │       └── service.go          # 1파일 1메서드
│   ├── flows/                      # Genkit Flows (LLM 통합용)
│   ├── models/                     # 공통 데이터 구조
│   └── config/                     # 설정 관리
└── tests/Feature/                  # Feature 테스트
    └── {Domain}/{Action}/{Scenario}/
        └── test.go                 # 1파일 1메서드
```

## 핵심 원칙

1. **1파일 1메서드**: Controller, Service, Test 각각 1개 함수만
2. **타입명 고정**: controller.go, request.go, response.go, service.go
3. **도메인 분리**: OCR/, PDF/, LLM/, Analysis/ 등
4. **계층 분리**: Route → Controller → Service

## 실행 방법

```bash
# 의존성 설치
go mod download

# 서버 실행
go run cmd/server/main.go
```

## API 엔드포인트

- `POST /api/ocr/process-image` - 이미지 OCR 처리
- `POST /api/ocr/process-pdf` - PDF OCR 처리
- `POST /api/analysis/analyze-document` - LLM 문서 분석

## API 응답 표준

```json
{
  "success": true,
  "message": "요청이 성공적으로 처리되었습니다",
  "data": { ... }
}
```

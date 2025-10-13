# GenkitGo - Document OCR API (Go + Genkit)

FastAPI 기반 OCR 시스템의 Go + Firebase Genkit 포팅 버전입니다.

## 주요 특징

- **🔥 Firebase Genkit**: 강력한 AI 플로우 오케스트레이션
- **🤖 Gemini Integration**: Google Gemini 모델을 통한 문서 분석
- **📄 OCR Processing**: Tesseract/Surya 기반 다국어 OCR
- **🚀 고성능**: Go 언어 기반 병렬 처리
- **🏗️ 확장 가능한 아키텍처**: 도메인 기반 계층 분리

## 아키텍처

CLAUDE.md의 Laravel 패턴을 Go 언어에 적용한 구조:

```
Route → Controller → Service → Genkit Flows
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
│   │   ├── OCR/                   # OCR 관련 서비스
│   │   ├── PDF/                   # PDF 처리 서비스
│   │   └── LLM/                   # LLM 분석 서비스
│   ├── flows/                      # Genkit Flows (AI 오케스트레이션)
│   │   └── flows.go               # OCR + Analysis 플로우
│   ├── models/                     # 공통 데이터 구조
│   ├── config/                     # 설정 관리
│   └── middleware/                 # HTTP 미들웨어
├── pkg/                            # 외부 공개 패키지
├── tests/                          # 테스트
│   ├── unit/                      # 단위 테스트
│   └── integration/               # 통합 테스트
├── demo/                           # 샘플 문서
│   ├── input/                     # 입력 샘플
│   └── processed/                 # 처리 결과
└── templates/                      # 템플릿 정의
```

## 핵심 원칙

1. **1파일 1메서드**: Controller, Service, Test 각각 1개 함수만
2. **타입명 고정**: controller.go, request.go, response.go, service.go
3. **도메인 분리**: OCR/, PDF/, LLM/, Analysis/ 등
4. **계층 분리**: Route → Controller → Service → Genkit Flow

## 설치 및 실행

### 사전 요구사항

- Go 1.22 이상
- Tesseract OCR (선택사항)
- Google Cloud API Key (Gemini 사용)

### 설치

```bash
# 저장소 클론
git clone <repository-url>
cd GenkitGo

# 의존성 설치
go mod download

# 환경 변수 설정
cp .env.example .env
# .env 파일에서 GOOGLE_API_KEY 설정
```

### 실행

```bash
# 개발 모드 실행
go run cmd/server/main.go

# 빌드 후 실행
go build -o bin/server cmd/server/main.go
./bin/server
```

서버는 기본적으로 `http://localhost:6003`에서 실행됩니다.

## API 엔드포인트

### Health Check
- `GET /` - 서버 상태 확인
- `GET /health` - Health check

### OCR Processing
- `POST /api/process-image` - 이미지 OCR 처리
- `POST /api/process-pdf` - PDF OCR 처리

### Document Analysis
- `POST /api/analyze` - LLM 기반 문서 분석

### Request Management
- `GET /api/requests` - 처리 요청 목록
- `GET /api/requests/{id}` - 특정 요청 상세 정보

## Genkit Flows

### processOCR
이미지 또는 PDF에서 텍스트를 추출합니다.

```go
Input: OCRRequest {
  FilePath: string
  Language: string
  UseGPU: bool
}

Output: OCRResponse {
  RequestID: string
  Blocks: []map[string]interface{}
  Text: string
  Success: bool
  Message: string
}
```

### analyzeDocument
LLM을 사용하여 문서를 분석합니다.

```go
Input: AnalysisRequest {
  Text: string
  Blocks: []map[string]interface{}
  Prompt: string
  ModelName: string
}

Output: AnalysisResponse {
  Analysis: string
  Success: bool
  Message: string
}
```

### processAndAnalyze
OCR 처리와 LLM 분석을 결합한 플로우입니다.

## API 응답 표준

### 성공 응답
```json
{
  "success": true,
  "message": "요청이 성공적으로 처리되었습니다",
  "data": {
    "request_id": "req_123",
    "result": { ... }
  }
}
```

### 실패 응답
```json
{
  "success": false,
  "message": "오류 메시지",
  "data": null
}
```

## 환경 변수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `SERVER_PORT` | 서버 포트 | `6003` |
| `SERVER_HOST` | 서버 호스트 | `0.0.0.0` |
| `OCR_ENGINE` | OCR 엔진 (tesseract/surya) | `tesseract` |
| `OCR_LANGUAGE` | OCR 언어 | `kor+eng` |
| `USE_GPU` | GPU 사용 여부 | `false` |
| `PDF_DPI` | PDF 변환 DPI | `300` |
| `GOOGLE_API_KEY` | Google API Key (필수) | - |
| `MODEL_NAME` | Gemini 모델명 | `gemini-1.5-flash` |
| `OUTPUT_DIR` | 출력 디렉토리 | `output` |
| `CACHE_DIR` | 캐시 디렉토리 | `cache` |
| `MAX_WORKERS` | 최대 워커 수 | `4` |
| `DEBUG` | 디버그 모드 | `false` |

## 개발 가이드

### 새로운 엔드포인트 추가

1. `internal/http/controllers/{Domain}/{Action}/` 디렉토리 생성
2. `controller.go`, `request.go`, `response.go` 파일 작성
3. 필요시 `internal/services/{Domain}/{Feature}/service.go` 작성
4. `cmd/server/main.go`에 라우트 등록

### 새로운 Genkit Flow 추가

1. `internal/flows/flows.go`에 플로우 함수 작성
2. `InitializeFlows()`에서 플로우 등록
3. Controller에서 플로우 호출

## 테스트

```bash
# 모든 테스트 실행
go test ./...

# 특정 패키지 테스트
go test ./internal/services/...

# 커버리지 확인
go test -cover ./...
```

## 라이선스

MIT License

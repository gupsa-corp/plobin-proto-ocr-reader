# GenkitGo Architecture

## 프로젝트 구조

```
GenkitGo/
├── cmd/
│   └── server/
│       └── main.go                    # 서버 엔트리 포인트, 라우팅 설정
│
├── internal/
│   ├── config/
│   │   └── config.go                  # 환경 변수 및 설정 관리
│   │
│   ├── flows/
│   │   └── flows.go                   # Google Generative AI를 사용한 플로우 관리
│   │                                  # - ProcessOCR: OCR 처리
│   │                                  # - AnalyzeDocument: LLM 문서 분석
│   │                                  # - ProcessAndAnalyze: OCR + 분석 결합
│   │
│   ├── models/
│   │   └── document.go                # 공통 데이터 모델
│   │
│   ├── http/
│   │   ├── common/                    # 공통 응답 핸들러
│   │   │   ├── ErrorResponse/
│   │   │   │   └── service.go
│   │   │   └── SuccessResponse/
│   │   │       └── service.go
│   │   │
│   │   └── controllers/               # HTTP 컨트롤러 (1파일 1메서드 원칙)
│   │       ├── OCR/
│   │       │   ├── ProcessImage/
│   │       │   │   ├── controller.go
│   │       │   │   └── request.go
│   │       │   └── ProcessPDF/
│   │       │       ├── controller.go
│   │       │       └── request.go
│   │       │
│   │       ├── Analysis/
│   │       │   └── AnalyzeDocument/
│   │       │       ├── controller.go
│   │       │       └── request.go
│   │       │
│   │       ├── Blocks/
│   │       ├── Images/
│   │       ├── Pages/
│   │       ├── Requests/
│   │       └── Meta/
│   │
│   ├── services/                      # 비즈니스 로직 (1파일 1메서드 원칙)
│   │   ├── OCR/
│   │   │   ├── InitializeOCR/
│   │   │   ├── ExtractBlocks/
│   │   │   └── MergeBlocks/
│   │   │
│   │   ├── PDF/
│   │   │   └── ConvertToImage/
│   │   │
│   │   └── LLM/
│   │       └── AnalyzeContent/
│   │
│   ├── middleware/                    # HTTP 미들웨어
│   └── handlers/                      # 기타 핸들러
│
├── pkg/                               # 외부 공개 패키지
├── tests/                             # 테스트 (1파일 1메서드 원칙)
│   ├── Feature/
│   │   └── OCR/
│   │       └── ProcessImage/
│   │           ├── Success/
│   │           │   └── test.go
│   │           └── ValidationFail/
│   │               └── test.go
│   ├── integration/
│   └── unit/
│
├── demo/                              # 샘플 문서
│   ├── input/
│   └── processed/
│
├── templates/                         # 템플릿 정의
│
├── go.mod                            # Go 모듈 정의
├── Makefile                          # 빌드 스크립트
├── .env.example                      # 환경 변수 예시
├── .gitignore                        # Git 제외 파일
├── README.md                         # 프로젝트 문서
└── ARCHITECTURE.md                   # 아키텍처 문서 (이 파일)
```

## 데이터 플로우

### 1. OCR 처리 플로우
```
HTTP Request → Controller → Service → OCR Engine → Response
                              ↓
                        FlowManager (선택)
```

### 2. LLM 분석 플로우
```
HTTP Request → Controller → FlowManager → Gemini API → Response
```

### 3. 통합 플로우 (OCR + Analysis)
```
HTTP Request → Controller → FlowManager → OCR Engine → Gemini API → Response
```

## 주요 컴포넌트

### FlowManager (`internal/flows/flows.go`)
- **역할**: Google Generative AI를 사용한 AI 플로우 오케스트레이션
- **주요 메서드**:
  - `NewFlowManager(ctx, apiKey, modelName)`: FlowManager 생성
  - `ProcessOCR(ctx, req)`: OCR 처리
  - `AnalyzeDocument(ctx, req)`: LLM 기반 문서 분석
  - `ProcessAndAnalyze(ctx, req)`: OCR + 분석 결합
  - `Close()`: 리소스 정리

### Config (`internal/config/config.go`)
- **역할**: 환경 변수 및 애플리케이션 설정 관리
- **주요 필드**:
  - Server: 포트, 호스트
  - OCR: 엔진, 언어, GPU 사용 여부
  - LLM: Google API Key, 모델명
  - Storage: 출력/캐시/템플릿 디렉토리
  - Performance: 워커 수, 압축 활성화

### Controllers
- **역할**: HTTP 요청/응답 처리
- **원칙**: 1파일 1메서드, 비즈니스 로직 포함 금지
- **구조**: `{Domain}/{Action}/controller.go`

### Services
- **역할**: 비즈니스 로직 처리
- **원칙**: 1파일 1메서드
- **구조**: `{Domain}/{Feature}/service.go`

## API 엔드포인트

### Health Check
- `GET /` - 서버 상태
- `GET /health` - Health check

### OCR Processing
- `POST /api/process-image` - 이미지 OCR
- `POST /api/process-pdf` - PDF OCR

### Document Analysis
- `POST /api/analyze` - LLM 분석

### Request Management
- `GET /api/requests` - 요청 목록
- `GET /api/requests/{id}` - 요청 상세

## 확장 가능성

### 새로운 OCR 엔진 추가
1. `internal/services/OCR/` 하위에 새 서비스 생성
2. `FlowManager.ProcessOCR()` 메서드에서 엔진 선택 로직 추가

### 새로운 LLM 모델 추가
1. `internal/flows/flows.go`의 `AnalyzeDocument()` 메서드 수정
2. 환경 변수에 모델명 추가

### 새로운 API 엔드포인트 추가
1. `internal/http/controllers/{Domain}/{Action}/` 생성
2. `controller.go`, `request.go` 작성
3. `cmd/server/main.go`에 라우트 등록

## 기술 스택

- **언어**: Go 1.24
- **라우터**: chi v5
- **LLM**: Google Generative AI (Gemini)
- **Validation**: go-playground/validator
- **환경 변수**: godotenv

## 개발 원칙

1. **1파일 1메서드**: 모든 Controller, Service, Test는 1개 메서드만 포함
2. **타입명 고정**: controller.go, request.go, response.go, service.go
3. **도메인 분리**: OCR, PDF, LLM, Analysis 등 도메인별 분리
4. **계층 분리**: Route → Controller → Service → FlowManager
5. **표준 응답**: 모든 API는 `{success, message, data}` 형식 사용

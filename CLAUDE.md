# Document OCR Reader API

## 프로젝트 개요
PaddleOCR을 기반으로 한 문서 텍스트 추출 및 블록 분류 API 서버

**Repository**: https://github.com/gupsa-corp/plobin-proto-ocr-reader

## 서버 정보
- **포트**: 6003 (폴더명 6003-ocr-reader에 맞춤)
- **주소**: http://localhost:6003
- **실행 명령어**: `python3 -m uvicorn api_server:app --host 0.0.0.0 --port 6003 --reload`

## API 엔드포인트

### 기본 정보
- `GET /` - API 정보 확인
- `GET /health` - 서버 상태 및 GPU 사용 가능 여부 확인
- `GET /supported-formats` - 지원하는 파일 포맷 목록

### 문서 처리
- `POST /process-image` - 이미지 파일 OCR 처리
- `POST /process-pdf` - PDF 파일 OCR 처리 (페이지별 분할)
- `POST /process-document` - 범용 문서 처리 (이미지/PDF 자동 감지)

### 새로운 요청 기반 처리 (UUID 구조)
- `POST /process-request` - UUID 기반 요청 생성 및 처리
- `GET /requests` - 모든 요청 목록 조회 (시간순 정렬)
- `GET /requests/{request_id}` - 특정 요청 정보 조회
- `GET /requests/{request_id}/pages/{page_number}` - 특정 페이지 결과 조회
- `GET /requests/{request_id}/pages/{page_number}/blocks/{block_id}` - 특정 블록 데이터 조회
- `GET /requests/{request_id}/pages/{page_number}/visualization` - 페이지 시각화 다운로드
- `GET /requests/{request_id}/pages/{page_number}/original` - 페이지 원본 이미지 다운로드
- `GET /requests/{request_id}/pages/{page_number}/blocks/{block_id}/image` - 블록 크롭 이미지 다운로드
- `DELETE /requests/{request_id}` - 요청 삭제

### 이미지 처리
- `GET /requests/{request_id}/pages/{page_number}/image-metadata` - 이미지 메타데이터 조회
- `GET /requests/{request_id}/pages/{page_number}/thumbnail` - 이미지 썸네일 생성
- `GET /requests/{request_id}/pages/{page_number}/proxy` - 이미지 프록시 (변환/리사이즈)
- `POST /convert-image` - 이미지 형식 변환

### 서버 상태
- `GET /status` - 서버 상태 및 처리 통계 확인

### 템플릿 관리
- `POST /templates` - 새 템플릿 생성
- `GET /templates` - 템플릿 목록 조회 (필터링 지원)
- `GET /templates/{template_id}` - 특정 템플릿 조회
- `PUT /templates/{template_id}` - 템플릿 수정
- `DELETE /templates/{template_id}` - 템플릿 삭제
- `POST /templates/{template_id}/duplicate` - 템플릿 복제
- `GET /templates/search` - 템플릿 검색
- `GET /templates/statistics` - 템플릿 통계
- `POST /templates/validate` - 템플릿 검증
- `POST /templates/{template_id}/match` - 특정 템플릿으로 문서 처리
- `POST /templates/auto-match` - 자동 템플릿 매칭으로 문서 처리
- `GET /templates/{template_id}/preview` - 템플릿 시각화 미리보기
- `POST /templates/{template_id}/validate-document` - 템플릿으로 문서 검증
- `POST /templates/{template_id}/usage` - 템플릿 사용 횟수 증가
- `POST /templates/{template_id}/accuracy` - 템플릿 정확도 업데이트

### LLM 분석 (신규)
- `POST /analysis/sections/analyze` - 개별 섹션 텍스트 LLM 분석
- `POST /analysis/documents/{request_id}/pages/{page_number}/analyze` - 문서 페이지 섹션별 LLM 분석
- `GET /analysis/documents/{request_id}/pages/{page_number}/analysis` - 저장된 분석 결과 조회
- `GET /analysis/documents/{request_id}/analysis/summary` - 전체 문서 분석 요약 조회
- `DELETE /analysis/documents/{request_id}/analysis` - 문서 분석 결과 삭제
- `GET /analysis/models` - 사용 가능한 LLM 모델 목록 조회
- `GET /analysis/health` - LLM 분석 서비스 상태 확인

### 통합 OCR + LLM 분석 (신규)
- `POST /analysis/process-and-analyze` - 파일 업로드 → OCR → LLM 분석 원스톱 처리
- `GET /analysis/integrated-results` - 통합 분석 결과 목록 조회 (페이징 지원)
- `GET /analysis/integrated-results/{request_id}` - 특정 통합 결과 JSON 조회
- `GET /analysis/integrated-results/{request_id}/download` - 통합 결과 JSON 파일 다운로드

### 디버깅 및 개발 도구 (신규)
- `GET /analysis/debug/api-info` - LLM API 연결 정보 및 설정 확인
- `GET /analysis/debug/test-connection` - 다양한 LLM API 엔드포인트 연결 테스트
- `POST /analysis/debug/manual-request` - 수동 LLM API 요청 테스트

## 지원 파일 포맷
- **이미지**: JPEG, PNG, BMP, TIFF, WEBP
- **문서**: PDF

## 응답 형식 (새로운 UUID 기반)
```json
{
  "request_id": "01890a5d-ac96-774b-bcce-b302099a8057",
  "status": "completed",
  "original_filename": "sample_document.pdf",
  "file_type": "pdf",
  "file_size": 245760,
  "total_pages": 3,
  "processing_time": 2.345,
  "processing_url": "/requests/01890a5d-ac96-774b-bcce-b302099a8057"
}
```

## 테스트 방법
```bash
# API 테스트 실행
python3 test_api.py

# 기본 엔드포인트 테스트
curl -X GET http://localhost:6003/health
curl -X GET http://localhost:6003/status
curl -X GET http://localhost:6003/supported-formats

# 문서 처리 테스트
curl -X POST -F "file=@demo/invoices/sample_invoice.pdf" http://localhost:6003/process-pdf
curl -X POST -F "file=@demo/images/sample.png" http://localhost:6003/process-image
curl -X POST -F "file=@demo/invoices/sample_invoice.pdf" http://localhost:6003/process-document

# UUID 기반 요청 관리 테스트
curl -X POST -F "file=@demo/invoices/sample_invoice.pdf" -F "description=테스트 요청" http://localhost:6003/process-request
curl -X GET http://localhost:6003/requests
curl -X GET http://localhost:6003/requests/{request_id}
curl -X GET http://localhost:6003/requests/{request_id}/pages/1
curl -X GET http://localhost:6003/requests/{request_id}/pages/1/blocks/1
curl -X GET http://localhost:6003/requests/{request_id}/pages/1/visualization
curl -X DELETE http://localhost:6003/requests/{request_id}

# 이미지 처리 API 테스트
curl -X GET http://localhost:6003/requests/{request_id}/pages/1/image-metadata
curl -X GET "http://localhost:6003/requests/{request_id}/pages/1/thumbnail?size=200&quality=85"
curl -X GET "http://localhost:6003/requests/{request_id}/pages/1/proxy?image_type=original&format=jpeg&quality=70&max_width=800"
curl -X GET "http://localhost:6003/requests/{request_id}/pages/1/proxy?image_type=visualization&max_height=500"
curl -X GET "http://localhost:6003/requests/{request_id}/pages/1/proxy?image_type=block/1&format=webp&quality=60"
curl -X POST "http://localhost:6003/convert-image?target_format=webp&quality=80&resize_width=400" -F "file=@demo/images/sample.png"

# 템플릿 API 테스트
curl -X GET http://localhost:6003/templates
curl -X GET http://localhost:6003/templates/invoice_standard_001
curl -X GET http://localhost:6003/templates/statistics
curl -X GET "http://localhost:6003/templates/search?query=송장"
curl -X POST -F "file=@demo/invoices/sample_invoice.pdf" http://localhost:6003/templates/invoice_standard_001/match
curl -X POST -F "file=@demo/invoices/sample_invoice.pdf" http://localhost:6003/templates/auto-match

# LLM 분석 API 테스트 (신규)
python3 test_analysis_api.py
curl -X GET http://localhost:6003/analysis/health
curl -X GET http://localhost:6003/analysis/models
curl -X POST http://localhost:6003/analysis/sections/analyze -H "Content-Type: application/json" -d '{"text":"테스트 텍스트","section_type":"general","model":"boto"}'
curl -X POST http://localhost:6003/analysis/documents/{request_id}/pages/1/analyze -H "Content-Type: application/json" -d '{"model":"boto"}'
curl -X GET http://localhost:6003/analysis/documents/{request_id}/pages/1/analysis
curl -X GET http://localhost:6003/analysis/documents/{request_id}/analysis/summary

# 통합 OCR + LLM 분석 API 테스트 (신규)
curl -X POST http://localhost:6003/analysis/process-and-analyze -F "file=@test_receipt.png" -F "description=영수증 분석 테스트"
curl -X POST http://localhost:6003/analysis/process-and-analyze -F "file=@document.pdf" -F "description=문서 분석" -F 'analysis_config={"perform_llm_analysis": true, "model": "boto", "document_type": "invoice"}'
curl -X GET http://localhost:6003/analysis/integrated-results
curl -X GET http://localhost:6003/analysis/integrated-results/{request_id}
curl -X GET http://localhost:6003/analysis/integrated-results/{request_id}/download

# 디버깅 및 개발 도구 테스트 (신규)
curl -X GET http://localhost:6003/analysis/debug/api-info
curl -X GET http://localhost:6003/analysis/debug/test-connection
curl -X POST http://localhost:6003/analysis/debug/manual-request -H "Content-Type: application/json" -d '{"url":"https://llm.gupsa.net/v1/models","method":"GET"}'
```

## 출력 파일 구조 (UUID 기반)
```
output/
└── {UUID}/                          # 시간 기반 UUID (예: 01890a5d-ac96-774b-bcce-b302099a8057)
    ├── metadata.json                # 요청 메타데이터 (원본 파일명, 타입, 크기 등)
    ├── summary.json                 # 전체 처리 요약
    └── pages/                       # 페이지들을 담는 폴더
        ├── 001/                     # 페이지별 폴더 (3자리 숫자)
        │   ├── page_info.json      # 페이지 메타데이터
        │   ├── result.json         # 페이지 OCR 결과
        │   ├── original.png        # 원본 페이지 이미지
        │   ├── visualization.png   # 바운딩 박스 시각화
        │   ├── analysis/           # LLM 분석 결과 (신규)
        │   │   └── llm_analysis.json  # 섹션별 LLM 분석 결과
        │   └── blocks/             # 블록별 상세 데이터
        │       ├── block_001.json  # 블록 메타데이터
        │       ├── block_001.png   # 크롭된 블록 이미지
        │       ├── block_002.json
        │       ├── block_002.png
        │       └── ...
        ├── 002/
        └── ...
```

**특징**:
- 요청별 명확한 분리 및 추적
- 블록별 개별 접근 및 이미지 다운로드 가능
- 시간 순서 자동 정렬 (UUID v7 기반)
- 확장성 및 메타데이터 관리 용이
- 원본 이미지, 블록 크롭 이미지, 시각화 이미지 모두 저장

## 주요 파일
- `api_server.py` - FastAPI 서버 메인 파일
- `services/` - 도메인별 서비스 레이어 (도메인/하위도메인 구조)
  - `ocr/` - OCR 도메인
    - `initialization.py` - PaddleOCR 초기화
    - `extraction.py` - 텍스트 블록 추출
    - `merging.py` - 블록 병합 로직
    - `visualization.py` - 블록 시각화
  - `pdf/` - PDF 도메인
    - `conversion.py` - PDF를 이미지로 변환
    - `processing.py` - PDF OCR 처리
  - `file/` - 파일 관리 도메인
    - `storage.py` - 파일 저장/로드 (기존 + 새로운 RequestStorage 클래스)
    - `metadata.py` - 파일명 생성 및 메타데이터 관리
    - `directories.py` - 디렉토리 관리 (기존 + UUID 기반 구조)
    - `request_manager.py` - 요청 관리 및 시간 기반 UUID 생성
  - `image/` - 이미지 처리 도메인
    - `io.py` - 이미지 입출력
    - `validation.py` - 이미지 검증
    - `metadata.py` - 이미지 메타데이터
  - `visualization/` - 시각화 도메인
    - `rendering.py` - 바운딩 박스 렌더링
    - `legend.py` - 범례 생성
    - `export.py` - 시각화 내보내기
  - `template/` - 템플릿 관리 도메인 (신규)
    - `manager.py` - 템플릿 CRUD 관리
    - `storage.py` - 템플릿 파일 저장/로드
    - `validator.py` - 템플릿 유효성 검증
    - `matcher.py` - 템플릿 매칭 알고리즘 (구현 예정)
    - `generator.py` - 자동 템플릿 생성 (구현 예정)
    - `visualization.py` - 템플릿 시각화 (구현 예정)
  - `llm/` - LLM 분석 도메인 (신규)
    - `client.py` - ai.gupsa.net/v1 LLM API 클라이언트
    - `analyzer.py` - OCR 결과 섹션별 분석기
- `api/endpoints/` - API 엔드포인트 모듈들
  - `requests.py` - 새로운 UUID 기반 요청 처리 API
  - `templates.py` - 템플릿 관리 API (신규)
  - `analysis.py` - LLM 분석 API (신규)
- `api/models/` - Pydantic 스키마 모델들
  - `analysis.py` - LLM 분석 관련 스키마 (신규)
- `api/utils/` - 유틸리티 함수들
- `test_api.py` - API 테스트 스크립트
- `test_analysis_api.py` - LLM 분석 API 테스트 스크립트 (신규)

## 개발 환경
- Python 3.12
- PaddleOCR v2.7.3
- FastAPI 0.118.0
- GPU: RTX 3090 (현재 CPU 모드 실행)

## 성능
- PDF 처리: 평균 99.0% 신뢰도
- 이미지 처리: 평균 97.2% 신뢰도
- 실시간 처리 가능
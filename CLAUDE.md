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
- `DELETE /requests/{request_id}` - 요청 삭제

### 서버 상태 및 결과 관리
- `GET /status` - 서버 상태 및 처리 통계 확인
- `GET /output/list` - 처리 결과 파일 목록 조회
- `GET /output/stats` - 출력 폴더 통계 정보
- `GET /output/search` - 파일 검색 (쿼리, 타입, 날짜 필터)
- `POST /output/batch` - 배치 파일 작업

### 개별 파일 관리
- `GET /output/{filename}` - 개별 파일 내용 조회
- `GET /output/download/{filename}` - 파일 다운로드
- `DELETE /output/{filename}` - 파일 삭제

### 블록별 세부 조회
- `GET /output/{filename}/blocks/{block_id}` - 특정 블록 조회
- `GET /output/{filename}/blocks` - 블록 필터링 및 범위 조회
- `GET /output/{filename}/blocks/stats` - 블록 통계
- `GET /output/{filename}/blocks/by_position` - 좌표 기반 블록 검색

## 지원 파일 포맷
- **이미지**: JPEG, PNG, BMP, TIFF, WEBP
- **문서**: PDF

## 응답 형식
```json
{
  "filename": "문서명",
  "total_blocks": 추출된_블록_수,
  "average_confidence": 평균_신뢰도,
  "processing_time": 처리_시간_초,
  "blocks": [
    {
      "text": "추출된_텍스트",
      "confidence": 신뢰도_점수,
      "bbox": [[x1,y1], [x2,y2], [x3,y3], [x4,y4]],
      "block_type": "블록_타입"
    }
  ],
  "output_files": {
    "json_result": "output/결과_파일.json",
    "result_filename": "결과_파일.json",
    "visualization": "output/시각화_이미지.png",
    "visualization_filename": "시각화_이미지.png"
  }
}
```

## 테스트 방법
```bash
# API 테스트 실행
python3 test_api.py

# 개별 엔드포인트 테스트
curl -X GET http://localhost:6003/health
curl -X GET http://localhost:6003/status
curl -X GET http://localhost:6003/output/list
curl -X POST -F "file=@demo/invoices/sample_invoice.pdf" http://localhost:6003/process-pdf

# 기존 API 테스트
curl -X GET http://localhost:6003/output/stats
curl -X GET "http://localhost:6003/output/search?query=aaa&file_type=json"
curl -X GET http://localhost:6003/output/aaa_20250929_232830_result.json
curl -X GET http://localhost:6003/output/aaa_20250929_232830_result.json/blocks/5
curl -X GET "http://localhost:6003/output/aaa_20250929_232830_result.json/blocks?confidence_min=0.95&start=0&end=10"
curl -X GET http://localhost:6003/output/aaa_20250929_232830_result.json/blocks/stats
curl -X GET "http://localhost:6003/output/aaa_20250929_232830_result.json/blocks/by_position?x=500&y=300"

# 새로운 UUID 기반 API 테스트
curl -X POST -F "file=@demo/invoices/sample_invoice.pdf" -F "description=테스트 요청" http://localhost:6003/process-request
curl -X GET http://localhost:6003/requests
curl -X GET http://localhost:6003/requests/{request_id}
curl -X GET http://localhost:6003/requests/{request_id}/pages/1
curl -X GET http://localhost:6003/requests/{request_id}/pages/1/blocks/1
curl -X GET http://localhost:6003/requests/{request_id}/pages/1/visualization
curl -X DELETE http://localhost:6003/requests/{request_id}
```

## 출력 파일 구조

### 기존 구조 (레거시)
- **JSON 결과**: 타임스탬프가 포함된 상세 OCR 결과 파일
- **시각화 이미지**: 바운딩 박스가 표시된 원본 이미지
- **자동 파일명**: `원본파일명_YYYYMMDD_HHMMSS_result.json/visualization.png`

### 새로운 UUID 기반 구조
```
output/
└── {UUID}/                          # 시간 기반 UUID (예: 01890a5d-ac96-774b-bcce-b302099a8057)
    ├── metadata.json                # 요청 메타데이터 (원본 파일명, 타입, 크기 등)
    ├── summary.json                 # 전체 처리 요약
    └── pages/                       # 페이지들을 담는 폴더
        ├── 001/                     # 페이지별 폴더 (3자리 숫자)
        │   ├── page_info.json      # 페이지 메타데이터
        │   ├── result.json         # 페이지 OCR 결과
        │   ├── visualization.png   # 페이지 시각화
        │   └── blocks/             # 블록별 상세 데이터
        │       ├── block_001.json
        │       ├── block_002.json
        │       └── ...
        ├── 002/
        └── ...
```

**장점**:
- 요청별 명확한 분리 및 추적
- 블록별 개별 접근 가능
- 시간 순서 자동 정렬 (UUID v7 유사)
- 확장성 및 메타데이터 관리 용이

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
- `api/endpoints/` - API 엔드포인트 모듈들
  - `requests.py` - 새로운 UUID 기반 요청 처리 API
- `api/models/` - Pydantic 스키마 모델들
- `api/utils/` - 유틸리티 함수들
- `test_api.py` - API 테스트 스크립트

## 개발 환경
- Python 3.12
- PaddleOCR v2.7.3
- FastAPI 0.118.0
- GPU: RTX 3090 (현재 CPU 모드 실행)

## 성능
- PDF 처리: 평균 99.0% 신뢰도
- 이미지 처리: 평균 97.2% 신뢰도
- 실시간 처리 가능
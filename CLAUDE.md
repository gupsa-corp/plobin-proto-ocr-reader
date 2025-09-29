# Document OCR Reader API

## 프로젝트 개요
PaddleOCR을 기반으로 한 문서 텍스트 추출 및 블록 분류 API 서버

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

# 새로운 API 테스트
curl -X GET http://localhost:6003/output/stats
curl -X GET "http://localhost:6003/output/search?query=aaa&file_type=json"
curl -X GET http://localhost:6003/output/aaa_20250929_232830_result.json
curl -X GET http://localhost:6003/output/aaa_20250929_232830_result.json/blocks/5
curl -X GET "http://localhost:6003/output/aaa_20250929_232830_result.json/blocks?confidence_min=0.95&start=0&end=10"
curl -X GET http://localhost:6003/output/aaa_20250929_232830_result.json/blocks/stats
curl -X GET "http://localhost:6003/output/aaa_20250929_232830_result.json/blocks/by_position?x=500&y=300"
```

## 출력 파일 구조
- **JSON 결과**: 타임스탬프가 포함된 상세 OCR 결과 파일
- **시각화 이미지**: 바운딩 박스가 표시된 원본 이미지
- **자동 파일명**: `원본파일명_YYYYMMDD_HHMMSS_result.json/visualization.png`

## 주요 파일
- `api_server.py` - FastAPI 서버 메인 파일
- `document_block_extractor.py` - PaddleOCR 블록 추출 클래스
- `pdf_to_image_processor.py` - PDF를 이미지로 변환하는 클래스
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
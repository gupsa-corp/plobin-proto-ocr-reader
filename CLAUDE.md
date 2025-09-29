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

## 지원 파일 포맷
- **이미지**: JPEG, PNG, BMP, TIFF, WEBP
- **문서**: PDF

## 응답 형식
```json
{
  "filename": "문서명",
  "total_blocks": 추출된_블록_수,
  "average_confidence": 평균_신뢰도,
  "blocks": [
    {
      "text": "추출된_텍스트",
      "confidence": 신뢰도_점수,
      "bbox": [[x1,y1], [x2,y2], [x3,y3], [x4,y4]],
      "block_type": "블록_타입"
    }
  ]
}
```

## 테스트 방법
```bash
# API 테스트 실행
python3 test_api.py

# 개별 엔드포인트 테스트
curl -X GET http://localhost:6003/health
curl -X POST -F "file=@demo/invoices/sample_invoice.pdf" http://localhost:6003/process-pdf
```

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
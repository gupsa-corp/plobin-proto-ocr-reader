# Plobin Proto OCR Reader - Laravel API

Laravel 기반 OCR 문서 처리 시스템입니다. Python FastAPI OCR 엔진과 연동하여 이미지 및 PDF 파일에서 텍스트를 추출합니다.

## 🚀 주요 기능

- **이미지 OCR 처리**: JPEG, PNG, GIF, WEBP 형식 지원
- **PDF OCR 처리**: 다중 페이지 PDF 파일 처리
- **Python OCR 엔진 연동**: FastAPI 기반 PaddleOCR 엔진 활용
- **데이터베이스 관리**: 요청, 페이지, 블록 정보 저장
- **RESTful API**: 표준 HTTP 메서드 지원

## 📦 설치

### 1. 사전 요구사항

- PHP 8.2 이상
- Composer
- SQLite (또는 MySQL/PostgreSQL)
- Python FastAPI OCR 서버 (별도 실행 필요)

### 2. 프로젝트 설정

```bash
# 의존성 설치
composer install

# 환경 설정 파일 복사
cp .env.example .env

# 애플리케이션 키 생성
php artisan key:generate

# 데이터베이스 마이그레이션
php artisan migrate
```

### 3. Python OCR 서버 실행

```bash
# 기존 Python 프로젝트 디렉토리로 이동
cd ../plobin-proto-ocr-reader

# Python 가상환경 활성화
source paddle_ocr_env/bin/activate  # Linux/Mac
# 또는
.\paddle_ocr_env\Scripts\activate  # Windows

# FastAPI 서버 실행
python api_server.py
# 기본 포트: http://localhost:6003
```

### 4. Laravel 개발 서버 실행

```bash
php artisan serve
# 기본 포트: http://localhost:8000
```

## 🔧 환경 설정

`.env` 파일에서 Python OCR API URL을 설정하세요:

```env
PYTHON_OCR_API_URL=http://localhost:6003
```

## 📖 API 엔드포인트

### 1. 이미지 OCR 처리

**POST** `/api/process-image`

**요청 (multipart/form-data)**:
```
file: [이미지 파일] (필수)
merge_blocks: true (선택, 기본값: true)
merge_threshold: 30 (선택, 기본값: 30)
```

**응답**:
```json
{
  "success": true,
  "message": "OCR 처리가 완료되었습니다.",
  "data": {
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "original_filename": "document.jpg",
    "file_type": "image",
    "file_size": 1024000,
    "total_pages": 1,
    "processing_time": 2.354,
    "processing_url": "/requests/550e8400-e29b-41d4-a716-446655440000"
  }
}
```

**cURL 예제**:
```bash
curl -X POST http://localhost:8000/api/process-image \
  -F "file=@/path/to/image.jpg" \
  -F "merge_blocks=true" \
  -F "merge_threshold=30"
```

### 2. PDF OCR 처리

**POST** `/api/process-pdf`

**요청 (multipart/form-data)**:
```
file: [PDF 파일] (필수)
merge_blocks: true (선택, 기본값: true)
merge_threshold: 30 (선택, 기본값: 30)
```

**응답**:
```json
{
  "success": true,
  "message": "PDF OCR 처리가 완료되었습니다.",
  "data": {
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "original_filename": "document.pdf",
    "file_type": "pdf",
    "file_size": 2048000,
    "total_pages": 5,
    "processing_time": 12.567,
    "processing_url": "/requests/550e8400-e29b-41d4-a716-446655440000"
  }
}
```

**cURL 예제**:
```bash
curl -X POST http://localhost:8000/api/process-pdf \
  -F "file=@/path/to/document.pdf" \
  -F "merge_blocks=true" \
  -F "merge_threshold=30"
```

## 🗄️ 데이터베이스 구조

### plobin_ocr_requests
OCR 요청 정보 저장
- `id`: 기본 키
- `request_id`: UUID 고유 요청 ID
- `original_filename`: 원본 파일명
- `file_type`: 파일 타입 (image/pdf)
- `file_size`: 파일 크기 (bytes)
- `total_pages`: 총 페이지 수
- `status`: 처리 상태 (processing/completed/failed)
- `overall_confidence`: 전체 신뢰도
- `total_blocks`: 전체 블록 수
- `processing_time`: 처리 시간 (초)
- `completed_at`: 완료 시각

### plobin_ocr_pages
페이지별 OCR 결과 저장
- `id`: 기본 키
- `request_id`: 요청 ID (외래 키)
- `page_number`: 페이지 번호
- `total_blocks`: 페이지 블록 수
- `average_confidence`: 평균 신뢰도
- `processing_time`: 처리 시간 (초)
- `original_image_path`: 원본 이미지 경로
- `visualization_path`: 시각화 이미지 경로

### plobin_ocr_blocks
블록별 텍스트 및 메타데이터 저장
- `id`: 기본 키
- `page_id`: 페이지 ID (외래 키)
- `block_number`: 블록 번호
- `text`: 인식된 텍스트
- `confidence`: 신뢰도
- `bbox`: 바운딩 박스 좌표 (JSON)
- `block_type`: 블록 타입 (title/paragraph/table/list/other)
- `image_path`: 블록 이미지 경로

## 🏗️ 프로젝트 구조

```
plobin-proto-ocr-reader-laravel/
├── app/
│   ├── Http/
│   │   └── Controllers/
│   │       └── Ocr/
│   │           ├── ProcessImage/
│   │           │   ├── Controller.php
│   │           │   ├── Request.php
│   │           │   └── Response.php
│   │           └── ProcessPdf/
│   │               ├── Controller.php
│   │               ├── Request.php
│   │               └── Response.php
│   └── Services/
│       └── Ocr/
│           ├── ProcessImage/
│           │   └── Service.php
│           └── ProcessPdf/
│               └── Service.php
├── database/
│   └── migrations/
│       ├── 2025_10_12_033424_create_plobin_ocr_requests_table.php
│       ├── 2025_10_12_033425_create_plobin_ocr_pages_table.php
│       └── 2025_10_12_033425_create_plobin_ocr_blocks_table.php
├── routes/
│   ├── api.php
│   └── web.php
└── config/
    └── services.php
```

## 🔍 아키텍처 원칙

### 1파일 1메서드 원칙
- Controller, Service, Request, Response 각각 단일 메서드만 보유
- 명확한 책임 분리와 유지보수성 향상

### Layered Architecture
- **Controller**: HTTP 요청 수신 → Service 호출 → Response 반환
- **Service**: Python OCR API 호출 및 비즈니스 로직 처리
- **Request**: 입력 데이터 유효성 검증
- **Response**: API 응답 구조화

## 🧪 테스트

```bash
# 단위 테스트 실행
php artisan test

# 특정 테스트 실행
php artisan test --filter=ProcessImageTest
```

## 📝 주의사항

1. **Python OCR 서버 필수**: Laravel API를 사용하기 전에 Python FastAPI 서버가 실행 중이어야 합니다.
2. **파일 크기 제한**: 이미지 10MB, PDF 50MB (php.ini에서 조정 가능)
3. **타임아웃 설정**: 대용량 PDF 처리 시 `max_execution_time` 증가 권장

## 🤝 기여

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 라이선스

MIT License

## 🙏 감사의 말

- [Laravel](https://laravel.com/) - 우아한 PHP 프레임워크
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) - 강력한 OCR 엔진
- [FastAPI](https://fastapi.tiangolo.com/) - Python OCR 서버 프레임워크

---

**⭐ 이 프로젝트가 도움이 되었다면 별표를 눌러주세요!**

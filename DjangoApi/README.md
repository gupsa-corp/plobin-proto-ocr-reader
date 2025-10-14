# Document OCR Reader API - Django 버전

FastAPI에서 Django로 포팅된 문서 OCR 처리 API 서버

## 프로젝트 개요

Surya OCR을 기반으로 한 문서 텍스트 추출 및 블록 분류 API 서버 (90+ 언어 지원)

## 주요 변경 사항

### FastAPI → Django 전환

- **프레임워크**: FastAPI → Django + Django REST Framework
- **구조**: 서비스 레이어는 유지, API 엔드포인트만 Django 뷰로 전환
- **데이터베이스**: 요청 관리를 위한 모델 추가 (ProcessingRequest, PageResult)
- **문서화**: FastAPI의 OpenAPI → DRF Spectacular

### 디렉토리 구조

```
DjangoApi/
├── manage.py                  # Django 관리 명령어
├── requirements.txt           # 의존성 패키지
├── ocr_api/                  # Django 프로젝트 설정
│   ├── settings.py           # 설정 파일
│   ├── urls.py               # 메인 URL 라우팅
│   ├── wsgi.py               # WSGI 애플리케이션
│   └── asgi.py               # ASGI 애플리케이션
├── apps/                     # Django 앱들
│   ├── ocr/                  # OCR 처리 앱
│   │   ├── models.py         # 데이터 모델
│   │   ├── views.py          # API 뷰
│   │   ├── serializers.py    # DRF 시리얼라이저
│   │   ├── urls.py           # URL 라우팅
│   │   └── services/         # FastAPI의 services 복사
│   ├── analysis/             # LLM 분석 앱
│   ├── templates/            # 템플릿 관리 앱
│   └── requests/             # 요청 관리 앱
├── output/                   # OCR 결과 저장
├── media/                    # 미디어 파일
├── static/                   # 정적 파일
└── logs/                     # 로그 파일
```

## 설치 및 실행

### 1. 의존성 설치

```bash
cd DjangoApi
pip install -r requirements.txt
```

### 2. 데이터베이스 마이그레이션

```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. 서버 실행

```bash
# 개발 서버
python manage.py runserver 0.0.0.0:6003

# 프로덕션 (Gunicorn)
gunicorn ocr_api.wsgi:application --bind 0.0.0.0:6003 --workers 4
```

### 4. API 문서 확인

- Swagger UI: http://localhost:6003/api/docs/
- OpenAPI Schema: http://localhost:6003/api/schema/

## API 엔드포인트

### 헬스 체크
- `GET /api/health/` - 서버 상태 및 GPU 사용 가능 여부 확인
- `GET /api/status/` - 서버 통계 정보

### OCR 처리
- `POST /api/process-image/` - 이미지 파일 OCR 처리

### LLM 분석
- `GET /api/analysis/health/` - LLM 분석 서비스 상태

## 주요 기능

### 1. OCR 처리
- Surya OCR 엔진 사용 (90+ 언어 지원)
- GPU 가속 지원
- 블록 병합 및 섹션 그룹핑
- 계층 구조 구축

### 2. 데이터 모델
- ProcessingRequest: 처리 요청 정보
- PageResult: 페이지별 결과 정보

### 3. 파일 관리
- UUID 기반 요청 관리
- 원본/시각화/블록 이미지 저장
- JSON 결과 파일 저장

## FastAPI 대비 차이점

### 장점
1. **Django Admin**: 데이터베이스 관리 UI 제공
2. **ORM**: 강력한 쿼리 기능
3. **미들웨어**: 다양한 미들웨어 생태계
4. **인증/권한**: Django의 강력한 인증 시스템

### 단점
1. **성능**: FastAPI보다 약간 느릴 수 있음
2. **비동기**: FastAPI의 네이티브 async/await 지원 부족
3. **타입 힌팅**: Pydantic만큼 강력하지 않음

## 개발 환경
- Python 3.12
- Django 5.0
- Django REST Framework 3.14
- Surya OCR v0.4.0+
- GPU: RTX 3090 (선택 사항)

## 테스트

```bash
# 헬스 체크
curl http://localhost:6003/api/health/

# 이미지 처리
curl -X POST http://localhost:6003/api/process-image/ \
  -F "file=@test_image.png" \
  -F "merge_blocks=true" \
  -F "create_sections=true"
```

## 라이선스

MIT License

## 연락처

- Repository: https://github.com/gupsa-corp/plobin-proto-ocr-reader

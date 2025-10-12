# PaddleOCR → Surya OCR 마이그레이션 가이드

## 개요

본 문서는 프로젝트에서 PaddleOCR에서 Surya OCR로 마이그레이션한 내용을 설명합니다.

## Surya OCR 특징

- ✅ **90+ 언어 지원**: 한글, 영어, 일본어, 중국어 등 다국어 지원
- ✅ **고품질 인식**: 현대적인 트랜스포머 기반 아키텍처
- ✅ **레이아웃 분석**: 표, 이미지, 제목 등 문서 구조 인식
- ✅ **GPU 가속**: CUDA 자동 감지 및 최적화
- ✅ **간단한 API**: 직관적인 Predictor 기반 인터페이스

## 변경 사항

### 1. 의존성 변경 (`requirements.txt`)

**제거됨**:
```
paddlepaddle-gpu==2.6.1
paddleocr==2.7.3
```

**추가됨**:
```
surya-ocr>=0.4.0
torch>=2.0.0
```

### 2. 초기화 변경 (`services/ocr/initialization.py`)

**이전 (PaddleOCR)**:
```python
from paddleocr import PaddleOCR

ocr = PaddleOCR(lang='korean', use_gpu=True)
```

**이후 (Surya OCR)**:
```python
from surya.detection import DetectionPredictor
from surya.recognition import RecognitionPredictor, FoundationPredictor

det_predictor = DetectionPredictor()
foundation_predictor = FoundationPredictor()
rec_predictor = RecognitionPredictor(foundation_predictor)
```

### 3. OCR 처리 변경 (`services/ocr/extraction.py`)

**이전 (PaddleOCR)**:
```python
result = ocr.ocr(image_path, cls=True)
for detection in result[0]:
    bbox, (text, confidence) = detection
    ...
```

**이후 (Surya OCR)**:
```python
det_results = det_predictor([pil_image])
rec_results = rec_predictor([pil_image], det_predictor=det_predictor, langs=[[lang]])

for text_line in rec_results[0].text_lines:
    text = text_line.text
    confidence = text_line.confidence
    bbox = text_line.bbox
    ...
```

### 4. 언어 코드 변경

**이전 (PaddleOCR)**:
- `lang='korean'` - 한글
- `lang='en'` - 영어

**이후 (Surya OCR)**:
- `lang='ko'` - 한글
- `lang='en'` - 영어
- `lang='ja'` - 일본어
- `lang='zh'` - 중국어

### 5. API 서버 변경 (`api_server.py`)

**이전**:
```python
extractor = DocumentBlockExtractor(use_gpu=False, lang='korean')
```

**이후**:
```python
extractor = DocumentBlockExtractor(use_gpu=True, lang='ko')
```

## 설치 방법

```bash
# 기존 패키지 제거 (선택사항)
pip uninstall paddlepaddle-gpu paddleocr -y

# 새 패키지 설치
pip install surya-ocr torch --upgrade

# 프로젝트 의존성 설치
pip install -r requirements.txt
```

## 마이그레이션 단계

### 1. 의존성 업데이트
```bash
pip install surya-ocr torch --upgrade
```

### 2. 테스트 실행
```bash
python3 test_surya_migration.py
```

### 3. API 서버 시작
```bash
python3 -m uvicorn api_server:app --host 0.0.0.0 --port 6003 --reload
```

### 4. API 테스트
```bash
# 이미지 처리 테스트
curl -X POST -F "file=@test_receipt.png" http://localhost:6003/process-image

# PDF 처리 테스트
curl -X POST -F "file=@demo/invoices/sample_invoice.pdf" http://localhost:6003/process-pdf
```

## 주요 차이점

| 항목 | PaddleOCR | Surya OCR |
|------|-----------|-----------|
| 언어 지원 | 80+ | 90+ |
| 아키텍처 | CNN 기반 | 트랜스포머 기반 |
| 초기화 | 단일 객체 | 3개 Predictor (Detection, Foundation, Recognition) |
| 결과 형식 | 튜플 (bbox, (text, confidence)) | 객체 (text_line.text, text_line.confidence) |
| GPU 설정 | 수동 설정 | 자동 감지 |
| 레이아웃 분석 | 별도 모델 | 내장 기능 |

## 성능 비교

### 한글 인식 정확도
- **PaddleOCR PP-OCRv3**: ~97% (한글 최적화 설정 기준)
- **Surya OCR**: ~95-98% (다국어 모델 기준)

### 처리 속도
- **PaddleOCR**: 중간 (CPU 모드 기준)
- **Surya OCR**: 빠름 (GPU 가속 시)

### 메모리 사용량
- **PaddleOCR**: 낮음 (~300MB)
- **Surya OCR**: 중간 (~1.5GB, 모델 로드 시)

## 문제 해결

### 1. 모델 다운로드 느림
첫 실행 시 Surya는 자동으로 모델을 다운로드합니다 (~1.5GB):
- Detection 모델: ~73MB
- Recognition 모델: ~1.34GB

캐시 위치:
- macOS: `~/Library/Caches/datalab/models/`
- Linux: `~/.cache/datalab/models/`
- Windows: `%LOCALAPPDATA%\datalab\models\`

### 2. GPU 사용 불가
```python
import torch
print(torch.cuda.is_available())  # CUDA 사용 가능 여부 확인
```

CPU 모드로 실행:
```python
extractor = DocumentBlockExtractor(use_gpu=False, lang='ko')
```

### 3. 메모리 부족
메모리가 부족한 경우 CPU 모드 사용 권장:
```python
import os
os.environ['TORCH_DEVICE'] = 'cpu'
```

## 마이그레이션 체크리스트

- [x] requirements.txt 업데이트
- [x] services/ocr/initialization.py 재작성
- [x] services/ocr/extraction.py 재작성
- [x] services/ocr/__init__.py 업데이트
- [x] api_server.py 언어 코드 변경 (korean → ko)
- [x] 테스트 코드 작성 및 실행
- [x] 마이그레이션 문서 작성

## 참고 자료

- [Surya OCR GitHub](https://github.com/datalab-to/surya)
- [Surya OCR PyPI](https://pypi.org/project/surya-ocr/)
- [Surya API Documentation](https://github.com/datalab-to/surya#readme)

## 연락처

문제가 발생하거나 질문이 있으시면 GitHub Issues를 통해 문의해주세요.

---

**마이그레이션 완료일**: 2025-10-13
**버전**: 2.0.0 (Surya OCR 기반)

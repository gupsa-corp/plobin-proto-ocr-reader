# 폰트 설정

## 폰트 파일

이 디렉토리에는 한글 텍스트 렌더링을 위한 Noto Sans CJK 폰트가 포함되어 있습니다.

### 포함된 폰트
- **NotoSansCJK-Regular.ttc**: Noto Sans CJK 일반 글꼴 (한중일 통합)

## 사용 방법

`FastApi/services/visualization/rendering.py` 모듈은 자동으로 이 폰트를 로드하여 matplotlib의 기본 폰트로 설정합니다.

### 자동 폰트 로딩 프로세스
1. 프로젝트 루트의 `fonts/NotoSansCJK-Regular.ttc` 파일 확인
2. 폰트가 있으면 matplotlib에 등록
3. 폰트가 없으면 시스템 폰트로 폴백

## 폰트 경고 해결

이전에 발생하던 폰트 경고:
```
[WARNING] font_manager.py:1431 - findfont: Font family 'Noto Sans CJK JP' not found.
```

이 경고는 이제 다음과 같이 해결됩니다:
- 프로젝트 폰트 파일을 직접 로드하여 시스템 폰트에 의존하지 않음
- matplotlib 폰트 캐시를 사용하여 성능 최적화

## 폰트 다운로드

폰트 파일을 다시 다운로드해야 하는 경우:

```bash
cd fonts
curl -L -o NotoSansCJK-Regular.ttc \
  "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTC/NotoSansCJK-Regular.ttc"
```

## 라이선스

Noto Sans CJK는 SIL Open Font License 1.1 하에 배포됩니다.
- 상업적 사용 허용
- 수정 및 재배포 허용
- 라이선스 텍스트 포함 필수

자세한 내용: https://github.com/googlefonts/noto-cjk

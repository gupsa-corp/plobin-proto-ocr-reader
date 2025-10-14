# OCR domain - Surya OCR based implementation
from .initialization import initialize_ocr, get_supported_languages
from .extraction import extract_blocks, extract_blocks_with_layout_analysis, crop_all_blocks
from .merging import merge_adjacent_blocks


# DocumentBlockExtractor wrapper for Surya OCR
class DocumentBlockExtractor:
    def __init__(self, use_gpu: bool = True, lang: str = 'ko',
                 use_korean_enhancement: bool = False, use_ppocrv5: bool = False):
        """
        Surya OCR 기반 문서 블록 추출기

        Args:
            use_gpu: GPU 사용 여부 (CUDA 자동 감지)
            lang: 언어 코드 ('ko', 'en', 'ja' 등)
            use_korean_enhancement: 호환성 유지용 (Surya는 기본적으로 다국어 최적화)
            use_ppocrv5: 호환성 유지용
        """
        self.lang = lang
        self.use_gpu = use_gpu

        print(f"Surya OCR 초기화 중 (언어: {lang})...")

        # Surya OCR 모델 초기화
        self.ocr_models = initialize_ocr(
            use_gpu=use_gpu,
            lang=lang,
            enable_layout_analysis=True,
            use_korean_optimized=use_korean_enhancement
        )

        print(f"✅ Surya OCR 초기화 완료")

    def extract_blocks(self, image_path: str, confidence_threshold: float = 0.5,
                      merge_blocks: bool = True, merge_threshold: int = 30, **kwargs):
        """
        이미지에서 텍스트 블록 추출

        Args:
            image_path: 이미지 파일 경로
            confidence_threshold: 신뢰도 임계값
            merge_blocks: 블록 병합 여부
            merge_threshold: 병합 임계값
            **kwargs: 추가 설정

        Returns:
            블록 정보 딕셔너리
        """
        return extract_blocks(
            self.ocr_models,
            image_path,
            confidence_threshold=confidence_threshold,
            merge_blocks=merge_blocks,
            merge_threshold=merge_threshold,
            lang=self.lang,
            **kwargs
        )

    def extract_blocks_with_layout(self, image_path: str, confidence_threshold: float = 0.5,
                                   merge_blocks: bool = True, merge_threshold: int = 30,
                                   enable_table_recognition: bool = True, use_cache: bool = True):
        """
        레이아웃 분석을 포함한 블록 추출

        Args:
            image_path: 이미지 파일 경로
            confidence_threshold: 신뢰도 임계값
            merge_blocks: 블록 병합 여부
            merge_threshold: 병합 임계값
            enable_table_recognition: 표 인식 활성화
            use_cache: 캐싱 사용 여부

        Returns:
            레이아웃 분석 결과가 포함된 블록 정보
        """
        return extract_blocks_with_layout_analysis(
            self.ocr_models,
            image_path,
            confidence_threshold=confidence_threshold,
            merge_blocks=merge_blocks,
            merge_threshold=merge_threshold,
            enable_table_recognition=enable_table_recognition,
            lang=self.lang,
            use_cache=use_cache
        )

    def visualize_blocks(self, image_path: str, result, save_path=None):
        """
        블록 시각화 (호환성 유지)

        Args:
            image_path: 원본 이미지 경로
            result: OCR 결과 딕셔너리
            save_path: 저장 경로 (선택)

        Returns:
            시각화된 이미지
        """
        try:
            from .visualization import visualize_blocks as viz_blocks
            return viz_blocks(image_path, result, save_path)
        except ImportError:
            print("⚠️ 시각화 모듈을 찾을 수 없습니다.")
            return None


__all__ = [
    'DocumentBlockExtractor',
    'initialize_ocr',
    'get_supported_languages',
    'extract_blocks',
    'extract_blocks_with_layout_analysis',
    'crop_all_blocks',
    'merge_adjacent_blocks'
]

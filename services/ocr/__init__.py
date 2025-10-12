# OCR domain
from .initialization import initialize_ocr
from .extraction import extract_blocks, extract_blocks_with_layout_analysis, crop_all_blocks
from .merging import merge_adjacent_blocks, merge_line_blocks, create_merged_block
from .visualization import visualize_blocks
from .table_recognition import create_table_recognizer
from .hierarchy import build_hierarchy, get_block_hierarchy_tree, get_hierarchy_statistics, flatten_hierarchy

# Legacy DocumentBlockExtractor class for backward compatibility (한글 정확도 향상 포함)
class DocumentBlockExtractor:
    def __init__(self, use_gpu: bool = True, lang: str = 'en', use_korean_enhancement: bool = False, use_ppocrv5: bool = False):
        self.lang = lang
        self.use_gpu = use_gpu
        self.use_korean_enhancement = use_korean_enhancement
        self.use_ppocrv5 = use_ppocrv5
        # 한글 최적화 설정 적용 (PP-OCRv5 지원)
        self.ocr = initialize_ocr(use_gpu, lang, enable_layout_analysis=True,
                                 use_korean_optimized=(lang == 'korean' and use_korean_enhancement),
                                 use_ppocrv5=use_ppocrv5)

    def extract_blocks(self, image_path: str, confidence_threshold: float = 0.5, merge_blocks: bool = True,
                      merge_threshold: int = 30, enable_table_recognition: bool = True,
                      use_korean_enhancement: bool = None, preprocessing_level: str = 'medium'):
        # 기본값 설정
        if use_korean_enhancement is None:
            use_korean_enhancement = self.use_korean_enhancement

        if enable_table_recognition:
            return extract_blocks_with_layout_analysis(
                self.ocr, image_path, confidence_threshold, merge_blocks, merge_threshold,
                enable_table_recognition, use_cache=True)
        else:
            return extract_blocks(
                self.ocr, image_path, confidence_threshold, merge_blocks, merge_threshold,
                use_korean_enhancement, preprocessing_level)

    def visualize_blocks(self, image_path: str, result, save_path=None):
        return visualize_blocks(image_path, result, save_path)

__all__ = ['DocumentBlockExtractor', 'initialize_ocr', 'extract_blocks', 'extract_blocks_with_layout_analysis', 'visualize_blocks', 'merge_adjacent_blocks', 'merge_line_blocks', 'create_merged_block', 'create_table_recognizer', 'crop_all_blocks', 'build_hierarchy', 'get_block_hierarchy_tree', 'get_hierarchy_statistics', 'flatten_hierarchy']
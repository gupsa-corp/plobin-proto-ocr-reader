# OCR domain
from .initialization import initialize_ocr
from .extraction import extract_blocks, extract_blocks_with_layout_analysis, crop_all_blocks
from .merging import merge_adjacent_blocks, merge_line_blocks, create_merged_block
from .visualization import visualize_blocks
from .table_recognition import create_table_recognizer

# Legacy DocumentBlockExtractor class for backward compatibility
class DocumentBlockExtractor:
    def __init__(self, use_gpu: bool = True, lang: str = 'korean'):
        self.lang = lang
        self.use_gpu = use_gpu
        self.ocr = initialize_ocr(use_gpu, lang)

    def extract_blocks(self, image_path: str, confidence_threshold: float = 0.5, merge_blocks: bool = True, merge_threshold: int = 30, enable_table_recognition: bool = True):
        if enable_table_recognition:
            return extract_blocks_with_layout_analysis(self.ocr, image_path, confidence_threshold, merge_blocks, merge_threshold, enable_table_recognition)
        else:
            return extract_blocks(self.ocr, image_path, confidence_threshold, merge_blocks, merge_threshold)

    def visualize_blocks(self, image_path: str, result, save_path=None):
        return visualize_blocks(image_path, result, save_path)

__all__ = ['DocumentBlockExtractor', 'initialize_ocr', 'extract_blocks', 'extract_blocks_with_layout_analysis', 'visualize_blocks', 'merge_adjacent_blocks', 'merge_line_blocks', 'create_merged_block', 'create_table_recognizer', 'crop_all_blocks']
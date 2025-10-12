#!/usr/bin/env python3
"""
PDF to image conversion services
"""

import fitz  # PyMuPDF
from pathlib import Path


def pdf_to_images(pdf_path, output_dir, dpi=120, max_width=2000, max_height=2000):
    """
    PDF를 페이지별 이미지로 변환 (메모리 최적화)

    Args:
        pdf_path: PDF 파일 경로
        output_dir: 이미지 저장 디렉토리
        dpi: 이미지 해상도
        max_width: 최대 이미지 너비 (픽셀)
        max_height: 최대 이미지 높이 (픽셀)

    Returns:
        변환된 이미지 파일 경로 리스트
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # PDF 열기
    doc = fitz.open(pdf_path)
    image_paths = []

    pdf_name = Path(pdf_path).stem

    print(f"📄 PDF '{pdf_name}' 변환 중... ({len(doc)} 페이지)")

    for page_num in range(len(doc)):
        # 페이지 가져오기
        page = doc[page_num]

        # 페이지 크기 확인
        page_rect = page.rect
        page_width = page_rect.width
        page_height = page_rect.height

        # DPI 기반 스케일 계산
        scale = dpi / 72  # 72 DPI가 기본값

        # 예상 이미지 크기
        target_width = int(page_width * scale)
        target_height = int(page_height * scale)

        # 최대 크기 제한 적용
        if target_width > max_width or target_height > max_height:
            width_scale = max_width / target_width if target_width > max_width else 1.0
            height_scale = max_height / target_height if target_height > max_height else 1.0
            scale = scale * min(width_scale, height_scale)
            print(f"   ⚠️  페이지 {page_num + 1}: 크기 제한으로 스케일 조정 ({target_width}x{target_height} → {int(page_width * scale)}x{int(page_height * scale)})")

        # 이미지로 변환 (조정된 스케일 적용)
        mat = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat)

        # 이미지 파일명
        image_filename = f"{pdf_name}_page_{page_num + 1:03d}.png"
        image_path = output_dir / image_filename

        try:
            # 이미지 저장
            pix.save(str(image_path))
            image_paths.append(str(image_path))
            print(f"   ✅ 페이지 {page_num + 1}/{len(doc)} 변환 완료: {image_filename} ({pix.width}x{pix.height}px)")
        finally:
            # 명시적으로 메모리 해제
            pix = None

    doc.close()
    return image_paths


class PDFToImageProcessor:
    """PDF를 이미지로 변환하는 클래스"""

    def __init__(self, dpi=150):
        self.dpi = dpi

    def convert_pdf_to_images(self, pdf_path, output_dir):
        """
        PDF를 페이지별 이미지로 변환

        Args:
            pdf_path: PDF 파일 경로
            output_dir: 이미지 저장 디렉토리

        Returns:
            변환된 이미지 파일 경로 리스트
        """
        return pdf_to_images(pdf_path, output_dir, self.dpi)


__all__ = ['pdf_to_images', 'PDFToImageProcessor']
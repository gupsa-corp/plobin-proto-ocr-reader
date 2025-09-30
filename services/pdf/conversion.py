#!/usr/bin/env python3
"""
PDF to image conversion services
"""

import fitz  # PyMuPDF
from pathlib import Path


def pdf_to_images(pdf_path, output_dir, dpi=150):
    """
    PDF를 페이지별 이미지로 변환

    Args:
        pdf_path: PDF 파일 경로
        output_dir: 이미지 저장 디렉토리
        dpi: 이미지 해상도

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

        # 이미지로 변환 (DPI 설정)
        mat = fitz.Matrix(dpi/72, dpi/72)  # 72 DPI가 기본값
        pix = page.get_pixmap(matrix=mat)

        # 이미지 파일명
        image_filename = f"{pdf_name}_page_{page_num + 1:03d}.png"
        image_path = output_dir / image_filename

        # 이미지 저장
        pix.save(str(image_path))
        image_paths.append(str(image_path))

        print(f"   ✅ 페이지 {page_num + 1}/{len(doc)} 변환 완료: {image_filename}")

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
#!/usr/bin/env python3
"""
PDF Wrapper for Go integration
Receives PDF path and options, converts to images and returns JSON result
"""

import sys
import json
from pathlib import Path
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.pdf import PDFToImageProcessor
from services.ocr import DocumentBlockExtractor

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: pdf_wrapper.py <pdf_path> [options_json]"}))
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    options = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    
    # Create temporary directory for images
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Initialize PDF processor
        dpi = options.get('dpi', 150)
        pdf_processor = PDFToImageProcessor(dpi=dpi)
        
        # Convert PDF to images
        image_paths = pdf_processor.convert_pdf_to_images(pdf_path, temp_dir)
        
        # Initialize OCR extractor
        extractor = DocumentBlockExtractor(
            use_gpu=options.get('use_gpu', False),
            lang=options.get('language', 'ko')
        )
        
        # Process each page
        pages = []
        total_blocks = 0
        total_confidence = 0.0
        block_count = 0
        
        for i, image_path in enumerate(image_paths):
            result = extractor.extract_blocks(
                image_path,
                merge_blocks=options.get('merge_blocks', True),
                merge_threshold=options.get('merge_threshold', 30),
                create_sections=options.get('create_sections', False),
                build_hierarchy_tree=options.get('build_hierarchy_tree', False)
            )
            
            page_blocks = result.get('blocks', [])
            page_result = {
                "page_number": i + 1,
                "blocks": page_blocks,
                "total_blocks": len(page_blocks),
                "average_confidence": result.get('average_confidence', 0.0),
                "sections": result.get('sections', []),
                "hierarchy_tree": result.get('hierarchy_tree', {})
            }
            
            pages.append(page_result)
            total_blocks += len(page_blocks)
            
            for block in page_blocks:
                total_confidence += block.get('confidence', 0.0)
                block_count += 1
        
        # Calculate overall average confidence
        avg_confidence = total_confidence / block_count if block_count > 0 else 0.0
        
        # Output result
        output = {
            "request_id": "",  # Will be set by Go
            "total_pages": len(pages),
            "total_blocks": total_blocks,
            "average_confidence": avg_confidence,
            "pages": pages
        }
        
        print(json.dumps(output))
        
    finally:
        # Cleanup temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    main()

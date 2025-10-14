#!/usr/bin/env python3
"""
OCR Wrapper for Go integration
Receives image path and options, returns JSON result
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.ocr import DocumentBlockExtractor

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: ocr_wrapper.py <image_path> [options_json]"}))
        sys.exit(1)
    
    image_path = sys.argv[1]
    options = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    
    # Initialize extractor
    extractor = DocumentBlockExtractor(
        use_gpu=options.get('use_gpu', False),
        lang=options.get('language', 'ko')
    )
    
    # Extract blocks
    result = extractor.extract_blocks(
        image_path,
        merge_blocks=options.get('merge_blocks', True),
        merge_threshold=options.get('merge_threshold', 30),
        create_sections=options.get('create_sections', False),
        build_hierarchy_tree=options.get('build_hierarchy_tree', False)
    )
    
    # Convert to JSON
    output = {
        "request_id": "",  # Will be set by Go
        "blocks": result.get('blocks', []),
        "total_blocks": len(result.get('blocks', [])),
        "average_confidence": result.get('average_confidence', 0.0),
        "sections": result.get('sections', []),
        "hierarchy_tree": result.get('hierarchy_tree', {})
    }
    
    print(json.dumps(output))

if __name__ == "__main__":
    main()

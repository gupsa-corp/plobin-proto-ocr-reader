"""
Section Visualization Service

Handles visualization of OCR section groups including:
- Section type-based color coding
- Full section visualization image
- Individual section cropping
- Section metadata rendering
"""

from PIL import Image, ImageDraw, ImageFont
import numpy as np
from typing import List, Dict, Tuple, Optional
import os

# Section type color mapping (RGB)
SECTION_COLORS = {
    "header": (52, 152, 219),      # Blue
    "body": (46, 204, 113),        # Green
    "footer": (230, 126, 34),      # Orange
    "title": (231, 76, 60),        # Red
    "table": (155, 89, 182),       # Purple
    "list": (241, 196, 15),        # Yellow
    "unknown": (149, 165, 166)     # Gray
}

# Default color for unknown types
DEFAULT_COLOR = (149, 165, 166)

def get_section_color(section_type: str) -> Tuple[int, int, int]:
    """
    Get RGB color for section type

    Args:
        section_type: Type of section (header, body, footer, etc.)

    Returns:
        RGB color tuple
    """
    return SECTION_COLORS.get(section_type.lower(), DEFAULT_COLOR)


def visualize_sections(
    image: Image.Image,
    sections: List[Dict],
    line_thickness: int = 3
) -> Image.Image:
    """
    Create visualization with section bounding boxes

    Args:
        image: Original image
        sections: List of section dictionaries with bbox and section_type
        line_thickness: Thickness of bounding box lines

    Returns:
        Image with section bounding boxes drawn
    """
    # Convert to RGB if needed
    if image.mode != 'RGB':
        image = image.convert('RGB')

    # Create a copy to draw on
    vis_image = image.copy()
    draw = ImageDraw.Draw(vis_image)

    # Try to load font
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
    except:
        font = ImageFont.load_default()

    # Draw each section
    for idx, section in enumerate(sections):
        bbox = section.get('bbox', {})
        section_type = section.get('section_type', 'unknown')
        block_count = len(section.get('blocks', []))
        avg_confidence = section.get('avg_confidence', 0.0)

        # Handle bbox format (dict or list)
        if isinstance(bbox, dict):
            x1 = bbox.get('x_min', 0)
            y1 = bbox.get('y_min', 0)
            x2 = bbox.get('x_max', 0)
            y2 = bbox.get('y_max', 0)
        elif isinstance(bbox, list) and len(bbox) == 4:
            x1, y1, x2, y2 = bbox
        else:
            continue

        # Get color for this section type
        color = get_section_color(section_type)
        draw.rectangle(
            [(x1, y1), (x2, y2)],
            outline=color,
            width=line_thickness
        )

        # Prepare label text
        label = f"S{idx + 1}: {section_type.upper()}"
        info = f"Blocks: {block_count} | Conf: {avg_confidence:.2f}"

        # Draw label background
        label_bbox = draw.textbbox((x1, y1 - 30), label, font=font)
        draw.rectangle(
            [(label_bbox[0] - 2, label_bbox[1] - 2),
             (label_bbox[2] + 2, label_bbox[3] + 2)],
            fill=color
        )

        # Draw label text
        draw.text((x1, y1 - 30), label, fill='white', font=font)

        # Draw info text below label
        try:
            info_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        except:
            info_font = font

        draw.text((x1, y1 - 10), info, fill=color, font=info_font)

    return vis_image


def crop_section(
    image: Image.Image,
    section: Dict,
    padding: int = 5
) -> Optional[Image.Image]:
    """
    Crop individual section from image

    Args:
        image: Original image
        section: Section dictionary with bbox
        padding: Pixels to add around bbox

    Returns:
        Cropped section image or None if invalid bbox
    """
    bbox = section.get('bbox', {})

    # Handle bbox format (dict or list)
    if isinstance(bbox, dict):
        x1 = bbox.get('x_min', 0)
        y1 = bbox.get('y_min', 0)
        x2 = bbox.get('x_max', 0)
        y2 = bbox.get('y_max', 0)
    elif isinstance(bbox, list) and len(bbox) == 4:
        x1, y1, x2, y2 = bbox
    else:
        return None

    # Convert to RGB if needed
    if image.mode != 'RGB':
        image = image.convert('RGB')
    x1 = max(0, x1 - padding)
    y1 = max(0, y1 - padding)
    x2 = min(image.width, x2 + padding)
    y2 = min(image.height, y2 + padding)

    # Crop section
    cropped = image.crop((x1, y1, x2, y2))

    return cropped


def create_section_visualization_with_crops(
    image: Image.Image,
    sections: List[Dict],
    output_dir: str,
    line_thickness: int = 3,
    padding: int = 5
) -> Tuple[Image.Image, List[str]]:
    """
    Create full section visualization and crop individual sections

    Args:
        image: Original image
        sections: List of section dictionaries
        output_dir: Directory to save cropped sections
        line_thickness: Thickness of bounding box lines
        padding: Padding around cropped sections

    Returns:
        Tuple of (visualization image, list of cropped section paths)
    """
    # Create full visualization
    vis_image = visualize_sections(image, sections, line_thickness)

    # Create output directory if needed
    os.makedirs(output_dir, exist_ok=True)

    # Crop individual sections
    cropped_paths = []
    for idx, section in enumerate(sections):
        cropped = crop_section(image, section, padding)

        if cropped is not None:
            # Generate filename with 3-digit padding
            section_id = f"{idx + 1:03d}"
            crop_path = os.path.join(output_dir, f"section_{section_id}.png")

            # Save cropped section
            cropped.save(crop_path)
            cropped_paths.append(crop_path)

    return vis_image, cropped_paths


def extract_section_metadata(section: Dict, section_id: str) -> Dict:
    """
    Extract metadata for a section to save as JSON

    Args:
        section: Section dictionary
        section_id: Section ID (e.g., "001")

    Returns:
        Section metadata dictionary
    """
    # Extract block information from section's blocks list
    blocks_data = section.get('blocks', [])

    # Extract block IDs and text content
    block_ids = []
    text_parts = []

    for block in blocks_data:
        # Blocks in sections are full block objects, not indices
        if isinstance(block, dict):
            block_id = block.get('id', 0)
            block_ids.append(f"{block_id + 1:03d}")
            text_parts.append(block.get('text', ''))
        elif isinstance(block, int):
            # If it's an index, format it
            block_ids.append(f"{block + 1:03d}")

    # Combine all text content
    text_content = " ".join(text_parts)

    metadata = {
        "section_id": section_id,
        "section_type": section.get('section_type', 'unknown'),
        "bbox": section.get('bbox', {}),
        "block_count": len(blocks_data),
        "blocks": block_ids,
        "avg_confidence": section.get('avg_confidence', 0.0),
        "text_content": text_content.strip()
    }

    return metadata

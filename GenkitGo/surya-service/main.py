"""
Surya OCR Service - Advanced Layout Detection and Text Recognition
Provides REST API for Go server to use Surya's powerful OCR capabilities
"""
import os
import io
import time
from typing import List, Optional
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from PIL import Image
import uvicorn

from surya import detection, layout, recognition
from surya.model.detection.model import load_model as load_det_model, load_processor as load_det_processor
from surya.model.recognition.model import load_model as load_rec_model
from surya.model.recognition.processor import load_processor as load_rec_processor
from surya.settings import settings

app = FastAPI(
    title="Surya OCR Service",
    description="Advanced OCR with Layout Detection and Text Recognition",
    version="1.0.0"
)

# Global model instances (loaded once per model type)
_det_model = None
_det_processor = None
_rec_model = None
_rec_processor = None

def get_detection_models():
    """Load detection models (used for both detection and layout)"""
    global _det_model, _det_processor
    if _det_model is None:
        _det_model, _det_processor = load_det_model(), load_det_processor()
    return _det_model, _det_processor

def get_recognition_models():
    """Load recognition models"""
    global _rec_model, _rec_processor
    if _rec_model is None:
        _rec_model, _rec_processor = load_rec_model(), load_rec_processor()
    return _rec_model, _rec_processor


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Surya OCR",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "surya_version": "0.6.7",
        "models_loaded": True
    }


@app.post("/api/surya/layout")
async def layout_detection(
    file: UploadFile = File(...),
    languages: Optional[str] = Form(None)
):
    """
    Layout Detection - Detect document structure (tables, images, headers, etc.)

    Returns layout information with bounding boxes for each element type
    """
    start_time = time.time()

    try:
        # Read image
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))

        # Load models (cached after first call)
        det_model, det_processor = get_detection_models()

        # Perform layout detection (uses detection model)
        layout_predictions = layout.batch_layout_detection([image], det_model, det_processor)

        if not layout_predictions:
            raise HTTPException(status_code=500, detail="Layout detection failed")

        pred = layout_predictions[0]

        # Convert to response format
        blocks = []
        for i, bbox in enumerate(pred.bboxes):
            block = {
                "id": i,
                "bbox": {
                    "x": int(bbox.bbox[0]),
                    "y": int(bbox.bbox[1]),
                    "width": int(bbox.bbox[2] - bbox.bbox[0]),
                    "height": int(bbox.bbox[3] - bbox.bbox[1])
                },
                "bbox_points": [
                    {"x": int(bbox.bbox[0]), "y": int(bbox.bbox[1])},
                    {"x": int(bbox.bbox[2]), "y": int(bbox.bbox[1])},
                    {"x": int(bbox.bbox[2]), "y": int(bbox.bbox[3])},
                    {"x": int(bbox.bbox[0]), "y": int(bbox.bbox[3])}
                ],
                "layout_label": bbox.label,
                "confidence": float(bbox.confidence) if bbox.confidence is not None else 0.0,
                "block_type": bbox.label.lower()
            }
            blocks.append(block)

        processing_time = time.time() - start_time

        return {
            "success": True,
            "message": "Layout detection completed",
            "data": {
                "total_blocks": len(blocks),
                "blocks": blocks,
                "processing_time": processing_time
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Layout detection failed: {str(e)}")


@app.post("/api/surya/ocr")
async def full_ocr(
    file: UploadFile = File(...),
    languages: Optional[str] = Form("en")
):
    """
    Full OCR - Complete text recognition with layout detection

    Combines layout detection, text recognition, and reading order
    """
    start_time = time.time()

    try:
        # Read image
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))

        # Parse languages
        lang_list = [lang.strip() for lang in languages.split("+")]

        # Load models (cached after first call)
        det_model, det_processor = get_detection_models()
        rec_model, rec_processor = get_recognition_models()

        # Step 1: Layout detection (uses detection model)
        layout_predictions = layout.batch_layout_detection([image], det_model, det_processor)

        # Step 2: Text detection
        detection_predictions = detection.batch_text_detection([image], det_model, det_processor)

        # Step 3: OCR with detected lines
        ocr_predictions = recognition.batch_recognition(
            [image],
            lang_list,
            rec_model,
            rec_processor,
            bboxes=detection_predictions
        )

        if not ocr_predictions:
            raise HTTPException(status_code=500, detail="OCR failed")

        ocr_pred = ocr_predictions[0]
        layout_pred = layout_predictions[0] if layout_predictions else None

        # Convert to response format
        blocks = []
        for i, text_line in enumerate(ocr_pred.text_lines):
            bbox = text_line.bbox

            # Find matching layout block
            layout_label = "Text"
            if layout_pred:
                for layout_box in layout_pred.bboxes:
                    # Check if text line is inside layout bbox
                    if (bbox[0] >= layout_box.bbox[0] and bbox[1] >= layout_box.bbox[1] and
                        bbox[2] <= layout_box.bbox[2] and bbox[3] <= layout_box.bbox[3]):
                        layout_label = layout_box.label
                        break

            block = {
                "id": i,
                "text": text_line.text,
                "confidence": float(text_line.confidence),
                "bbox": {
                    "x": int(bbox[0]),
                    "y": int(bbox[1]),
                    "width": int(bbox[2] - bbox[0]),
                    "height": int(bbox[3] - bbox[1])
                },
                "bbox_points": [
                    {"x": int(bbox[0]), "y": int(bbox[1])},
                    {"x": int(bbox[2]), "y": int(bbox[1])},
                    {"x": int(bbox[2]), "y": int(bbox[3])},
                    {"x": int(bbox[0]), "y": int(bbox[3])}
                ],
                "block_type": "text",
                "layout_label": layout_label
            }
            blocks.append(block)

        # Calculate average confidence
        avg_confidence = sum(b["confidence"] for b in blocks) / len(blocks) if blocks else 0.0

        processing_time = time.time() - start_time

        return {
            "success": True,
            "message": "OCR completed successfully",
            "data": {
                "total_blocks": len(blocks),
                "average_confidence": avg_confidence,
                "blocks": blocks,
                "processing_time": processing_time
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR failed: {str(e)}")


@app.post("/api/surya/detect")
async def text_detection(
    file: UploadFile = File(...)
):
    """
    Text Line Detection - Detect text lines without recognition

    Returns bounding boxes for detected text lines
    """
    start_time = time.time()

    try:
        # Read image
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))

        # Load models (cached after first call)
        det_model, det_processor = get_detection_models()

        # Perform detection
        predictions = detection.batch_text_detection([image], det_model, det_processor)

        if not predictions:
            raise HTTPException(status_code=500, detail="Detection failed")

        pred = predictions[0]

        # Convert to response format
        blocks = []
        for i, line in enumerate(pred.bboxes):
            block = {
                "id": i,
                "bbox": {
                    "x": int(line.bbox[0]),
                    "y": int(line.bbox[1]),
                    "width": int(line.bbox[2] - line.bbox[0]),
                    "height": int(line.bbox[3] - line.bbox[1])
                },
                "bbox_points": [
                    {"x": int(line.bbox[0]), "y": int(line.bbox[1])},
                    {"x": int(line.bbox[2]), "y": int(line.bbox[1])},
                    {"x": int(line.bbox[2]), "y": int(line.bbox[3])},
                    {"x": int(line.bbox[0]), "y": int(line.bbox[3])}
                ],
                "confidence": float(line.confidence),
                "block_type": "text_line"
            }
            blocks.append(block)

        processing_time = time.time() - start_time

        return {
            "success": True,
            "message": "Text detection completed",
            "data": {
                "total_blocks": len(blocks),
                "blocks": blocks,
                "processing_time": processing_time
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


if __name__ == "__main__":
    port = int(os.getenv("SURYA_PORT", "6004"))
    host = os.getenv("SURYA_HOST", "0.0.0.0")

    print(f"🚀 Starting Surya OCR Service on {host}:{port}")
    print(f"📦 Surya version: 0.6.7")
    print(f"🔧 Settings: {settings}")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )

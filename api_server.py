from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Union
import tempfile
import os
import json
from pathlib import Path
import asyncio
import shutil

from document_block_extractor import DocumentBlockExtractor
from pdf_to_image_processor import PDFToImageProcessor

app = FastAPI(
    title="Document OCR API",
    description="API for document text extraction and block classification using PaddleOCR",
    version="1.0.0"
)

class BlockInfo(BaseModel):
    text: str
    confidence: float
    bbox: List[List[int]]
    block_type: str

class ProcessingResult(BaseModel):
    filename: str
    total_blocks: int
    average_confidence: float
    blocks: List[BlockInfo]
    processing_time: Optional[float] = None

class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None

extractor = DocumentBlockExtractor(use_gpu=False)
pdf_processor = PDFToImageProcessor()

@app.get("/")
async def root():
    return {"message": "Document OCR API", "version": "1.0.0", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "gpu_available": extractor.use_gpu}

@app.post("/process-image", response_model=ProcessingResult)
async def process_image(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_path = tmp_file.name

        try:
            result = extractor.extract_blocks(tmp_path)
            blocks = result.get('blocks', [])

            if not blocks:
                return ProcessingResult(
                    filename=file.filename,
                    total_blocks=0,
                    average_confidence=0.0,
                    blocks=[]
                )

            block_infos = []
            total_confidence = 0

            for block in blocks:
                block_info = BlockInfo(
                    text=block['text'],
                    confidence=block['confidence'],
                    bbox=block['bbox_points'],
                    block_type=block['type']
                )
                block_infos.append(block_info)
                total_confidence += block['confidence']

            avg_confidence = total_confidence / len(blocks)

            return ProcessingResult(
                filename=file.filename,
                total_blocks=len(blocks),
                average_confidence=round(avg_confidence, 3),
                blocks=block_infos
            )

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

@app.post("/process-pdf", response_model=List[ProcessingResult])
async def process_pdf(file: UploadFile = File(...)):
    if not file.content_type or file.content_type != 'application/pdf':
        raise HTTPException(status_code=400, detail="File must be a PDF")

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_path = tmp_file.name

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                image_paths = pdf_processor.convert_pdf_to_images(tmp_path, temp_dir)

                results = []

                for i, image_path in enumerate(image_paths):
                    result = extractor.extract_blocks(image_path)
                    blocks = result.get('blocks', [])

                    if blocks:
                        block_infos = []
                        total_confidence = 0

                        for block in blocks:
                            block_info = BlockInfo(
                                text=block['text'],
                                confidence=block['confidence'],
                                bbox=block['bbox_points'],
                                block_type=block['type']
                            )
                            block_infos.append(block_info)
                            total_confidence += block['confidence']

                        avg_confidence = total_confidence / len(blocks)

                        result = ProcessingResult(
                            filename=f"{file.filename}_page_{i+1}",
                            total_blocks=len(blocks),
                            average_confidence=round(avg_confidence, 3),
                            blocks=block_infos
                        )
                    else:
                        result = ProcessingResult(
                            filename=f"{file.filename}_page_{i+1}",
                            total_blocks=0,
                            average_confidence=0.0,
                            blocks=[]
                        )

                    results.append(result)

                return results

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

@app.post("/process-document")
async def process_document(file: UploadFile = File(...)):
    content_type = file.content_type or ""

    if content_type.startswith('image/'):
        return await process_image(file)
    elif content_type == 'application/pdf':
        return await process_pdf(file)
    else:
        raise HTTPException(
            status_code=400,
            detail="File must be an image (JPEG, PNG, etc.) or PDF"
        )

@app.get("/supported-formats")
async def get_supported_formats():
    return {
        "image_formats": ["JPEG", "PNG", "BMP", "TIFF", "WEBP"],
        "document_formats": ["PDF"],
        "max_file_size": "10MB (configurable)"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6003)
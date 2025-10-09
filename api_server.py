from fastapi import FastAPI
from pathlib import Path
from datetime import datetime

# Import internal components
from services.ocr import DocumentBlockExtractor
from services.pdf import PDFToImageProcessor

# Import API modules
from api.endpoints import root, process_image, process_pdf, blocks, templates, pages, images
from api.endpoints.requests import router as requests_router, set_dependencies as set_requests_dependencies, set_processing_dependencies as set_requests_processing_dependencies
from api.endpoints.analysis import router as analysis_router

# Initialize FastAPI app
app = FastAPI(
    title="Document OCR API",
    description="API for document text extraction and block classification using PaddleOCR",
    version="1.0.0"
)

# Global configuration and dependencies
server_stats = {
    "start_time": datetime.now(),
    "total_requests": 0,
    "total_images_processed": 0,
    "total_pdfs_processed": 0,
    "total_blocks_extracted": 0,
    "total_processing_time": 0.0,
    "last_request_time": None,
    "errors": 0
}

# Initialize processors
extractor = DocumentBlockExtractor(use_gpu=False)
pdf_processor = PDFToImageProcessor()

# Initialize output directory
output_dir = Path("output")
output_dir.mkdir(exist_ok=True)

# Set up dependencies for endpoint modules
root.set_server_stats(server_stats)
process_image.set_dependencies(server_stats, extractor, str(output_dir))
process_pdf.set_dependencies(server_stats, extractor, pdf_processor, str(output_dir))
set_requests_dependencies(str(output_dir))
set_requests_processing_dependencies(extractor, pdf_processor)
pages.set_dependencies(str(output_dir))
blocks.set_dependencies(str(output_dir))
images.set_dependencies(str(output_dir))

# Include routers
app.include_router(root.router, tags=["Root"])
app.include_router(process_image.router, tags=["Processing"])
app.include_router(process_pdf.router, tags=["Processing"])
app.include_router(requests_router, tags=["Request Management"])
app.include_router(templates.router, tags=["Template Management"])
app.include_router(pages.router, tags=["Page Navigation"])
app.include_router(blocks.router, tags=["Block Editing"])
app.include_router(images.router, tags=["Image Processing"])
app.include_router(analysis_router, tags=["LLM Analysis"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6003, reload=True)